# PyLedger

A Python implementation of the [hledger](https://hledger.org) plain-text accounting tool.

## Features (planned for v1)

- Parse `.journal` files compatible with the hledger format
- Core commands: `balance`, `register`, `print`, `accounts`, `stats`
- Pure Python — no third-party runtime dependencies
- Modular, testable architecture

## Requirements

- Python 3.10+

## Installation

```bash
pip install -e .
```

## Usage

```bash
pyLedger balance myfile.journal
pyLedger register myfile.journal
pyLedger accounts myfile.journal
pyLedger print myfile.journal
pyLedger stats myfile.journal
```

## Development

```bash
# Run all tests
python -m unittest discover tests/

# Run a specific test module
python -m unittest tests.test_parser
```

See [docs/architecture.md](docs/architecture.md) for module design and
[docs/api-spec.md](docs/api-spec.md) for the public API.

## Hledger Compatibility

See [docs/hledger-compatibility.md](docs/hledger-compatibility.md) for which
hledger journal features are supported in v1.
