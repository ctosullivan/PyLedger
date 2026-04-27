# Domain Rules

Tacit knowledge about the hledger journal format and PyLedger's implementation that Claude cannot infer from code alone.

---

## Double-space separator is mandatory between account name and amount

Postings use two or more spaces (or a tab) to separate the account name from the amount. A single space is not sufficient.

```
    expenses:food  £30.00   ← valid (2+ spaces)
    expenses:food £30.00    ← invalid (1 space — rejected by _TWO_SPACE_SEP)
```

**Why it matters:** Account names may legitimately contain spaces (e.g. `assets:joint account`). The double-space is the only unambiguous delimiter.

**Implication:** Never use a single space between account and amount in fixtures or test strings.

---

## At most one elided amount per transaction block

Exactly one posting per transaction may omit its amount. The parser infers the missing amount so the transaction balances to zero. Two or more elided amounts are ambiguous and raise `ParseError`.

**Implication:** Always provide explicit amounts in test fixtures except when specifically testing elision.

---

## `Posting.amount` is `Amount | None` by design

`None` is not an error state — it means the posting has an intentionally elided amount (to be inferred at check/report time). Code accessing `.quantity` or `.commodity` must guard with `assert amt is not None` or an equivalent.

---

## P directive records a price at a point in time — it is not a global rate

`P 2024-01-01 € $1.20` means "on 2024-01-01, one € was worth $1.20". It does NOT mean all €-denominated amounts throughout the journal are worth $1.20. Commodity valuation logic must use the *closest preceding date* for a given commodity pair.

**Scope:** P directives are file-local. Whether they propagate through `include` is TBD for Milestone 2.

---

## Balance rule: all postings in a transaction must sum to zero per commodity

A transaction is balanced when the algebraic sum of all posting amounts (per commodity) is zero. This is enforced by `checks.check_autobalanced`, not by the parser.

**Elided amount rule:** If one posting has no amount, its amount is inferred as the negation of the sum of all other postings. This only works when all other postings share a single commodity.

---

## `strict` mode requires ALL accounts AND commodities to be declared

Under `-s`/`--strict`, every account name appearing in a posting must have a matching `account` directive, and every commodity symbol must have a matching `commodity` directive. The check stops at the first failure and reports it with file path and line number.

**Implication:** Strict-mode fixtures (`tests/fixtures/strict_valid.journal`) must declare every account and commodity used.

---

## Account names use `:` as a hierarchy separator

`assets:bank:checking` has three segments. The `account_depth` stat counts colon-delimited segments. Leaf uniqueness (`uniqueleafnames` check) compares only the last segment.

---

## `decimal-mark` changes the parser mode for subsequent postings only

After `decimal-mark ,`, amounts must use European format (`1.234,56`). The change is not retroactive. Mixing formats within a file after the directive is a parse error.

**Default:** Period decimal (`1234.56`). Explicit `decimal-mark .` resets to default.

---

## Commodity symbols may be prefix or suffix

`£30.00` — prefix symbol (`£`), no space.
`30.00 EUR` — suffix symbol (`EUR`), one space separator.
Both are valid; the commodity value in `Amount.commodity` is just the symbol string without spaces.

---

## `include` directive: glob vs explicit path error handling

- **Explicit path** (no glob characters): raises `FileNotFoundError` if file does not exist.
- **Glob pattern** (`*`, `**`, `?`, `[range]`): silently produces no entries if no files match — this is NOT an error.

This matches the hledger 1.52 `include` spec.
