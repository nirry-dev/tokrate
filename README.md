# tokrate

**Benchmark a local, OpenAI-compatible LLM endpoint.**

Point it at a chat-completions URL and it measures the three numbers that decide
whether a local setup feels fast: how long until the **first token** (TTFT), how
fast it **generates** (tokens/sec), and how much **throughput** you get as you
add concurrency. It streams the responses itself and times them.

```text
$ tokrate http://localhost:8080/v1/chat/completions -m llama-8b -n 16 -c 4 --warmup
endpoint    http://localhost:8080/v1/chat/completions
model       llama-8b
requests    16 ok, 0 failed   concurrency 4   wall 6.80s
TTFT        mean 180.2ms  median 171.0ms  p95 240.5ms
tok/s       mean 52.4  median 53.1  (per request)
throughput  186.3 tok/s aggregate   2.35 req/s
```

No dependencies — just the Python standard library. Python 3.9+.

---

## Why

"Is it fast enough?" is the first question about any local model, and the answer
is a few concrete numbers. tokrate gets them without a framework: it speaks the
OpenAI streaming API that llama.cpp, vLLM, Ollama and the rest already serve,
reads the token count from the response's own `usage`, and reports per-request
latency alongside the aggregate throughput — because a single stream's speed and
what the box can do under load are two different questions.

## Install

```bash
pip install tokrate
```

Or vendor the `tokrate/` package — it's pure standard library, no build step.

## Use it

### On the command line

```bash
tokrate http://localhost:8080/v1/chat/completions -m llama-8b
tokrate http://localhost:8080/v1/chat/completions -n 32 -c 8 --warmup --json
```

| Option | Meaning |
| --- | --- |
| `URL` | the chat-completions endpoint (default `http://localhost:8080/v1/chat/completions`) |
| `-m, --model` | model name to request |
| `-n, --requests` | total requests to send (default 8) |
| `-c, --concurrency` | how many at once (default 1) |
| `--max-tokens` | tokens to generate per request (default 128) |
| `--warmup` | send one uncounted request first — loads the model so it isn't timed |
| `--prompt` | the prompt to send |
| `--api-key-env VAR` | read a bearer token from an environment variable |
| `--json` | machine-readable output |

Exit status: `0` when every request succeeded, `1` when any failed (or none ran).

### In Python

```python
from tokrate import run

s = run("http://localhost:8080/v1/chat/completions", model="llama-8b", prompt="hi", n=16, concurrency=4)
s.stats()   # {'ttft_ms': 180.2, 'tok_s_median': 53.1, 'throughput_tok_s': 186.3, 'requests_per_s': 2.35, ...}
```

`run(...)` returns a `Summary` with the raw per-request numbers; `one_request(...)`
times a single call if you want to build your own harness.

## What it measures

- **TTFT** — time to the first content token, per request (mean / median / p95).
- **tok/s (per request)** — a single stream's generation rate, from the first
  token to the last.
- **throughput** — total tokens across the run divided by wall-clock time: what
  the endpoint delivers at the chosen concurrency.
- **requests/s** — completed requests per second.

Token counts come from each response's `usage.completion_tokens` when the server
sends it; otherwise tokrate counts the content deltas, which is close.

## What it is not

- **Not a quality benchmark.** It measures speed, not whether the answers are any
  good. For that, run an eval.
- **Not a tokenizer.** It trusts the server's token count (or counts deltas). To
  measure a prompt's size against a specific model, use
  [gguftok](https://github.com/nirry-dev/gguftok).
- **Not a load generator for production.** It's a quick local measurement, not a
  sustained load test with think-time and arrival distributions.

## License

MIT. Part of [Nirry Labs](https://nirry.net) — local-first AI and security tools,
dependency-light and auditable by design.
