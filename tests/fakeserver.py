"""A fake, streaming OpenAI-compatible endpoint for the tests — no model needed."""

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class _Handler(BaseHTTPRequestHandler):
    tokens = 8
    delay = 0.002
    status = 200
    send_usage = True

    def log_message(self, *args):  # silence
        pass

    def do_POST(self):
        length = int(self.headers.get("content-length", 0) or 0)
        self.rfile.read(length)
        if self.status != 200:
            self.send_response(self.status)
            self.send_header("content-type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"error":{"message":"boom"}}')
            return
        self.send_response(200)
        self.send_header("content-type", "text/event-stream")
        self.end_headers()
        for i in range(self.tokens):
            time.sleep(self.delay)
            self._event({"choices": [{"delta": {"content": f"t{i} "}}]})
        if self.send_usage:
            self._event({"choices": [{"delta": {}}], "usage": {"prompt_tokens": 5, "completion_tokens": self.tokens, "total_tokens": self.tokens + 5}})
        self.wfile.write(b"data: [DONE]\n\n")
        self.wfile.flush()

    def _event(self, obj):
        self.wfile.write(b"data: " + json.dumps(obj).encode("utf-8") + b"\n\n")
        self.wfile.flush()


def make_server(*, tokens=8, delay=0.002, status=200, send_usage=True):
    handler = type("_H", (_Handler,), {"tokens": tokens, "delay": delay, "status": status, "send_usage": send_usage})
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def url_of(server, path="/v1/chat/completions"):
    return f"http://127.0.0.1:{server.server_address[1]}{path}"


def stop(server):
    server.shutdown()
    server.server_close()
