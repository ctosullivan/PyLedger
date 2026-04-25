# Architecture

## Overview

PyLedger follows a linear data-flow pipeline:

```
Journal file(s) (.journal / .ledger)
        │
        ▼
  [ loader.py ]        ← File I/O, include directive expansion, path resolution,
        │                glob matching, and circular include detection
        ▼
  [ parser.py ]        ← Pure text → structured Python objects (no file I/O)
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

### `PyLedger/loader.py`

**Single responsibility**: File I/O, include directive expansion, path
resolution, glob matching, and circular include detection.

- `load_journal(path)` — public entry point; reads a `.journal` or `.ledger`
  file and returns a fully populated `Journal` object
- Recursively expands `include` directives before parsing (text-expansion
  strategy), so directive scope propagates naturally through included content
- Resolves include paths: relative (to containing file's directory), absolute,
  and tilde (`~`) expansion; glob patterns via `glob.glob(recursive=True)`
- Detects circular includes by tracking visited paths
- Populates `journal.source_file` and `journal.included_files`
- Raises `ParseError` for unsupported extensions, format prefixes, circular
  includes, or glob patterns that match no files
- Raises `FileNotFoundError` if the root file or a non-glob included file does
  not exist

### `PyLedger/parser.py`

**Single responsibility**: Convert raw `.journal` text (a Python string) into
`Transaction` objects and a `Journal` container.

- `parse_string(text)` — the sole public function; operates on text only,
  performs no file I/O
- Reads journal text line by line via a state machine
- Recognises transaction headers, postings, comments, and directives
- Raises `ParseError` with line number on malformed input
- Does **not** perform any balance validation, file loading, or reporting logic
- `include` directive lines encountered in raw text are silently skipped
  (expansion is always done by `loader.py` before `parse_string` is called)

### `PyLedger/models.py`

**Single responsibility**: Define the canonical Python data structures for
journal entries.

Core types:
- `Amount` — a numeric value paired with a commodity symbol
- `Posting` — an account name plus an optional `Amount`
- `Transaction` — a date, optional cleared/pending flag, description, and list of `Posting`s
- `Journal` — top-level container: a list of `Transaction`s, a list of
  `PriceDirective`s, `source_file`, and `included_files` count

Models are plain dataclasses. They contain no parsing or reporting logic.

### `PyLedger/reports.py`

**Single responsibility**: Accept a `Journal` and produce structured report
data (not formatted strings).

Reports:
- `balance(journal, ...)` → mapping of account name → running balance
- `register(journal, ...)` → list of register rows (date, description, amount, balance)
- `accounts(journal)` → sorted list of account names
- `stats(journal)` → `JournalStats` dataclass with summary statistics

Reports do **not** print to stdout — they return data that `cli.py` formats.

### `PyLedger/cli.py`

**Single responsibility**: Parse command-line arguments and coordinate
`loader` → `reports` → formatted output.

- Uses `argparse` from the standard library
- Calls `loader.load_journal()` to load the journal (with include support)
- Calls the appropriate `reports.*` function
- Formats and prints the result to stdout

---

## Error Handling Strategy

| Layer | Error type | Action |
|---|---|---|
| `loader` | `ParseError` | Raised for extension/format/circular/glob errors; line numbers re-attributed to original source file |
| `loader` | `FileNotFoundError` | Raised if root or non-glob included file is missing |
| `parser` | `ParseError` | Raised with line number and message |
| `reports` | `ValueError` | Raised for invalid arguments |
| `cli` | Any | Caught, printed to stderr, exit code 1 |

---

## Design Principles

- Each module imports only from modules below it in the pipeline
  (`cli` → `loader` → `parser`/`models`; `reports` → `models`)
- No circular imports
- No global mutable state
