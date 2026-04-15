# Hledger Compatibility

Reference: https://hledger.org/1.52/hledger.html

This document tracks which hledger format features are in scope for **v1** of
PyLedger, which are explicitly out of scope, and which are undecided.

---

## Supported File Formats

PyLedger accepts the following file extensions. This is a deliberate subset of
what hledger 1.52 supports (full comparison below).

| Extension | Description |
|---|---|
| `.journal` | Primary hledger journal format — fully supported |
| `.ledger` | Ledger-CLI compatible journal syntax — supported to the same degree as `.journal`; both use identical parsing in PyLedger v1 |

### Deviation from hledger 1.52

hledger 1.52 supports seven format families. The table below documents every
format and PyLedger's stance. Reference: https://hledger.org/1.52/hledger.html#data-formats

| hledger 1.52 format | Extensions | PyLedger v1 |
|---|---|---|
| journal | `.journal` `.j` `.hledger` `.ledger` | **Supported** for `.journal` and `.ledger` only; `.j` and `.hledger` aliases are **not** accepted |
| timeclock | `.timeclock` | **Not supported** — out of scope |
| timedot | `.timedot` | **Not supported** — out of scope |
| csv | `.csv` | **Not supported** — out of scope |
| ssv | `.ssv` | **Not supported** — out of scope |
| tsv | `.tsv` | **Not supported** — out of scope |
| rules | `.rules` | **Not supported** — out of scope |

**Note on `.ledger`:** PyLedger does not aim for full Ledger-CLI compatibility.
The `.ledger` extension is accepted because the hledger-compatible subset of
Ledger syntax is identical to `.journal` syntax within v1 scope. Ledger-specific
features (e.g. automated transactions, periodic transactions, value expressions)
remain out of scope and will raise `ParseError` or be silently ignored per the
rules in the "Out of Scope" table below.

---

## Transaction Block Structure

A transaction block is the fundamental unit of a journal file.

```
; Transaction block — annotated

2024-01-15 * (INV-42) Groceries  ; comment   ← block BEGINS here (date required)
│           │  │        │          │
│           │  │        │          └─ inline comment          (optional)
│           │  │        └──────────── description             (optional, free text)
│           │  └───────────────────── transaction code        (optional, parenthesised)
│           └──────────────────────── status: * cleared / ! pending (optional)
└──────────────────────────────────── date YYYY-MM-DD         (REQUIRED)

    expenses:food:groceries   £85.40          ← posting lines (2+ space indent)
    assets:bank:checking                      ← elided amount (at most ONE per block)

                                              ← blank line ENDS the block (or EOF)
```

**Delimiter rules:**
- A block **begins** on any non-indented line whose first token matches `\d{4}-\d{2}-\d{2}`
- A block **ends** on the first blank line that follows the header, or at end of file
- The field order on the header line is fixed: `date [flag] [(code)] [description] [; comment]`
- Posting lines are identified by 2+ leading spaces (or a tab)
- Within a posting line, the account name and amount **must** be separated by
  two or more spaces; a single space is treated as part of the account name
  (e.g. `expenses:fun money`) — a `ParseError` is raised if no double-space
  separator is found and no amount can be parsed
- Exactly **one** posting per block may omit its amount (the *elided* posting); two or
  more elided amounts in the same block is a `ParseError`

---

## In Scope (v1)

### Transactions

| Feature | Example | Notes |
|---|---|---|
| Simple date | `2024-01-15`, `2024/1/15`, `2024.1.15`, `1/15` | Separators: `-` `/` `.`; leading zeros optional; year may be omitted (inferred from current date) |
| Description | `2024-01-15 Groceries` | Free text after the date |
| Cleared flag | `2024-01-15 * Groceries` | `*` = cleared |
| Pending flag | `2024-01-15 ! Groceries` | `!` = pending |
| Transaction code | `2024-01-15 (INV-42) Groceries` | Parenthesised string before description |
| Postings | `  expenses:food  £30.00` | Two-space indent; account and amount **must** be separated by two or more spaces |
| Elided amount | `  assets:checking` | One posting per transaction may omit amount; no separator required when amount is absent |

### Account Names

| Feature | Example | Notes |
|---|---|---|
| Hierarchical names | `expenses:food:restaurants` | Colon-separated segments |
| Mixed case | `Assets:Bank` | Case-sensitive |
| Spaces in names | `expenses:fun money` | Supported |

### Amounts

| Feature | Example | Notes |
|---|---|---|
| Prefixed symbol | `£30.00`, `$10` | Symbol before quantity |
| Suffixed symbol | `30.00 EUR` | Symbol after quantity (space optional) |
| Negative amounts | `-£5.00` | Leading minus |
| Decimal separator | `1,234.56` | Comma thousands separator, period decimal |
| No decimal | `£100` | Integer quantities |

### Comments

| Feature | Example | Notes |
|---|---|---|
| Whole-line `;` | `; this is a comment` | Any line whose first non-space character is `;` |
| Whole-line `#` | `# another comment` | Any line whose first non-space character is `#` |
| Inline `;` on transaction | `2024-01-15 Desc  ; comment` | `;` after description; captured in `Transaction.comment` |
| Inline `;` on posting | `  expenses:food  £30  ; note` | `;` after amount; stripped during parsing |
| Follow-on comment line | `    ; continued note` | Indented line starting with `;` inside a transaction block; silently skipped |
| Block comment | `comment` / `end comment` | All lines between the two directives are skipped; unclosed block runs to EOF |

---

## Out of Scope (v1)

These features will **not** be implemented in v1. Attempting to parse them
will either be silently ignored or raise a `ParseError` — documented per
feature below.

| Feature | hledger syntax | v1 behaviour |
|---|---|---|
| Directives | `account`, `commodity`, `include`, etc. | Silently ignored (lines starting with a known keyword are skipped) |
| Auto postings | `= expenses:food` rules | `ParseError` |
| Periodic transactions | `~ monthly` | `ParseError` |
| Timeclock entries | `i`, `o`, `b`, `h` records | `ParseError` |
| Decimal comma | `1.234,56` (EU style) | Not supported — `ParseError` |
| Secondary dates | `2024-01-15=2024-01-20` | Secondary date ignored |
| Tags | `; tag:value` | Silently ignored |
| Lot prices | `10 AAPL @ $150.00` | `ParseError` |
| Balance assertions | `assets:checking = £500` | Silently ignored |
| Virtual postings | `(expenses:food)` or `[expenses:food]` | `ParseError` |
| Multi-currency auto-conversion | | Not supported |
| `include` directive | `include other.journal` | Silently ignored |

---

## Undecided / Future

- Commodity price directives (`P 2024-01-01 EUR 1.10 USD`)
- Multiple commodities in one transaction
- Strict mode (unbalanced transaction detection)
- Account type inference from name prefixes (`assets`, `liabilities`, etc.)
- Smart dates (hledger relative date expressions such as `today`, `yesterday`,
  `last month`, `next year`) — not currently planned for v1
- Comment "other syntax" — hledger accepts additional comment introducers in
  certain contexts (e.g. `*` in org-mode files); not currently planned for v1

---

## Compatibility Notes

- PyLedger does **not** aim for 100% hledger compatibility in v1.
- The goal is to correctly parse the most common single-currency personal
  finance journal files.
- When a file is not parseable, `ParseError` should include the line number
  and a clear message explaining what was unexpected.
