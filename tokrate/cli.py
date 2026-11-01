"""Command line: ``tokrate URL`` benchmarks a local LLM endpoint.

    tokrate http://localhost:8080/v1/chat/completions -m llama-8b
    tokrate http://localhost:8080/v1/chat/completions -n 32 -c 8 --warmup

Exit status: 0 when every request succeeded, 1 when any failed (or none ran), 2
for a bad call.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from typing import Optional, Sequence

from . import __version__
from .bench import Summary, run

DEFAULT_URL = "http://localhost:8080/v1/chat/completions"


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="tokrate", description="Benchmark a local, OpenAI-compatible LLM endpoint.")
    p.add_argument("url", nargs="?", default=DEFAULT_URL, help=f"chat-completions URL (default: {DEFAULT_URL})")
    p.add_argument("-m", "--model", default="default", help="model name to request (default: default)")
    p.add_argument("--prompt", default="Write a short paragraph about the sea.", help="the prompt to send")
    p.add_argument("--max-tokens", type=int, default=128, help="max tokens to generate (default: 128)")
    p.add_argument("-n", "--requests", type=int, default=8, metavar="N", help="total requests (default: 8)")
    p.add_argument("-c", "--concurrency", type=int, default=1, metavar="C", help="concurrent requests (default: 1)")
    p.add_argument("--timeout", type=float, default=60.0, metavar="S", help="per-request timeout (default: 60)")
    p.add_argument("--warmup", action="store_true", help="send one uncounted request first (loads the model)")
    p.add_argument("--api-key-env", metavar="VAR", help="environment variable holding a bearer token")
    p.add_argument("--json", action="store_true", help="output JSON")
    p.add_argument("-V", "--version", action="version", version=f"tokrate {__version__}")
    return p


def _fmt(value, unit: str = "") -> str:
    return "n/a" if value is None else f"{value}{unit}"


def _print_table(s: Summary) -> None:
    st = s.stats()
    print(f"endpoint    {s.url}")
    print(f"model       {s.model}")
    print(f"requests    {s.ok} ok, {s.failed} failed   concurrency {s.concurrency}   wall {st['wall_s']}s")
    if s.ok:
        print(f"TTFT        mean {_fmt(st['ttft_ms'], 'ms')}  median {_fmt(st['ttft_ms_median'], 'ms')}  p95 {_fmt(st['ttft_ms_p95'], 'ms')}")
        print(f"tok/s       mean {_fmt(st['tok_s_mean'])}  median {_fmt(st['tok_s_median'])}  (per request)")
        print(f"throughput  {_fmt(st['throughput_tok_s'])} tok/s aggregate   {_fmt(st['requests_per_s'])} req/s")
    for err, count in Counter(s.errors).most_common(3):
        print(f"  {count}x {err}", file=sys.stderr)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_parser().parse_args(argv)

    headers = {}
    if args.api_key_env:
        key = os.environ.get(args.api_key_env)
        if key:
            headers["authorization"] = f"Bearer {key}"
        else:
            print(f"tokrate: ${args.api_key_env} is not set", file=sys.stderr)

    summary = run(
        args.url,
        model=args.model,
        prompt=args.prompt,
        max_tokens=args.max_tokens,
        n=args.requests,
        concurrency=args.concurrency,
        headers=headers,
        timeout=args.timeout,
        warmup=args.warmup,
    )

    if args.json:
        print(json.dumps(summary.stats(), indent=2))
    else:
        _print_table(summary)

    return 0 if summary.failed == 0 and summary.ok > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
