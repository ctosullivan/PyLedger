# PyLedger Python API

PyLedger can be used as a Python library. The public API is designed to be
simple: load a journal file, then call report methods on the returned object.

---

## Loading a Journal

```python
import PyLedger

journal = PyLedger.load("myfile.journal")
```

`PyLedger.load()` accepts `.journal` or `.ledger` files and returns a
`Journal` object. It fully supports the `include` directive — included files
are resolved and expanded recursively before parsing.

Raises `FileNotFoundError` if the file does not exist, or `ParseError` if
the file is malformed, uses an unsupported extension, contains a circular
include, or has a glob pattern that matches no files.

You can also call the lower-level text parser directly (no file I/O, no
include directive support):

```python
from PyLedger.parser import parse_string

journal = parse_string("2024-01-01 Test\n    assets:bank  £100\n    equity\n")
```

---

## The `Journal` Object

A `Journal` holds all parsed data from the file.

```python
journal.transactions   # list[Transaction]
journal.prices         # list[PriceDirective]  — from P directives
journal.source_file    # str | None  — absolute path of the root file
journal.included_files # int  — count of distinct files pulled in via include
```

### Report methods

All report methods are available directly on the `Journal` object:

```python
account_list = journal.accounts()   # list[str] — sorted unique account names
balances     = journal.balance()    # dict[str, Decimal] — net balance per account
rows         = journal.register()   # list[RegisterRow] — chronological postings
summary      = journal.stats()      # JournalStats — counts, date range, etc.
```

> **Note:** Report methods currently raise `NotImplementedError` — they will
> be implemented in Milestone 2.

---

## Data Models

### `Transaction`

```python
txn.date          # datetime.date
txn.description   # str
txn.postings      # list[Posting]
txn.cleared       # bool  — True if marked with *
txn.pending       # bool  — True if marked with !
txn.code          # str   — transaction code in parentheses, e.g. "INV-42"
txn.comment       # str   — inline comment text
```

### `Posting`

```python
posting.account   # str          — e.g. "expenses:food"
posting.amount    # Amount|None  — None means elided (inferred at report time)
```

### `Amount`

```python
amount.quantity   # Decimal  — numeric value
amount.commodity  # str      — e.g. "£", "EUR", "AAPL"
```

### `PriceDirective`

```python
price.date        # datetime.date
price.commodity   # str     — the commodity being priced, e.g. "AAPL"
price.price       # Amount  — the price expressed as an Amount
```

---

## Error Handling

```python
from PyLedger.parser import ParseError

try:
    journal = PyLedger.load("myfile.journal")
except FileNotFoundError:
    print("File not found")
except ParseError as e:
    print(f"Parse error on line {e.line_number}: {e}")
```

---

## Example: Iterate Transactions

```python
import PyLedger

journal = PyLedger.load("myfile.journal")

for txn in journal.transactions:
    status = "*" if txn.cleared else ("!" if txn.pending else " ")
    print(f"{txn.date} {status} {txn.description}")
    for posting in txn.postings:
        if posting.amount:
            print(f"    {posting.account}  {posting.amount.commodity}{posting.amount.quantity}")
        else:
            print(f"    {posting.account}")
    print()
```
