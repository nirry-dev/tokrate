import unittest

from tokrate.bench import one_request, run
from tests.fakeserver import make_server, stop, url_of


class TestRun(unittest.TestCase):
    def test_measures_against_a_streaming_server(self):
        srv = make_server(tokens=6, delay=0.002)
        try:
            s = run(url_of(srv), model="m", prompt="hi", max_tokens=16, n=4, concurrency=2)
            self.assertEqual(s.ok, 4)
            self.assertEqual(s.failed, 0)
            self.assertEqual(s.tokens_total, 24)  # 6 tokens x 4 requests
            self.assertEqual(len(s.ttfts), 4)
            self.assertTrue(all(t > 0 for t in s.ttfts))
            st = s.stats()
            self.assertEqual(st["tokens_total"], 24)
            self.assertIsNotNone(st["throughput_tok_s"])
            self.assertIsNotNone(st["ttft_ms"])
        finally:
            stop(srv)

    def test_counts_deltas_when_no_usage(self):
        srv = make_server(tokens=5, delay=0.001, send_usage=False)
        try:
            r = one_request(url_of(srv), {"model": "m", "messages": [], "stream": True}, {}, 10.0)
            self.assertTrue(r.ok)
            self.assertEqual(r.tokens, 5)  # fallback: counted the content deltas
        finally:
            stop(srv)

    def test_http_error_is_a_failure(self):
        srv = make_server(status=500)
        try:
            s = run(url_of(srv), model="m", prompt="hi", n=2, concurrency=1)
            self.assertEqual(s.ok, 0)
            self.assertEqual(s.failed, 2)
            self.assertTrue(s.errors)
        finally:
            stop(srv)

    def test_connection_failure(self):
        s = run("http://127.0.0.1:1/v1/chat/completions", model="m", prompt="hi", n=3, concurrency=3, timeout=2)
        self.assertEqual(s.ok, 0)
        self.assertEqual(s.failed, 3)
        self.assertTrue(s.errors)


if __name__ == "__main__":
    unittest.main()
