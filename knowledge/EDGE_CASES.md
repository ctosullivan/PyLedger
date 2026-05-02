# Edge Cases

Human-identified cases that are non-obvious or would be easy to regress. Each entry records what the expected behaviour is and whether it is currently handled.

---

## EC-001 — `end comment` outside a block comment

**Trigger:** `end comment` appears in a file with no preceding `comment` directive.
**Expected behaviour:** Silently ignored. Does not raise `ParseError`.
**Source:** Identified during block-comment implementation, 2026-04-xx.
**Status:** Handled ✓ (`test_end_comment_outside_block_silently_ignored`)

---

## EC-002 — Two elided amounts in one transaction block

**Trigger:** A transaction has two postings with no amount (no `  £X.XX` suffix).
**Expected behaviour:** Raises `ParseError` with message containing "at most one elided amount".
**Source:** hledger spec — only one posting per block may have its amount inferred.
**Status:** Handled ✓ (`test_two_elided_raises`)

---

## EC-003 — Posting line outside a transaction block

**Trigger:** An indented posting-like line appears before any transaction header.
**Expected behaviour:** Raises `ParseError` with message containing "outside a transaction block".
**Note:** Non-indented lines outside a block are silently skipped; only indented lines trigger the error.
**Status:** Handled ✓ (`test_posting_outside_block_raises`)

---

## EC-004 — Year-omitted date with no `default_year`

**Trigger:** A date like `1/31` or `03-15` is parsed without passing `default_year` to `parse_string`.
**Expected behaviour:** The current calendar year (`datetime.date.today().year`) is used.
**Source:** hledger simple-date spec.
**Status:** Handled ✓ (`test_year_omitted_defaults_to_current_year`)

---

## EC-005 — Unclosed block comment runs to end of file

**Trigger:** A `comment` directive with no matching `end comment` before EOF.
**Expected behaviour:** All content after `comment` is silently consumed. No error raised.
**Source:** hledger spec — unclosed comment blocks are not an error.
**Status:** Handled ✓ (`test_unclosed_block_comment_runs_to_eof`)

---

## EC-006 — `include` glob matches no files

**Trigger:** `include *.journal` in a directory with no `.journal` files.
**Expected behaviour:** Silently produces no entries (no error).
**Note:** Contrasted with explicit non-glob paths, which raise `FileNotFoundError` if missing.
**Status:** Handled ✓ (loader.py glob branch)

---

## EC-007 — Circular `include` detection

**Trigger:** File A includes File B which includes File A (directly or transitively).
**Expected behaviour:** `ParseError` raised identifying the circular reference. Does not infinite-loop.
**Status:** Handled ✓ (loader.py `seen` set)

---

## EC-008 — `decimal-mark ,` followed by period-decimal amount

**Trigger:** After `decimal-mark ,`, a posting uses period as decimal separator (e.g. `£30.00`).
**Expected behaviour:** `ParseError` — the amount does not match the active `_AMOUNT_COMMA` pattern.
**Note:** The directive switches the parser mode for all subsequent postings; mixing formats in one file is invalid.
**Status:** Handled ✓ (parser rejects non-matching amounts)

---

## EC-009 — `P` directive with inline `;` or `#` comment

**Trigger:** `P 2024-01-01 € $1.35  ; ECB rate` or `P 2024-01-01 € $1.35  # ECB rate`.
**Expected behaviour:** Comment stripped; price parsed as `$1.35`.
**Status:** Handled ✓ (`test_p_directive_semicolon_comment_stripped`, `test_p_directive_hash_comment_stripped`)

---

## EC-010 — Thousands-separator comma in amount

**Trigger:** Posting amount written as `£1,234.56`.
**Expected behaviour:** Parsed as `Decimal("1234.56")` with commodity `"£"`.
**Note:** The comma is a thousands separator, not a decimal mark. Only valid in default (period-decimal) mode.
**Status:** Handled ✓ (`test_thousands_comma`)

---

## EC-011 — `account` / `payee` / `commodity` directives with trailing `;` or `#` comments

**Trigger:** `account assets:bank  ; checking` or `commodity $  # US dollar`.
**Expected behaviour:** Comment stripped; only the account/payee/commodity name stored.
**Status:** Handled ✓ (all directive handlers call `_strip_directive_comment`)

---

## EC-012 — Two consecutive transactions with identical date and description in `register`

**Trigger:** Two separate transactions share the same `date` and `description` (e.g., two
salary postings on the same day with the same payee string).
**Expected behaviour (hledger):** Each transaction starts a new block in the register view;
the second transaction's first posting shows the date and description.
**Actual behaviour (PyLedger CLI):** The continuation-row detection key is `(date, description)`,
so the second transaction's first posting is silently treated as a continuation row of the
first — the date and description are blanked.
**Status:** Known limitation — not handled. The `RegisterRow` dataclass does not carry a
transaction identity field, so the CLI cannot distinguish the boundary without a deeper change.
**Workaround:** None currently. A future fix would either add a transaction ID/index to
`RegisterRow`, or pass grouped rows from `register()`.
**Source:** Identified during register CLI formatting work, 2026-05-02.
