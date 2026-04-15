# Tests

## Running Tests

Run the full test suite from the project root:

```bash
python -m unittest discover tests/
```

Run a single test module:

```bash
python -m unittest tests.test_parser
python -m unittest tests.test_models
python -m unittest tests.test_reports
```

Run a single test case or method:

```bash
python -m unittest tests.test_parser.TestParseString.test_simple_transaction
```

## Conventions

### File naming

| What | Convention | Example |
|---|---|---|
| Test module | `test_<module>.py` | `test_parser.py` |
| Test class | `Test<What>` | `TestParseString`, `TestBalance` |
| Test method | `test_<behaviour>` | `test_parse_simple_transaction` |

### What to test

- Every public function in `hledger/` must have at least one test.
- Tests should cover the happy path and the most important error paths.
- For parser tests: test both valid input (produces expected model) and
  invalid input (raises `ParseError` with a useful message).

### Fixtures

Sample journal files live in `tests/fixtures/`. Use them in tests via a
relative path from the project root, or load them with `importlib.resources`
if the package is installed.

```python
import os

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
SAMPLE_JOURNAL = os.path.join(FIXTURES, "sample.journal")
```

Add new fixture files when a test requires a specific journal structure not
covered by `sample.journal`. Name fixtures descriptively:
`minimal.journal`, `multi_currency.journal`, `malformed_date.journal`, etc.

### No third-party test dependencies

Tests use Python's built-in `unittest` only. Do not add pytest, hypothesis,
or any other test library without user approval.
