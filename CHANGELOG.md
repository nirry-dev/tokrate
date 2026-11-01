# Changelog

All notable changes to tokrate are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project aims to
follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] — 2026-11-01

First release.

### Added
- `run(url, ...)` — fire N streaming chat completions at a chosen concurrency and
  return a `Summary`: time-to-first-token (mean / median / p95), per-request
  tokens/sec, aggregate throughput and requests/sec. `one_request(...)` times a
  single call.
- Token counts come from each response's `usage.completion_tokens`, falling back
  to a count of content deltas when the server doesn't report usage.
- A `tokrate` command-line tool: URL, `--model`, `-n`/`-c`, `--max-tokens`,
  `--warmup`, `--api-key-env`, `--json`, and a failure-aware exit code. Also
  runnable as `python -m tokrate`.
- Pure standard library — it streams and times the responses itself.
