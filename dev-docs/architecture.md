# Architecture

## Overview

PyLedger follows a linear data-flow pipeline:

```
Journal file (.journal)
        │
        ▼
  [ parser.py ]        ← Reads raw text, produces structured Python objects
        │
        ▼
  [ models.py ]        ← Core data model: Transaction, Posting, Amount, etc.
        │
        ▼
  [ reports.py ]       ← Consumes model objects, produces report data
        │
        ▼
  [ cli.py ]           ← Formats and prints report data for the terminal
```

---

## Module Responsibilities

### `pyLedger/parser.py`

**Single responsibility**: Convert a raw `.journal` file (or string) into a
list of `Transaction` objects (and other top-level journal entries).

- Reads journal text line by line
- Recognises transaction headers, postings, and comments
- Raises `ParseError` on malformed input
- Does **not** perform any balance validation or reporting logic

### `pyLedger/models.py`

**Single responsibility**: Define the canonical Python data structures for
journal entries.

Core types:
- `Amount` — a numeric value paired with a commodity symbol
- `Posting` — an account name plus an optional `Amount`
- `Transaction` — a date, optional cleared flag, description, and list of `Posting`s
- `Journal` — a collection of `Transaction`s (the top-level container)

Models are plain dataclasses (or similar). They contain no parsing or
reporting logic.

### `pyLedger/reports.py`

**Single responsibility**: Accept a `Journal` and produce structured report
data (not formatted strings).

Planned reports:
- `balance(journal, ...)` → mapping of account name → running balance
- `register(journal, ...)` → list of register rows (date, description, amount, balance)
- `accounts(journal)` → sorted list of account names
- `stats(journal)` → summary statistics dict

Reports do **not** print to stdout — they return data that `cli.py` formats.

### `pyLedger/cli.py`

**Single responsibility**: Parse command-line arguments and coordinate
`parser` → `reports` → formatted output.

- Uses `argparse` from the standard library
- Calls `parser.parse_file()` to load the journal
- Calls the appropriate `reports.*` function
- Formats and prints the result to stdout

---

## Error Handling Strategy

| Layer | Error type | Action |
|---|---|---|
| `parser` | `ParseError` | Raised with line number and message |
| `reports` | `ValueError` | Raised for invalid arguments |
| `cli` | Any | Caught, printed to stderr, exit code 1 |

---

## Design Principles

- Each module imports only from modules below it in the pipeline
  (`cli` → `reports` → `parser`/`models`; `parser` → `models`)
- No circular imports
- No global mutable state
