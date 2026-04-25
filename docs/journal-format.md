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

Declares a commodity price on a given date.

```
P 2024-03-01 AAPL $179.00
P 2024-03-15 EUR  1.08 USD
```

Syntax: `P DATE COMMODITY PRICE`

Each P directive is stored as a `PriceDirective` in `journal.prices`.
`journal.prices` is a list that holds every price declaration found in the
file, in the order they appear. Each entry records: the date of the price,
the commodity being priced (e.g. `AAPL`, `EUR`), and the price expressed
as an amount (e.g. `$179.00`).

---

## Include Directive (Multiple Files)

Embeds the contents of another journal file at the point of the directive, as
if the entries were written inline. Includes are processed recursively.

```
include accounts.journal
include ../shared/prices.journal
include ~/main.journal
include /home/user/finances.journal
include reports/*.journal
include **.journal
```

Syntax: `include PATH`

### Path resolution

| Path form | Resolution |
|---|---|
| `relative/path.journal` | Relative to the containing file's directory |
| `/absolute/path.journal` | Used as-is |
| `~/path.journal` | Tilde expanded to the home directory |
| `glob_*.journal` | Glob-expanded (see below) |

### Glob patterns

Glob characters `*`, `**`, `?`, and `[range]` are supported:

- `*` — matches any sequence of characters that are not path separators
- `**` — matches zero or more subdirectories and/or filename prefix characters
- `?` — matches any single character
- `[a-z]` — matches any character in the given range

Examples:

```
; Include all .journal files in the current directory
include *.journal

; Include all .journal files in this directory tree
include **.journal

; Include year-named files
include 202?.journal
```

The containing file is **always excluded** from glob results, even if the
pattern would match it.

A glob pattern that matches no files raises a `ParseError`.

### Format prefixes

Format prefixes (e.g. `timedot:`, `csv:`) are **not supported** in PyLedger v1.
Using them raises a `ParseError`. Remove the prefix and ensure the file has a
`.journal` or `.ledger` extension.

### Restrictions

Only `.journal` and `.ledger` files may be included; other extensions raise a
`ParseError`. Circular includes (A includes B which includes A) raise a
`ParseError`. Active directives (such as `alias`) at the point of the
`include` apply to the included file's entries.

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
- Decimal comma style (`1.234,56`)
- Smart dates (`today`, `last month`, etc.)
