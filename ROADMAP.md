# PyLedger Roadmap

Milestones track the planned development path. Each milestone corresponds to one
or more GitHub commits and should leave the codebase in a releasable, tested state.

**Status key:** `[DONE]` · `[IN PROGRESS]` · `[PLANNED]` · `[BACKLOG]`

---

## Milestone 0 — Project Foundation `[DONE]`

Establish the project structure, tooling contracts, and data models so that all
subsequent work has a clean, documented base to build on.

**Scope:**
- Project scaffold: folder structure, `pyproject.toml`, `CLAUDE.md` rules
- Core data models: `Amount`, `Posting`, `Transaction`, `Journal`
- Initial documentation: `architecture.md`, `api-spec.md`,
  `hledger-compatibility.md`, `SYNC.md`
- Developer tooling: `.gitignore`, test conventions (`tests/README.md`),
  sample fixture (`tests/fixtures/sample.journal`)

**Exit criteria:** All models importable; `python -m unittest discover tests/` runs
with no errors (empty suite passes).

---

## Milestone 1 — Journal Parser `[IN PROGRESS]`

Implement a working parser so that `.journal` files can be loaded into memory as
`Journal` objects.

**Scope:**
- `parse_string(text) -> Journal` and `parse_file(path) -> Journal`
- `ParseError` with line-number context
- Transaction header parsing (date, flag, code, description, comment)
- Posting parsing (prefix/suffix commodity, thousands separator, elided amount,
  double-space separator rule)
- 18 unit tests covering happy paths and error paths
- Inline regex documentation rule added to `CLAUDE.md`
- `hledger-compatibility.md` updated with transaction block structure diagram

**Exit criteria:** `python -m unittest discover tests/` — 18/18 pass;
`python -m pyLedger.cli print tests/fixtures/sample.journal` outputs all
5 transactions correctly.

---

## Milestone 2 — Core Reports `[PLANNED]`

> **Scope to be confirmed by user before implementation begins.**

Implement the four report functions so that all CLI commands produce output.

**Candidate scope:**
- `accounts(journal) -> list[str]`
- `balance(journal, accounts=None) -> dict[str, Decimal]`
- `stats(journal) -> JournalStats`
- `register(journal, accounts=None) -> list[RegisterRow]`
- Unit tests for each report (`tests/test_reports.py`)
- `api-spec.md` updated to mark each function `[IMPLEMENTED]`

**Exit criteria:** All five CLI commands (`balance`, `register`, `accounts`,
`print`, `stats`) produce correct output against `sample.journal`.

---

## Milestone 3 — First Release `[BACKLOG]`

> **Scope to be confirmed by user.**

Package the project for distribution and establish a baseline release.

**Candidate scope (to confirm):**
- `pip install -e .` installs cleanly; `pyLedger --help` works
- Version pinned in `__init__.py` and `pyproject.toml`
- `README.md` updated with real usage examples
- Changelog entry for `v0.1.0`

---

## Future / Backlog `[BACKLOG]`

Items not scheduled for a milestone yet. Promote to a milestone when prioritised.

| Item | Notes |
|---|---|
| Strict mode (balance validation) | Parser accepts unbalanced transactions; reports could flag them |
| Multiple commodities per journal | Currently assumed single-commodity per transaction |
| Account type inference | Infer assets/liabilities/income/expenses from name prefix |
| Commodity price directives | `P YYYY-MM-DD SYMBOL PRICE` |
| `include` directive | Compose multiple `.journal` files |
| Periodic/auto postings | Out of scope for v1 |
| Date format variants | `YYYY/MM/DD`, secondary dates |

---

## Deciding What Goes Into a Milestone

Before starting a new milestone, the user specifies the scope. Claude then:
1. Confirms the scope against `docs/hledger-compatibility.md` (supported features only)
2. Updates this file to move the milestone from `[PLANNED]` to `[IN PROGRESS]`
3. Implements, tests, and updates docs in the same response
4. Updates this file to `[DONE]` **only when the user explicitly confirms the
   milestone is complete**, and adds a `CHANGELOG.md` entry at that point
