# Contributing to tokrate

Thanks for taking a look. tokrate is small on purpose — stream a few completions,
time them, report the numbers — and the aim is to keep the numbers honest.

## Ground rules

- **Standard library only.** No runtime dependencies. Tests use `unittest`.
- **Every change comes with a test.** The suite stands up a fake streaming
  OpenAI-compatible server (`tests/fakeserver.py`), so the timing and the parsing
  are tested end to end with no model and no network.
- **Measure, don't flatter.** A change that makes the numbers look better without
  the endpoint actually being faster is a bug.

## Running the tests

```bash
python -m unittest discover -s tests -t .
```

No install needed — the tests import the package from the repo root.

## Good contributions

Support for a response shape a real server emits that tokrate mis-times; a
clearer metric; a sampling mode (varied prompts). Out of scope: scoring answer
quality, and a full production load generator — see "What it is not" in the
README. Security reports go to **info@nirry.net** — see [SECURITY.md](SECURITY.md).
