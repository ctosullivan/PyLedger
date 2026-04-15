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

## Acknowledgements

PyLedger is a Python implementation inspired by two pioneering plain-text
accounting projects. We gratefully acknowledge their authors and contributors.

### Ledger

**John Wiegley** created Ledger, the original plain-text double-entry accounting
tool, which established the journal file format and accounting model that this
ecosystem is built upon.

  https://github.com/ledger/ledger

### hledger

**Simon Michael** created hledger, a Haskell implementation of Ledger's concepts,
which has since evolved its own rich feature set and extensive documentation.
PyLedger's journal format support is modelled primarily on the hledger 1.52
specification.

  https://github.com/simonmichael/hledger

A full list of hledger contributors can be found at:

  https://github.com/simonmichael/hledger/blob/main/doc/CREDITS.md

Their work — and the broader plain-text accounting community — makes PyLedger
possible.