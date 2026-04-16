# API Specification

Status key: `[IMPLEMENTED]` · `[STUB — Milestone 2]` · `[PLANNED]`

---

## Top-level (`PyLedger/__init__.py`)

### `load` `[IMPLEMENTED]`

```python
def load(path: str | os.PathLike) -> Journal:
    """Load a .journal or .ledger file and return a Journal object.

    Alias for parse_file(). Intended for programmatic use:
        import PyLedger
        journal = PyLedger.load("myfile.journal")

    Raises:
        FileNotFoundError: if the path does not exist.
        ParseError: if the extension is unsupported or the file is malformed.
    """
```

Also invocable as a module:

```
python -m PyLedger <command> <journal-file>
```

---

## `PyLedger/models.py`

### `Amount` `[IMPLEMENTED]`

```python
@dataclass
class Amount:
    quantity: Decimal
    commodity: str  # e.g. "£", "$", "EUR", "AAPL"
```

Represents a single monetary or commodity amount.

---

### `Posting` `[IMPLEMENTED]`

```python
@dataclass
class Posting:
    account: str          # e.g. "expenses:food"
    amount: Amount | None  # None means "infer from other postings"
```

One line within a transaction, mapping an account to an amount.

The wire format requires **two or more spaces** between the account name and the
amount. A single space is treated as part of the account name, allowing names such
as `expenses:fun money`. When no double-space separator is present, the posting has
no amount (`amount=None` — elided).

---

### `Transaction` `[IMPLEMENTED]`

```python
@dataclass
class Transaction:
    date: datetime.date
    description: str
    postings: list[Posting]
    cleared: bool = False   # True if marked with "*"
    pending: bool = False   # True if marked with "!"
    code: str = ""          # Optional transaction code in parentheses
    comment: str = ""       # Inline or trailing comment text
```

Represents a complete journal transaction entry.

**Wire → model mapping** (see `dev-docs/hledger-compatibility.md` for block delimiters):

```
"2024-01-15 * (INV-42) Groceries ; comment"
  │            │  │       │        │
  │            │  │       │        └── comment     = "comment"
  │            │  │       └─────────── description = "Groceries"
  │            │  └─────────────────── code        = "INV-42"
  │            └────────────────────── cleared     = True  (pending = False)
  └─────────────────────────────────── date        = date(2024, 1, 15)
```

`postings` preserves journal order. A `Posting` with `amount=None` is an *elided*
posting whose value is inferred from the other postings at reporting time.

---

### `PriceDirective` `[IMPLEMENTED]`

```python
@dataclass
class PriceDirective:
    date: datetime.date
    commodity: str   # The commodity being priced, e.g. "AAPL", "EUR"
    price: Amount    # The price expressed as an Amount (quantity + currency symbol)
```

Represents one `P` directive from the journal. Stored in `Journal.prices`.

Example journal line: `P 2024-03-01 AAPL $179.00`

---

### `Journal` `[IMPLEMENTED]`

```python
@dataclass
class Journal:
    transactions: list[Transaction]
    prices: list[PriceDirective] = field(default_factory=list)
    source_file: str | None = None
```

Top-level container for all parsed journal data.

**Report methods** (delegate to `PyLedger.reports` via lazy import):

```python
def balance(self, accounts: list[str] | None = None) -> dict[str, Decimal]: ...
def register(self, accounts: list[str] | None = None) -> list[RegisterRow]: ...
def accounts(self) -> list[str]: ...
def stats(self) -> JournalStats: ...
```

All four methods are currently `[STUB — Milestone 2]` — they raise
`NotImplementedError` until the reports module is implemented.

---

## `PyLedger/parser.py`

### `ParseError` `[IMPLEMENTED]`

```python
class ParseError(ValueError):
    def __init__(self, message: str, line_number: int | None = None) -> None: ...
```

Raised on malformed journal input. `line_number` is 1-based when available.

---

### `parse_string` `[IMPLEMENTED]`

```python
def parse_string(text: str, default_year: int | None = None) -> Journal:
    """Parse a journal from a string and return a Journal object.

    Accepted date formats: YYYY-MM-DD, YYYY/MM/DD, YYYY.MM.DD, and year-omitted
    forms such as M/DD or MM-DD. Leading zeros on month and day are optional.
    When the year is omitted, default_year is used (defaults to the current
    calendar year when None).

    Raises:
        ParseError: if the input is not valid hledger journal syntax.
    """
```

---

### `parse_file` `[IMPLEMENTED]`

```python
def parse_file(path: str | os.PathLike) -> Journal:
    """Read a .journal or .ledger file from disk and return a Journal object.

    Supported extensions: .journal, .ledger
    See dev-docs/hledger-compatibility.md for the full format support matrix.

    Raises:
        FileNotFoundError: if the path does not exist.
        ParseError: if the extension is not supported, or if the file
                    contents are not valid hledger journal syntax.
    """
```

---

## `PyLedger/reports.py`

All report functions accept a `Journal` as their first argument and are also
accessible as methods on `Journal` directly (e.g. `journal.balance()`).

### `balance` `[STUB — Milestone 2]`

```python
def balance(
    journal: Journal,
    accounts: list[str] | None = None,
) -> dict[str, Decimal]:
    """Return a mapping of account name to net balance."""
```

---

### `register` `[STUB — Milestone 2]`

```python
@dataclass
class RegisterRow:
    date: datetime.date
    description: str
    account: str
    amount: Amount
    running_balance: Decimal

def register(
    journal: Journal,
    accounts: list[str] | None = None,
) -> list[RegisterRow]:
    """Return a chronological list of register rows."""
```

---

### `accounts` `[STUB — Milestone 2]`

```python
def accounts(journal: Journal) -> list[str]:
    """Return a sorted list of all unique account names in the journal."""
```

---

### `stats` `[STUB — Milestone 2]`

```python
@dataclass
class JournalStats:
    source_file: str | None
    transaction_count: int
    account_count: int
    date_range: tuple[datetime.date, datetime.date] | None  # (first, last)
    commodity_count: int

def stats(journal: Journal) -> JournalStats:
    """Return summary statistics for the journal."""
```

---

## `PyLedger/cli.py`

### `main` `[IMPLEMENTED]`

```python
def main(argv: list[str] | None = None) -> int:
    """Entry point for the PyLedger CLI.

    Args:
        argv: Argument list (defaults to sys.argv[1:] when None).

    Returns:
        Exit code (0 = success, 1 = error).
    """
```

CLI interface (via `pyproject.toml` `[project.scripts]` and `PyLedger/__main__.py`):

```
PyLedger <command> [options] <journal-file>
python -m PyLedger <command> [options] <journal-file>

Commands:
  balance    Print account balances
  register   Print a register of transactions
  accounts   List all accounts
  print      Print transactions in journal format
  stats      Print journal statistics
```
