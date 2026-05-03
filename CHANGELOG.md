# Changelog

All notable changes to PyLedger are recorded here.

Each entry corresponds to one GitHub commit. The **Human** line summarises what
the user directed or decided; the **Claude** line summarises what Claude
researched, designed, or implemented.

Format loosely follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased]

---

### [Unreleased] — feat: Milestone 3 — lenient parser, multi-commodity balance, tree mode, CheckError.line_number

**Human:** Implement Milestone 3: add `parse_string_lenient` for on-keystroke live parsing, add `CheckError.line_number` for clickable editor diagnostics, fix multi-commodity elision (one elided posting now generates N postings for N commodities), and change `balance()` to return `dict[str, dict[str, Decimal]]` with an optional `tree=True` mode returning `list[BalanceRow]`.

**Claude:** Added `Posting.inferred` field and `BalanceRow` dataclass to `models.py`. Added public `resolve_elision()` to `parser.py` that handles the N-commodity elided posting case; refactored parser body into `_parse_string_impl` with `skip_until_blank` error-recovery state; added `parse_string_lenient()` that never raises. Added `line_number: int | None = None` to `CheckError` and propagated it in all six check functions; removed the multi-commodity ambiguity error from `_check_txn_balanced` (one elided posting is always valid regardless of commodity count). Replaced `_infer_elided_posting_amount` with `resolve_elision()` in `reports.py`; updated `balance()` to return per-commodity nested dict and added `_build_balance_tree()` helper; updated `register()` and `balance_from_spec()`. Updated `cli.py` balance display to hledger-style: account name only on the last commodity line per account, negative amounts in ANSI red. Re-exported `BalanceRow`, `parse_string_lenient`, `resolve_elision` from `__init__.py`; bumped `__version__` to `"0.4.0"`. Added `tests/fixtures/multicommodity.journal`, `TestResolveElision` (11 tests), `TestParseStringLenient` (10 tests), `TestCheckErrorLineNumber` (6 tests), `TestBalanceMultiCommodity` (15 tests). Updated all existing balance assertions for the new nested-dict return type.

---

### [Unreleased] — chore: release v0.3.0 and mark Milestone 2 done

**Human:** Mark Milestone 2 complete, archive its changelog entries, include limited multi-commodity support in Milestone 3 scope, bump version to 0.3.0.
**Claude:** Created `dev-docs/changelog/MILESTONE-2.md` with all five Milestone 2 commits (oldest first). Replaced those entries in `CHANGELOG.md` with a summary link. Marked Milestone 2 `[DONE]` in `ROADMAP.md`; added limited multi-commodity support to Milestone 3 candidate scope. Bumped `__version__` and `pyproject.toml` from `0.2.1` to `0.3.0`.

---

### [Milestone 2 — Core Reports] — 2026-05-03

Full detail: [dev-docs/changelog/MILESTONE-2.md](dev-docs/changelog/MILESTONE-2.md)

**Summary:** Implemented the `Query` filter dataclass, all four report functions (`balance`, `register`, `accounts`, `stats`), `ReportSpec`/`ReportSection`/`ReportSectionResult` foundation, hledger-aligned CLI output for `balance` and `register`, full balance assertions (`=`, `==`, `=*`, `==*`) with automatic enforcement and `-I` flag, a project knowledge base, and a trailing-decimal amount fix. 363 tests across seven test modules.

---

### [Milestone 1 — Journal Parser] — 2026-04-26

Full detail: [dev-docs/changelog/MILESTONE-1.md](dev-docs/changelog/MILESTONE-1.md)

**Summary:** Implemented the full journal parser (`parse_string`, `load_journal`, `include` directive, all key hledger directives), the checks module with strict mode, the `stats` report, all five CLI commands, and the complete test suite (265 tests across six subdirectory modules).

---

### [Milestone 0 — Project Foundation] — 2026-04-15

Full detail: [dev-docs/changelog/MILESTONE-0.md](dev-docs/changelog/MILESTONE-0.md)

**Summary:** Established the full project scaffold, core data models, initial
documentation suite, and developer tooling conventions that all subsequent
milestones build on.

---

## How to add a changelog entry

When work is ready to commit, add a new entry at the top of the `[Unreleased]`
section following this template:

```markdown
### [0.x.y-dev.N] — Short title

**What changed:**
- Bullet list of files/modules affected and what changed in each

**Human:** One or two sentences on what the user directed, decided, or specified.

**Claude:** One or two sentences on what Claude researched, designed, or implemented.
```

Once the GitHub commit is made, move the entry out of `[Unreleased]` and
replace the dev tag with the actual commit hash or release version:

```markdown
## [abc1234] — 2026-04-14 — Short title
```

---

## Archiving at milestone completion

When a major milestone is marked `[DONE]` in `ROADMAP.md`, all `[Unreleased]`
entries that belong to that milestone are archived as follows:

1. **Create an archive file** at `dev-docs/changelog/MILESTONE-N.md` (e.g.
   `dev-docs/changelog/MILESTONE-1.md`), using this structure:

```markdown
# Changelog — Milestone N: <Milestone Title>

Archived on: YYYY-MM-DD
GitHub commits: <hash> … <hash>

<paste all dev entries that belong to this milestone, oldest first>
```

2. **Replace** the individual dev entries in `CHANGELOG.md` with a single
   summary entry pointing to the archive:

```markdown
### [Milestone N — <Title>] — YYYY-MM-DD

Full detail: [dev-docs/changelog/MILESTONE-N.md](dev-docs/changelog/MILESTONE-N.md)

**Summary:** One or two sentences describing what the milestone delivered.
```

3. **Update `ROADMAP.md`** to mark the milestone `[DONE]` if not already done.

This keeps `CHANGELOG.md` scannable as the project grows while preserving the
full per-commit history in the archive files.
