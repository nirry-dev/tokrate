"""tokrate — benchmark a local, OpenAI-compatible LLM endpoint.

Point it at a chat-completions URL and it measures what actually matters on one
machine: how long until the first token (TTFT), how fast it generates
(tokens/sec), and how much total throughput you get as you add concurrency.

    $ tokrate http://localhost:8080/v1/chat/completions -m llama-8b -n 16 -c 4

Pure standard library — it streams the responses itself and times them.
"""

from .bench import Result, Summary, one_request, run

__version__ = "0.1.0"

__all__ = ["run", "one_request", "Result", "Summary", "__version__"]
