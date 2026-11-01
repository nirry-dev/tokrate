"""Measure a local LLM endpoint: time-to-first-token, tokens/sec, throughput.

One request streams an OpenAI-compatible chat completion and times it: when the
first content token arrives (TTFT), when generation finishes, and how many tokens
came out (from the response's own ``usage``, or a count of content deltas as a
fallback). A run fires N of those across a thread pool at a chosen concurrency and
rolls the per-request numbers up into a summary.
"""

from __future__ import annotations

import http.client
import json
import ssl
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from statistics import mean, median
from typing import List, Optional
from urllib.parse import urlsplit

__all__ = ["Result", "Summary", "one_request", "run"]


@dataclass
class Result:
    ok: bool
    ttft: Optional[float] = None  # seconds until the first content token
    total: Optional[float] = None  # seconds for the whole response
    tokens: Optional[int] = None  # completion tokens
    status: Optional[int] = None
    error: Optional[str] = None

    @property
    def gen_time(self) -> Optional[float]:
        if self.total is None or self.ttft is None:
            return None
        return max(self.total - self.ttft, 0.0)

    @property
    def tok_s(self) -> Optional[float]:
        g = self.gen_time
        if self.tokens and g and g > 0:
            return self.tokens / g
        return None


def _connection(parts, timeout):
    if parts.scheme == "https":
        return http.client.HTTPSConnection(parts.hostname, parts.port or 443, timeout=timeout, context=ssl.create_default_context())
    return http.client.HTTPConnection(parts.hostname, parts.port or 80, timeout=timeout)


def one_request(url: str, payload: dict, headers: dict, timeout: float) -> Result:
    """Send one streaming completion and time it."""
    parts = urlsplit(url)
    path = (parts.path or "/") + (f"?{parts.query}" if parts.query else "")
    body = json.dumps(payload)
    conn = _connection(parts, timeout)
    start = time.perf_counter()
    try:
        conn.request("POST", path, body=body, headers={**headers, "content-type": "application/json", "accept": "text/event-stream"})
        resp = conn.getresponse()
        if resp.status >= 400:
            detail = resp.read()[:200].decode("utf-8", "replace").strip()
            return Result(ok=False, status=resp.status, error=f"HTTP {resp.status}: {detail}" if detail else f"HTTP {resp.status}", total=time.perf_counter() - start)

        ttft: Optional[float] = None
        tokens: Optional[int] = None
        deltas = 0
        for raw in resp:
            line = raw.strip()
            if not line.startswith(b"data:"):
                continue
            data = line[5:].strip()
            if data == b"[DONE]":
                break
            try:
                obj = json.loads(data)
            except json.JSONDecodeError:
                continue
            usage = obj.get("usage")
            if usage and usage.get("completion_tokens") is not None:
                tokens = usage["completion_tokens"]
            for choice in obj.get("choices") or []:
                content = (choice.get("delta") or {}).get("content")
                if content:
                    if ttft is None:
                        ttft = time.perf_counter() - start
                    deltas += 1
        total = time.perf_counter() - start
        if tokens is None:
            tokens = deltas  # no usage reported: count the content deltas
        return Result(ok=True, ttft=ttft, total=total, tokens=tokens, status=resp.status)
    except (OSError, http.client.HTTPException) as err:
        return Result(ok=False, error=str(err) or type(err).__name__, total=time.perf_counter() - start)
    finally:
        conn.close()


def _percentile(values: List[float], p: float) -> Optional[float]:
    if not values:
        return None
    s = sorted(values)
    k = (len(s) - 1) * p
    lo = int(k)
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


@dataclass
class Summary:
    url: str
    model: str
    concurrency: int
    requested: int
    ok: int
    failed: int
    wall: float
    ttfts: List[float] = field(default_factory=list)
    tok_rates: List[float] = field(default_factory=list)
    tokens_total: int = 0
    errors: List[str] = field(default_factory=list)

    def stats(self) -> dict:
        return {
            "url": self.url,
            "model": self.model,
            "concurrency": self.concurrency,
            "requested": self.requested,
            "ok": self.ok,
            "failed": self.failed,
            "wall_s": round(self.wall, 4),
            "ttft_ms": _round(_safe(mean, self.ttfts), 1000),
            "ttft_ms_median": _round(_safe(median, self.ttfts), 1000),
            "ttft_ms_p95": _round(_percentile(self.ttfts, 0.95), 1000),
            "tok_s_mean": _round(_safe(mean, self.tok_rates), 1),
            "tok_s_median": _round(_safe(median, self.tok_rates), 1),
            "throughput_tok_s": round(self.tokens_total / self.wall, 1) if self.wall > 0 else None,
            "requests_per_s": round(self.ok / self.wall, 2) if self.wall > 0 else None,
            "tokens_total": self.tokens_total,
        }


def _safe(fn, values):
    return fn(values) if values else None


def _round(value, scale):
    return round(value * scale, 1) if value is not None else None


def run(url: str, *, model: str, prompt: str, max_tokens: int = 128, n: int = 8, concurrency: int = 1, headers: Optional[dict] = None, timeout: float = 60.0, warmup: bool = False) -> Summary:
    """Fire *n* streaming completions at *concurrency* and summarize the timings."""
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "stream": True,
        "stream_options": {"include_usage": True},
    }
    headers = headers or {}
    if warmup:
        one_request(url, {**payload, "max_tokens": 1}, headers, timeout)

    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=max(1, concurrency)) as pool:
        results = list(pool.map(lambda _: one_request(url, payload, headers, timeout), range(n)))
    wall = time.perf_counter() - start

    ok = [r for r in results if r.ok]
    return Summary(
        url=url,
        model=model,
        concurrency=concurrency,
        requested=n,
        ok=len(ok),
        failed=len(results) - len(ok),
        wall=wall,
        ttfts=[r.ttft for r in ok if r.ttft is not None],
        tok_rates=[r.tok_s for r in ok if r.tok_s is not None],
        tokens_total=sum(r.tokens or 0 for r in ok),
        errors=[r.error for r in results if not r.ok and r.error],
    )
