# PyLedger Usage Guide

PyLedger can be used as a command-line tool or as a Python library.

---

## CLI Usage

### Syntax

```bash
PyLedger <command> <journal-file>
```

You can also invoke it as a Python module (equivalent):

```bash
python -m PyLedger <command> <journal-file>
```

---

### `print` — Display transactions

Prints all transactions from the journal in a human-readable format.

```bash
PyLedger print myledger.journal
```

Example output:

```
2024-01-01 Opening balance
    assets:bank:checking                        £1000.00
    equity:opening-balances

2024-01-10 * Supermarket
    expenses:food                               £45.00
    assets:bank:checking
```

---

### `balance` — Account balances

Prints the net balance for every account.

```bash
PyLedger balance myledger.journal
```

---

### `register` — Transaction register

Prints a chronological list of all postings with running balances.

```bash
PyLedger register myledger.journal
```

---

### `accounts` — List accounts

Prints all account names found in the journal, sorted alphabetically.

```bash
PyLedger accounts myledger.journal
```

---

### `stats` — Journal statistics

Prints a summary: file name, transaction count, account count, date range,
and commodities used.

```bash
PyLedger stats myledger.journal
```

---

## Python Library Usage

```python
import PyLedger

# Load a journal file
journal = PyLedger.load("myledger.journal")

# Access transactions directly
for txn in journal.transactions:
    print(txn.date, txn.description)

# Run reports (returns data, not formatted strings)
account_list = journal.accounts()   # list[str]
balances     = journal.balance()    # dict[str, Decimal]
rows         = journal.register()   # list[RegisterRow]
summary      = journal.stats()      # JournalStats
```

See [python-api.md](python-api.md) for full library documentation.

---

## Getting Help

```bash
PyLedger --help
```
