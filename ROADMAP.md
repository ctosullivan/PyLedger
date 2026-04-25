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
- Initial documentation: `dev-docs/architecture.md`, `dev-docs/api-spec.md`,
  `dev-docs/hledger-compatibility.md`, `dev-docs/SYNC.md`
- Developer tooling: `.gitignore`, test conventions (`tests/README.md`),
  sample fixture (`tests/fixtures/sample.journal`)

**Exit criteria:** All models importable; `python -m unittest tests.test_parser -v` runs
with no errors (empty suite passes).

---

## Milestone 1 — Journal Parser `[IN PROGRESS]`

Implement a working parser so that `.journal` files can be loaded into memory as
`Journal` objects, including key hledger directives.

**Scope:**
- `parse_string(text) -> Journal` — pure text parser ✅
- `load_journal(path) -> Journal` — file loader with include support (in `loader.py`) ✅
- `ParseError` with line-number context ✅
- Transaction header parsing (date, flag, code, description, comment) ✅
- Posting parsing (prefix/suffix commodity, thousands separator, elided amount,
  double-space separator rule) ✅
- Simple date formats: all three separators (`-`, `/`, `.`), optional leading
  zeros, year-omitted with inference ✅
- Block comments (`comment` / `end comment` directive) ✅
- **P directive** (`P DATE COMMODITY PRICE`) — market price declarations stored
  in `Journal.prices` as `PriceDirective` objects ✅
- **alias directive** (`alias OLD=NEW` / `alias /REGEX/=REPLACEMENT` /
  `end aliases`) — account names rewritten at parse time within the current file ✅
- **include directive** (`include other.journal`) — embeds entries and directives
  from another `.journal` or `.ledger` file inline; relative, absolute, tilde,
  and glob paths supported; circular include detection; format-prefix rejection ✅
- Module-level API: `Journal` report methods (`.balance()`, `.register()`,
  `.accounts()`, `.stats()`); `PyLedger.load()` convenience function;
  `python -m PyLedger` entry point ✅
- Regex documentation rule enforced on all patterns ✅
- `dev-docs/hledger-compatibility.md` updated with transaction block structure,
  P directive, alias directive, and include directive ✅

**Exit criteria:**
- `python -m unittest tests.test_parser tests.test_reports tests.test_loader -v` — all tests pass ✅
- `python -m PyLedger print tests/fixtures/sample.journal` outputs all
  5 transactions correctly ✅
- P directives parsed and stored in `journal.prices` ✅
- Account aliases applied correctly against a fixture covering both simple and
  regex alias forms ✅
- `include` directive resolves relative, absolute, tilde, and glob paths;
  included file entries appear in the resulting `Journal` as if written inline ✅

---

## Milestone 2 — Core Reports `[PLANNED]`

> **Scope to be confirmed by user before implementation begins.**

Implement the four report functions so that all CLI commands produce output.

**Candidate scope:**
- `accounts(journal) -> list[str]`
- `balance(journal, accounts=None) -> dict[str, Decimal]`
- `stats(journal) -> JournalStats`
- `register(journal, accounts=None) -> list[RegisterRow]`
- Commodity valuation using `Journal.prices` — convert/value amounts in reports
  using P directive data; scope behaviour (file-local vs propagated via
  `include`) to be confirmed at implementation
- Unit tests for each report (`tests/test_reports.py`)
- `dev-docs/api-spec.md` updated to mark each function `[IMPLEMENTED]`
- `docs/` human guides updated with real command output examples

**Exit criteria:** All five CLI commands (`balance`, `register`, `accounts`,
`print`, `stats`) produce correct output against `sample.journal`.

---

## Milestone 3 — First Release `[BACKLOG]`

> **Scope to be confirmed by user.**

Package the project for distribution and establish a baseline release.

**Candidate scope (to confirm):**
- `pip install -e .` installs cleanly; `PyLedger --help` works
- Version pinned in `__init__.py` and `pyproject.toml`
- `README.md` and `docs/` updated with real usage examples
- Changelog entry for `v0.1.0`

---

## Future / Backlog `[BACKLOG]`

Items not scheduled for a milestone yet. Promote to a milestone when prioritised.

| Item | Notes |
|---|---|
| Strict mode (balance validation) | Parser accepts unbalanced transactions; reports could flag them |
| Multiple commodities per journal | Currently assumed single-commodity per transaction |
| Account type inference | Infer assets/liabilities/income/expenses from name prefix |
| Periodic/auto postings | Out of scope for v1 |
| Secondary dates | `2024-01-15=2024-01-20` |
| `stats`: peak live memory (`X MB live`) | Requires `psutil` (third-party) or platform-specific syscall; not in scope without user approval of the dependency |
| `stats`: peak allocated memory (`X MB alloc`) | Implementable via stdlib `tracemalloc`; deferred to keep scope small |
| `stats`: per-reporting-interval output | Show stats broken down by week/month/year; needs date-interval logic |

---

## Deciding What Goes Into a Milestone

Before starting a new milestone, the user specifies the scope. Claude then:
1. Confirms the scope against `dev-docs/hledger-compatibility.md` (supported features only)
2. Updates this file to move the milestone from `[PLANNED]` to `[IN PROGRESS]`
3. Implements, tests, and updates docs in the same response
4. Updates this file to `[DONE]` **only when the user explicitly confirms the
   milestone is complete**, and adds a `CHANGELOG.md` entry at that point
