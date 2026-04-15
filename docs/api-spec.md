# API Specification

Status key: `[PLANNED]` = not yet implemented.

---

## `pyLedger/models.py`

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

**Wire → model mapping** (see `docs/hledger-compatibility.md` for block delimiters):

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

### `Journal` `[IMPLEMENTED]`

```python
@dataclass
class Journal:
    transactions: list[Transaction]
    source_file: str | None = None  # Path of the originating .journal or .ledger file
```

Top-level container for all parsed journal data.

---

## `pyLedger/parser.py`

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
    See docs/hledger-compatibility.md for the full format support matrix.

    Raises:
        FileNotFoundError: if the path does not exist.
        ParseError: if the file extension is not supported, or if the file
                    contents are not valid hledger journal syntax.
    """
```

---

## `pyLedger/reports.py`

All report functions accept a `Journal` as their first argument.

### `balance` `[PLANNED]`

```python
def balance(
    journal: Journal,
    accounts: list[str] | None = None,
) -> dict[str, Decimal]:
    """Return a mapping of account name to net balance.

    Args:
        journal: The parsed journal.
        accounts: Optional list of account name prefixes to filter by.
                  If None, all accounts are included.

    Returns:
        Dict mapping each account name to its net balance as a Decimal.
    """
```

---

### `register` `[PLANNED]`

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
    """Return a chronological list of register rows.

    Args:
        journal: The parsed journal.
        accounts: Optional list of account name prefixes to filter by.
    """
```

---

### `accounts` `[PLANNED]`

```python
def accounts(journal: Journal) -> list[str]:
    """Return a sorted list of all unique account names in the journal."""
```

---

### `stats` `[PLANNED]`

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

## `pyLedger/cli.py`

### `main` `[PLANNED]`

```python
def main(argv: list[str] | None = None) -> int:
    """Entry point for the pyLedger CLI.

    Args:
        argv: Argument list (defaults to sys.argv[1:] when None).

    Returns:
        Exit code (0 = success, 1 = error).
    """
```

CLI interface (via `pyproject.toml` `[project.scripts]`):

```
pyLedger <command> [options] <journal-file>

Commands:
  balance    Print account balances
  register   Print a register of transactions
  accounts   List all accounts
  print      Print transactions in journal format
  stats      Print journal statistics
```
