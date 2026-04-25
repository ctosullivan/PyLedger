# API Specification

Status key: `[IMPLEMENTED]` · `[STUB — Milestone 2]` · `[PLANNED]`

---

## Top-level (`PyLedger/__init__.py`)

### `load` `[IMPLEMENTED]`

```python
def load(path: str | os.PathLike) -> Journal:
    """Load a .journal or .ledger file and return a Journal object.

    Alias for loader.load_journal(). Supports include directives.
    Intended for programmatic use:
        import PyLedger
        journal = PyLedger.load("myfile.journal")

    Raises:
        FileNotFoundError: if the path or a non-glob included file does not exist.
        ParseError: if an extension is unsupported, a format prefix is used,
                    a circular include is detected, a glob matches nothing,
                    or the file contents are malformed.
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
    account: str                   # e.g. "expenses:food"
    amount: Amount | None = None   # None means "infer from other postings"
    source_line: int | None = None # 1-based line number in source file; None for programmatic objects
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
    cleared: bool = False          # True if marked with "*"
    pending: bool = False          # True if marked with "!"
    code: str = ""                 # Optional transaction code in parentheses
    comment: str = ""              # Inline or trailing comment text
    source_line: int | None = None # 1-based line number of the header in source file
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

Commodity valuation using these records (converting amounts between commodities
in reports) is in scope for v1 and will be implemented in Milestone 2.

---

### `Journal` `[IMPLEMENTED]`

```python
@dataclass
class Journal:
    transactions: list[Transaction]
    prices: list[PriceDirective] = field(default_factory=list)
    declared_accounts: list[str] = field(default_factory=list)
    declared_commodities: list[str] = field(default_factory=list)
    declared_payees: list[str] = field(default_factory=list)
    source_file: str | None = None
    included_files: int = 0   # count of distinct files pulled in via include
```

Top-level container for all parsed journal data.

`declared_accounts`, `declared_commodities`, and `declared_payees` are populated
by `account`, `commodity`, and `payee` directives respectively. They are used
by the strict-mode checks in `checks.py`.

`included_files` is set by `loader.load_journal()`. When `parse_string()` is
called directly (no file I/O), it remains `0`.

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

---

## `PyLedger/loader.py`

### `load_journal` `[IMPLEMENTED]`

```python
def load_journal(path: str | os.PathLike) -> Journal:
    """Load a .journal or .ledger file and return a Journal object.

    Handles include directives recursively. Included files are expanded at
    the point of the directive before parsing, preserving directive scope
    (e.g. an alias active before an include applies to included content).

    Path resolution in include directives:
      - ~/...       tilde expanded to the home directory
      - /abs/path   used as-is (absolute)
      - relative    resolved relative to the containing file's directory
      - Globs (* ** ? [range]) expanded via glob.glob; the containing file
        is always excluded from results.

    Populates journal.source_file (absolute path string) and
    journal.included_files (count of distinct included files).

    Raises:
        FileNotFoundError: if the root path or a non-glob included file
            does not exist.
        ParseError: if an extension is unsupported, a format prefix is
            used (e.g. timedot:), a circular include is detected, a glob
            matches no files, or the file contents are malformed.
    """
```

> **Note:** `parse_file()` was removed in this milestone. Use `load_journal()`
> (or the `PyLedger.load` alias) for all file loading.

---

### `load_journal_stdin` `[IMPLEMENTED]`

```python
def load_journal_stdin() -> Journal:
    """Read a journal from stdin and return a Journal object.

    Parses the full stdin contents as hledger journal text.
    Sets source_file to "(stdin)". included_files is always 0.

    Raises:
        ParseError: if the stdin content is malformed.
    """
```

---

### `merge_journals` `[IMPLEMENTED]`

```python
def merge_journals(journals: list[Journal]) -> Journal:
    """Merge a list of Journal objects into a single Journal.

    Transactions, prices, declared_accounts, declared_commodities, and
    declared_payees are all concatenated in input order.
    source_file is taken from the first journal.
    included_files is the sum across all input journals.

    Raises:
        ValueError: if journals is empty.
    """
```

---

## `PyLedger/checks.py`

### `CheckError` `[IMPLEMENTED]`

```python
@dataclass
class CheckError:
    check_name: str   # e.g. "autobalanced", "accounts"
    message: str      # human-readable single-line description
