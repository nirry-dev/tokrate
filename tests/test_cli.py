import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout

from tokrate.cli import main
from tests.fakeserver import make_server, stop, url_of


def run_cli(argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = main(argv)
    return code, out.getvalue(), err.getvalue()


class TestCli(unittest.TestCase):
    def test_table(self):
        srv = make_server(tokens=4, delay=0.001)
        try:
            code, out, _ = run_cli([url_of(srv), "-m", "m", "-n", "3", "-c", "1"])
            self.assertEqual(code, 0)
            self.assertIn("TTFT", out)
            self.assertIn("tok/s", out)
            self.assertIn("3 ok, 0 failed", out)
        finally:
            stop(srv)

    def test_json(self):
        srv = make_server(tokens=4, delay=0.001)
        try:
            code, out, _ = run_cli([url_of(srv), "-n", "2", "--json"])
            self.assertEqual(code, 0)
            data = json.loads(out)
            self.assertEqual(data["ok"], 2)
            self.assertEqual(data["tokens_total"], 8)
        finally:
            stop(srv)

    def test_failure_exit_code(self):
        code, _, _ = run_cli(["http://127.0.0.1:1/v1/chat/completions", "-n", "2", "--timeout", "2"])
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
