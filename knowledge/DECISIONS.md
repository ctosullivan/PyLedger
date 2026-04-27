# Decisions

Non-obvious judgment calls made during development. Each entry explains what was chosen, why, and what was rejected.

---

## 2026-04-15 — Parser silently accepts unbalanced transactions

**Decision:** `parse_string` does not validate that postings sum to zero. Unbalanced transactions are stored as-is and only rejected later by `checks.py`.

**Why:** The parser's job is to produce a structural model from text. Balance validation is a semantic check that belongs at the reports/checks layer, where the caller can decide whether to enforce it.

**Rejected alternative:** Raising `ParseError` in the parser when postings don't balance.

**Applies to:** `PyLedger/parser.py`, `PyLedger/checks.py`

---

## 2026-04-15 — Posting indentation is conventional, not required

**Decision:** The parser does not enforce 2-space or tab indentation on posting lines. Any non-header line inside an open transaction block is treated as a posting.

**Why:** hledger 1.52 documents indentation as conventional. Enforcing it would reject valid journals and contradict the compatibility spec.

**Rejected alternative:** Strict `line.startswith("  ") or line.startswith("\t")` gate (was the original implementation; removed).

**Applies to:** `PyLedger/parser.py`, `dev-docs/hledger-compatibility.md`

---

## 2026-04-17 — Only `.journal` and `.ledger` file formats supported

**Decision:** `load_journal()` and the `include` directive only accept `.journal` and `.ledger` extensions. All other hledger format families (`.csv`, `.timeclock`, `.timedot`, `.rules`, `.prices`, `.ledger-json`) raise `ParseError`.

**Why:** The other formats require fundamentally different parsers. Supporting them is a future milestone, not v1.

**Rejected alternative:** Silently ignoring unsupported formats or accepting any extension.

**Applies to:** `PyLedger/loader.py`, `dev-docs/hledger-compatibility.md`

---

## 2026-04-17 — File I/O extracted to `loader.py`; `parser.py` is pure text-only

**Decision:** `parse_file()` was removed from `parser.py`. All file reading, include resolution, and glob expansion live in `loader.py`. `parse_string()` is the only public entry point in `parser.py`.

**Why:** Separates concerns cleanly. The parser is a pure function (text → Journal); the loader handles I/O, paths, and multi-file merging. Easier to test each in isolation.

**Rejected alternative:** Keeping `parse_file()` in `parser.py` alongside `parse_string()`.

**Applies to:** `PyLedger/parser.py`, `PyLedger/loader.py`

---

## 2026-04-xx — `alias` directive is file-scoped at parse time

**Decision:** Aliases apply to account names within the file they are declared in, processing them at parse time. They are not propagated to including files.

**Why:** Matches hledger 1.52 semantics. Applying aliases globally would cause surprising account rewrites in unrelated included files.

**Rejected alternative:** Accumulating aliases across all included files and applying them in a post-processing pass.

**Applies to:** `PyLedger/parser.py`, `dev-docs/hledger-compatibility.md`

---

## 2026-04-xx — `decimal-mark` directive only applies forward, not retroactively

**Decision:** A `decimal-mark` directive only affects amount parsing for postings that appear *after* it in the file. Postings before the directive use the previous decimal mark (default: period).

**Why:** This matches hledger's streaming-parse model. Retroactive application would require a two-pass parser.

**Rejected alternative:** Applying the decimal mark to all transactions in the file regardless of position.

**Applies to:** `PyLedger/parser.py`

---

## 2026-04-27 — `assert amt is not None` over `self.assertIsNotNone()` for type narrowing

**Decision:** In tests, bare `assert x is not None` is used (not `self.assertIsNotNone(x)`) immediately after extracting a `Posting.amount` field.

**Why:** Pylance recognises bare `assert` as a type-narrowing guard and eliminates `reportOptionalMemberAccess` warnings. `self.assertIsNotNone()` does not narrow the type in Pylance's analysis.

**Rejected alternatives:** `cast()`, `# type: ignore`, `if x is None: self.fail(...)`.

**Applies to:** `tests/test_parser/test_parser.py`, `tests/test_directives/test_directives.py`

---

## 2026-04-27 — Minor version bump (0.2.0) for new milestone

**Decision:** Version bumped from `0.1.2` → `0.2.0` when starting Milestone 2.

**Why:** Minor version increments mark the start of a new milestone (new user-visible feature area). Patch versions are used for fixes and admin changes within a milestone.

**Rejected alternative:** Continuing to bump patch version (0.1.3, 0.1.4, …) indefinitely.

**Applies to:** `PyLedger/__init__.py`, `pyproject.toml`

---

## 2026-04-27 — Test subdirectories require `__init__.py`

**Decision:** Every test subdirectory (`test_parser/`, `test_directives/`, etc.) has an explicit `__init__.py`.

**Why:** Python 3.13's `unittest discover` silently skips namespace-package subdirectories (those without `__init__.py`). Without the file the tests are simply not found, with no warning.

**Rejected alternative:** Using namespace packages (no `__init__.py`).

**Applies to:** `tests/` subdirectories