```

Also re-exported from `PyLedger.__init__` as `PyLedger.CheckError`.

---

### Check constants `[IMPLEMENTED]`

```python
BASIC_CHECK_NAMES:  tuple[str, ...] = ("parseable", "autobalanced")
STRICT_CHECK_NAMES: tuple[str, ...] = ("accounts", "commodities")
OTHER_CHECK_NAMES:  tuple[str, ...] = ("payees", "ordereddates", "uniqueleafnames")
```

---

### Individual check functions `[IMPLEMENTED]`

All return `list[CheckError]` — empty list means no errors.

| Function | Tier | Description |
|---|---|---|
| `check_parseable(journal)` | basic | Always `[]` — already parsed |
| `check_autobalanced(journal)` | basic | Each transaction nets to zero per commodity; one elided posting allowed |
| `check_accounts(journal)` | strict | All posting accounts appear in `declared_accounts` |
| `check_commodities(journal)` | strict | All commodity symbols in amounts appear in `declared_commodities`; zero-amount postings (commodity `""`) are exempt |
| `check_payees(journal)` | other | All transaction descriptions appear in `declared_payees` |
| `check_ordereddates(journal)` | other | Transactions in non-decreasing date order |
| `check_uniqueleafnames(journal)` | other | No two accounts share the same final colon-segment |

---

### `run_basic_checks` `[IMPLEMENTED]`

```python
def run_basic_checks(journal: Journal) -> list[CheckError]:
    """Run parseable + autobalanced checks. Always run by the CLI."""
```

---

### `run_strict_checks` `[IMPLEMENTED]`

```python
def run_strict_checks(journal: Journal) -> list[CheckError]:
    """Run basic checks plus accounts + commodities checks."""
```

---

### `run_checks` `[IMPLEMENTED]`

```python
def run_checks(
    journal: Journal,
    names: list[str] | None = None,
    *,
    strict: bool = False,
) -> list[CheckError]:
    """Run basic checks always; strict checks if strict=True;
    named 'other' checks if listed in names.

    Valid names: "parseable", "autobalanced", "accounts", "commodities",
    "payees", "ordereddates", "uniqueleafnames".

    Raises:
        ValueError: if an unknown check name is provided.
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

### `stats` `[IMPLEMENTED]`

```python
@dataclass
class JournalStats:
    """Summary statistics for a journal. No runtime fields — CLI measures those."""
    source_file: str | None
    included_files: int              # count of distinct files pulled in via include
    transaction_count: int
    date_range: tuple[datetime.date, datetime.date] | None   # (first, last)
    last_txn_date: datetime.date | None
    last_txn_days_ago: int | None    # (today - last_txn_date).days
    txns_span_days: int | None       # (last - first).days + 1
    txns_per_day: float              # transaction_count / txns_span_days, else 0.0
    txns_last_30_days: int
    txns_per_day_last_30: float
    txns_last_7_days: int
    txns_per_day_last_7: float
    payee_count: int                 # unique descriptions
    account_count: int
    account_depth: int               # max colon-segment depth across all accounts
    commodity_count: int
    commodities: list[str]           # sorted commodity symbols
    price_count: int                 # len(journal.prices)

def stats(journal: Journal) -> JournalStats:
    """Return summary statistics for the journal."""
```

Also accessible as `PyLedger.JournalStats` (re-exported from `__init__.py`).

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
PyLedger [-f FILE]... [-s] [-v] [-1] [-o FILE] <command> [args...]
python -m PyLedger [-f FILE]... [-s] [-v] [-1] [-o FILE] <command> [args...]

Flags:
  -f, --file         Read data from FILE, or stdin if -. May be specified
                     more than once; all files are merged in order. If not
                     given, falls back to the positional argument, then
                     $LEDGER_FILE, then ~/.hledger.journal.
  -s, --strict       Enable strict mode: also check that all posting accounts
                     and commodity symbols are declared via account/commodity
                     directives. Equivalent to running check accounts commodities
                     in addition to the default basic checks.
  -v, --verbose      More detailed output (stats: show commodity names)
  -1                 Single tab-separated line (stats only)
  -o, --output-file  Write output to FILE instead of stdout

Commands:
  balance             Print account balances
  register            Print a register of transactions
  accounts            List all accounts
  print               Print transactions in journal format
  stats               Print journal statistics
  check [CHECK...]    Run validation checks; default runs basic checks only.
                      Named checks: parseable autobalanced accounts commodities
                                    payees ordereddates uniqueleafnames
```

**Default validation**: all commands run `autobalanced` and `parseable` checks
automatically before executing. Any failure prints an error to stderr and exits 1.

**`check` command**: accepts zero or more check names as positional arguments.
With no names, runs only the basic checks. With `-s`, also runs `accounts` and
`commodities`. Named `other` checks (`payees`, `ordereddates`, `uniqueleafnames`)
are run only if explicitly listed. Silent on success (exit 0); errors to stderr
(exit 1).

The positional `journal-file` argument (when not using `check`) is a
backward-compatible shorthand for `-f FILE`. Specifying both `-f` and a
positional argument is an error.
