# Journal Format Reference

PyLedger reads `.journal` and `.ledger` files. The format follows the
[hledger 1.52](https://hledger.org/1.52/hledger.html) journal specification.

---

## Transaction Block

A transaction block has a header line followed by one or more posting lines,
terminated by a blank line (or end of file).

```
2024-01-15 * (INV-42) Groceries  ; weekly shop
    expenses:food:groceries   £85.40
    assets:bank:checking
```

### Header fields (in order)

| Field | Required | Example | Notes |
|---|---|---|---|
| Date | Yes | `2024-01-15` | See Date Formats below |
| Status flag | No | `*` or `!` | `*` = cleared, `!` = pending |
| Code | No | `(INV-42)` | Any text in parentheses |
| Description | No | `Groceries` | Free text |
| Inline comment | No | `; weekly shop` | After `;` |

---

## Date Formats

All three separator characters are accepted. Leading zeros on month and day
are optional. The year may be omitted — PyLedger infers it from the current
calendar year.

| Format | Example |
|---|---|
| `YYYY-MM-DD` | `2024-01-15` |
| `YYYY/MM/DD` | `2024/1/15` |
| `YYYY.MM.DD` | `2024.1.15` |
| `MM-DD` | `01-15` (year inferred) |
| `M/D` | `1/15` (year inferred) |

---

## Postings

Each posting line maps an account name to an amount. The account name and
amount **must** be separated by two or more spaces. A single space is treated
as part of the account name.

```
    expenses:food:groceries   £85.40     ← two spaces before £
    assets:fun money          £10.00     ← "fun money" is part of the account name
```

**Elided amount:** Exactly one posting per transaction may omit its amount.
PyLedger records it as `None`; the value is inferred at report time.

```
    assets:bank:checking                 ← no amount — inferred from other postings
```

---

## Amounts

| Style | Example | Notes |
|---|---|---|
| Prefix symbol | `£30.00`, `$10` | Symbol before quantity |
| Suffix symbol | `30.00 EUR` | Symbol after quantity |
| Negative | `-£5.00` | Leading minus sign |
| Thousands | `1,234.56` | Comma thousands, period decimal |
| Integer | `£100` | No decimal part required |

---

## Account Names

- Colon-separated hierarchy: `expenses:food:restaurants`
- Case-sensitive: `Assets:Bank` ≠ `assets:bank`
- Spaces allowed: `expenses:fun money` (use two spaces before the amount)

---

## Comments

```
; whole-line comment
# also a whole-line comment

2024-01-15 Coffee  ; inline comment on the transaction header
    expenses:food  £4.50  ; inline comment on a posting
    assets:bank
    ; indented follow-on comment — silently skipped
```

**Block comments:**

```
comment
Everything here is ignored, including
  2024-01-01 fake transaction
end comment
```

An unclosed `comment` block silently consumes the rest of the file.

---

## P Directive (Market Prices)

Declares a commodity price on a given date. Used for valuation reports.

```
P 2024-03-01 AAPL $179.00
P 2024-03-15 EUR  1.08 USD
```

Syntax: `P DATE COMMODITY PRICE`

Price directives are stored in `journal.prices` and are global (apply to all
entries in the file).

---

## Alias Directive (Account Name Rewriting)

Rewrites account names in following entries, within the current file.

```
; Simple substitution
alias assets:savings=assets:bank:savings

; Regex substitution (backreferences supported)
alias /\./=:

; Reset all active aliases
end aliases
```

Syntax: `alias OLD=NEW` or `alias /REGEX/=REPLACEMENT`

Aliases apply from the directive to `end aliases` or end of file, whichever
comes first.

---

## Unsupported in v1

The following hledger features are not supported in PyLedger v1:

- Timeclock, timedot, CSV, SSV, TSV, rules file formats
- Secondary dates (`2024-01-15=2024-01-20`)
- Lot prices (`10 AAPL @ $150`)
- Balance assertions (`assets:checking = £500`)
- Virtual postings (`(expenses:food)` or `[expenses:food]`)
- Auto postings (`= expenses:food` rules)
- Periodic transactions (`~ monthly`)
- `include` directive
- Decimal comma style (`1.234,56`)
- Smart dates (`today`, `last month`, etc.)
