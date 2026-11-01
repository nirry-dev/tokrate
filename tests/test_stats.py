import unittest

from tokrate.bench import Summary, _percentile


class TestPercentile(unittest.TestCase):
    def test_interpolates(self):
        self.assertEqual(_percentile([0, 10], 0.95), 9.5)
        self.assertEqual(_percentile([5], 0.95), 5)
        self.assertIsNone(_percentile([], 0.5))

    def test_median_like(self):
        self.assertEqual(_percentile([1, 2, 3], 0.5), 2)


class TestSummaryStats(unittest.TestCase):
    def test_computed_fields(self):
        s = Summary(
            url="u",
            model="m",
            concurrency=2,
            requested=4,
            ok=4,
            failed=0,
            wall=2.0,
            ttfts=[0.1, 0.2, 0.3, 0.4],
            tok_rates=[40.0, 50.0, 60.0],
            tokens_total=200,
        )
        st = s.stats()
        self.assertEqual(st["ttft_ms"], 250.0)  # mean of [100,200,300,400] ms
        self.assertEqual(st["tok_s_mean"], 50.0)
        self.assertEqual(st["throughput_tok_s"], 100.0)  # 200 tokens / 2.0 s
        self.assertEqual(st["requests_per_s"], 2.0)  # 4 ok / 2.0 s

    def test_empty_is_safe(self):
        s = Summary(url="u", model="m", concurrency=1, requested=1, ok=0, failed=1, wall=0.5)
        st = s.stats()
        self.assertIsNone(st["ttft_ms"])
        self.assertIsNone(st["tok_s_mean"])
        self.assertEqual(st["throughput_tok_s"], 0.0)


if __name__ == "__main__":
    unittest.main()
