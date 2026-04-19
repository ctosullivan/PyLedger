# Changelog

All notable changes to PyLedger are recorded here.

Each entry corresponds to one GitHub commit. The **Human** line summarises what
the user directed or decided; the **Claude** line summarises what Claude
researched, designed, or implemented.

Format loosely follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased]

> The entries below represent work completed locally that has not yet been
> committed to GitHub. They will each become a separate commit.

---

### [Unreleased] — chore: switch to stable setuptools build backend

**Human:** Update `pyproject.toml` to use `setuptools.build_meta` and drop the version pin on `setuptools`.
**Claude:** Replaced `setuptools.backends.legacy:build` with `setuptools.build_meta` and changed `requires` from `["setuptools>=68"]` to `["setuptools"]`.

---

### [Unreleased] — Project: add CONTRIBUTING.md and CODE_OF_CONDUCT.md

**What changed:**
- `CONTRIBUTING.md` added at project root (moved from `PyLedger/` subfolder);
  title corrected from "hledger-textual" to "PyLedger"; test command updated
  from `uv run pytest` to `python -m unittest tests.test_parser -v`
- `CODE_OF_CONDUCT.md` added at project root (moved from `PyLedger/` subfolder)
- `README.md` — Contributing section updated with brief reference to
  `CONTRIBUTING.md` and `CODE_OF_CONDUCT.md`
- `CLAUDE.md` — Commit Message Format subsection added under Changelog & Roadmap
  Rules; specifies Conventional Commits standard with types, imperative mood,
  72-char limit, no trailing period, blank line + body for complex changes

**Human:** Added `CONTRIBUTING.md` and `CODE_OF_CONDUCT.md`; directed that
contribution guidelines should be referenced briefly in README and that Claude
should follow the commit message format defined in CONTRIBUTING.md.

**Claude:** Moved both files to project root; corrected project name and test
command in CONTRIBUTING.md; updated README.md Contributing section; added commit
message format rule to CLAUDE.md.

---

### [Unreleased] — Docs: correct P directive scope description

**What changed:**
- `docs/journal-format.md` — P directive section rewritten: removed incorrect
  "global" scope claim; added explanation of `journal.prices` (a list of
  `PriceDirective` objects, one per directive, in file order, each recording
  date, commodity, and price amount); removed milestone language from human doc
- `dev-docs/hledger-compatibility.md` — P directive notes updated: "global"
  removed; scope behaviour (file-local vs propagated via `include`) documented
  as TBD at implementation; commodity valuation noted as in-scope for Milestone 2
- `dev-docs/api-spec.md` — `PriceDirective` section updated: note added that
  commodity valuation is in scope for v1 (Milestone 2)
- `ROADMAP.md` — Milestone 2 candidate scope updated: commodity valuation using
  `Journal.prices` added as an explicit line item

**Human:** Identified that the P directive docs incorrectly stated "global
(apply to all entries in the file)"; clarified that P directives declare a
commodity price at a point in time, that `journal.prices` should be explained
to human readers, and that commodity valuation is in scope for v1.

**Claude:** Updated all four files; removed "global" claim; explained
`journal.prices` in human docs; moved commodity valuation into Milestone 2
candidate scope in the roadmap.

---

### [Unreleased] — Scope: add `include` directive to Milestone 1

**What changed:**
- `dev-docs/hledger-compatibility.md` — `include` directive moved from Out of
  Scope → **In Scope (v1)** Directives table; behaviour documented (inline
  embedding, parent-directive propagation, `.journal`/`.ledger` targets only,
  `ParseError` on unsupported extension); removed from "Directives" catch-all
  Out of Scope row
- `ROADMAP.md` — `include` directive added to Milestone 1 scope block and exit
  criteria; removed from Future/Backlog table

**Human:** Directed that the `include` directive is in scope for v1, referencing
the hledger 1.52 specification.

**Claude:** Fetched the hledger 1.52 `include` directive spec, updated the
compatibility doc and roadmap accordingly.

---

### [a2d68b3] — 2026-04-17 — Structural updates: docs split, packaging, module API, roadmap

**What changed:**
- `docs/` renamed → `dev-docs/` (git mv; all cross-references updated)
- `dev-docs/SYNC.md` — stale `hledger/` refs fixed to `PyLedger/`; human-docs
  sync rule added
- `dev-docs/api-spec.md` — all `pyLedger/` refs → `PyLedger/`; `Journal` report
  methods, `load()`, `PriceDirective`, and `python -m PyLedger` usage added
- `dev-docs/hledger-compatibility.md` — P directive and alias directive moved
  from Undecided/Out of Scope → **In Scope (v1)**; Directives table added
- `CLAUDE.md` — all `docs/` refs → `dev-docs/`; folder diagram corrected
  (`pyLedger/` → `PyLedger/`, `MANIFEST.in` and `__main__.py` added, `docs/`
  human section added); SYNC table updated; milestone archive path updated
- `README.md` — CLI command updated to `PyLedger`; Python library example added;
  docs table added; Contributing section with sparse-checkout command added
- `ROADMAP.md` — all `docs/` refs → `dev-docs/`; Milestone 1 scope extended with
  P directive, alias directive, and module-level API; `pyLedger.cli` → `PyLedger`;
  Commodity price directives removed from backlog (now in Milestone 1)
- `pyproject.toml` — script entry `pyLedger = "pyLedger.cli:main"` →
  `PyLedger = "PyLedger.cli:main"`; `include = ["pyLedger*"]` → `["PyLedger*"]`
- `MANIFEST.in` — new file; excludes `CLAUDE.md`, `CHANGELOG.md`, `ROADMAP.md`,
  `dev-docs/` from sdist
- `PyLedger/models.py` — `PriceDirective` dataclass added; `Journal.prices` field
  added; four report methods added to `Journal` (lazy-import delegation to reports)
- `PyLedger/__init__.py` — `load()` convenience function exported
- `PyLedger/__main__.py` — new file; enables `python -m PyLedger`
- `PyLedger/cli.py` — `prog="pyLedger"` → `prog="PyLedger"`
- `docs/` — new human-facing documentation folder created with four guides:
  `getting-started.md`, `usage.md`, `journal-format.md`, `python-api.md`

**Human:** Directed the structural refactor: rename `docs/` to `dev-docs/`,
create a human `docs/` folder, add sparse-checkout clone command, fix packaging
capitalisation, add `load()` + `__main__` + Journal report methods, extend
Milestone 1 to include P directive and alias directive.

**Claude:** Executed the full plan across 18 files: git mv for the folder rename,
updated all cross-references, created `MANIFEST.in`, added `PriceDirective` and
Journal methods with lazy-import pattern, created `__main__.py`, and authored all
four human guide files.

---

### [17207ce] — 2026-04-15 — Fix: normalise internal imports to PyLedger (capital P)

**What changed:**
- `PyLedger/parser.py` — `from pyLedger.models import` → `from PyLedger.models import`
- `PyLedger/reports.py` — `from pyLedger.models import` → `from PyLedger.models import`
- `PyLedger/cli.py` — all three `pyLedger` references updated to `PyLedger`
- `PyLedger/parser.py` — posting-outside-block guard restored: indented lines
  outside a transaction block still raise `ParseError`; non-indented lines outside
  a block are silently skipped

**Human:** Directed that all internal imports be normalised to `PyLedger`
(capital P) to match the package directory name and resolve the
`ModuleNotFoundError` that prevented the test suite from running.

**Claude:** Updated all cross-module imports in the three affected files, ran the
suite (36 tests), diagnosed one regression in `test_posting_outside_block_raises`
caused by the indentation relaxation, restored the guard for indented lines
outside a block, and confirmed 36/36 pass.

---

### [0.1.0-dev.10] — Fix: relax posting-line indentation requirement

**What changed:**
- `pyLedger/parser.py` — state machine restructured: transaction-header and
  directive checks now run before posting detection; posting branch changed from
  `line.startswith("  ") or line.startswith("\t")` to `current_txn is not None`,
  making indentation conventional rather than mandatory; `parse_string` docstring
  updated to document the relaxed rule; posting-branch inline comment updated
- `docs/hledger-compatibility.md` — first delimiter rule updated (user-applied):
  posting indentation noted as conventional, not required

**Human:** Identified that the strict 2+ space / tab gate in `parse_string`
contradicted the updated compatibility doc stating indentation is not a
requirement; directed the parser to be updated to match.

**Claude:** Restructured the state-machine branch order so that transaction-header
and directive checks run first, then any unmatched line inside an open block is
treated as a posting regardless of indentation.

---

### [11c35f8] — 2026-04-15 — Process: milestone archiving rule + Milestone 0 archive

**What changed:**
- `CLAUDE.md` — "Changelog & Roadmap Rules" bullet updated: milestones may only
  be marked `[DONE]` when the user explicitly states completion; "Milestone
  archiving" heading clarified to match
- `ROADMAP.md` — "Deciding What Goes Into a Milestone" step 4 updated with the
  same explicit-user-approval requirement
- `dev-docs/changelog/MILESTONE-0.md` — created; contains the `[0.1.0-dev.0]`
  scaffold entry (oldest first), archive date, and commit placeholder
- `CHANGELOG.md` — `[0.1.0-dev.0]` replaced with a single summary line linking
  to the archive file

**Human:** Directed that milestones should only be marked complete when
explicitly specified by the user; confirmed Milestone 0 is complete and directed
execution of the archiving procedure.

**Claude:** Updated the rule in `CLAUDE.md` and `ROADMAP.md`, created
`dev-docs/changelog/` and `MILESTONE-0.md`, and replaced the dev.0 entry with a
summary link.

---

### [0.1.0-dev.8] — Docs: MIT License and acknowledgements

**What changed:**
- `LICENSE` — MIT License added; Acknowledgements section credits John Wiegley
  and the Ledger project (https://github.com/ledger/ledger) and Simon Michael
  and hledger contributors (https://github.com/simonmichael/hledger), with a
  pointer to the full hledger CREDITS file

**Human:** Directed that an MIT License be added with acknowledgements to the
Ledger project / John Wiegley and the hledger project / Simon Michael and
contributors. Human subsequently manually copied acknowledgements to Readme.md

**Claude:** Created `LICENSE` with standard MIT terms and a plain-English
Acknowledgements section naming both upstream projects and linking to the
hledger CREDITS page.

---

### [0.1.0-dev.7] — Feature: block comments + comment coverage audit

**What changed:**
- `pyLedger/parser.py` — `in_block_comment` state variable added to
  `parse_string`; `comment` directive detected before the silent-skip
  fallthrough and enters block-comment mode (flushing any open transaction);
  all lines in block-comment mode are consumed until `end comment` or EOF;
  whole-line comment branch comment updated to document that it also catches
  indented follow-on `;` lines via `lstrip()`
- `docs/hledger-compatibility.md` — Comments table expanded from 3 to 6 rows
  covering all implemented comment types (whole-line `;`, whole-line `#`,
  inline `;` on transaction, inline `;` on posting, follow-on indented `;`,
  block comment); "Other syntax" added to Undecided/Future
- `tests/test_parser.py` — 5 new assertions in `TestBlockComments`: block
  between transactions, block at file start, unclosed block runs to EOF,
  follow-on comment lines skipped, `end comment` outside block silently ignored

**Human:** Requested full implementation of the hledger 1.52 comments spec;
specified that "Other syntax" features remain undecided.

**Claude:** Fetched the hledger 1.52 comments spec, audited existing parser
coverage (whole-line, inline, and follow-on comments already handled), identified
block comments as the sole gap, implemented and tested the `comment`/`end comment`
state machine, and updated docs accordingly.

---

### [0.1.0-dev.6] — Feature: simple date formats

**What changed:**
- `pyLedger/parser.py` — `_TXN_HEADER` date group broadened to capture all
  simple date variants; new `_SIMPLE_DATE` regex added with full group/edge-case
  comments; new `_parse_simple_date()` helper handles year inference; transaction
  header detection updated to match year-omitted dates; `parse_string` gains an
  optional `default_year` parameter (defaults to current calendar year)
- `docs/hledger-compatibility.md` — "Simple date" row updated to show all
  accepted formats; "Date formats" row removed from Out of Scope; "Smart dates"
  added to Undecided/Future
- `docs/api-spec.md` — `parse_string` signature and docstring updated with new
  `default_year` parameter and accepted date format descriptions
- `tests/test_parser.py` — 8 new assertions covering hyphen/slash/dot separators,
  optional leading zeros, year-omitted with explicit and default year, and
  invalid calendar date rejection

**Human:** Specified the full hledger simple dates spec (three separators,
optional leading zeros, optional year with inference rules), provided the
hledger 1.52 reference URL, and noted smart dates as undecided.

**Claude:** Redesigned the date-capture regex and parsing pipeline, implemented
year inference via `default_year`, updated all affected docs and the test suite.

---

### [0.1.0-dev.5] — Docs & spec: supported file formats

**What changed:**
- `docs/hledger-compatibility.md` — new "Supported File Formats" section
  documenting the `.journal` and `.ledger` extensions as the only accepted
  formats; full deviation table listing all seven hledger 1.52 format families
  and PyLedger's stance on each (with reference to the hledger 1.52 spec)
- `docs/api-spec.md` — `parse_file` docstring updated to state supported
  extensions and new `ParseError` condition for unsupported extensions;
  `Journal.source_file` comment updated accordingly
- `CLAUDE.md` — "Format target" updated to list both supported extensions
- `pyLedger/parser.py` — `_SUPPORTED_EXTENSIONS` constant added; `parse_file`
  extended with an extension check that raises `ParseError` for unsupported
  formats (`.csv`, `.timeclock`, `.j`, etc.)
- `tests/test_parser.py` — 5 new assertions (3 unsupported extension cases,
  2 accepted extension cases including a `.ledger` tempfile round-trip)

**Human:** Specified that PyLedger should support `.journal` and `.ledger` only,
identified this as a deliberate deviation from hledger 1.52, and provided the
hledger 1.52 data-formats reference URL for the full format list.

**Claude:** Fetched and parsed the hledger 1.52 data-formats page to compile
the complete format matrix, applied doc updates across four files, implemented
the extension guard in `parse_file`, and added tests for all new behaviour.

---

### [0.1.0-dev.4] — Docs: mandatory double-space posting separator

**What changed:**
- `docs/hledger-compatibility.md` — posting table row and block-structure rules
  updated to state that two or more spaces between account name and amount is
  mandatory, not optional formatting
- `docs/api-spec.md` — `Posting` section now explains the separator rule and
  why single spaces are preserved (account names containing spaces)

**Human:** Identified that the double-space separator rule was not explicitly
documented as a hard requirement in the compatibility spec or API docs, and
directed the update.

**Claude:** Located the three affected passages across two doc files, applied
the wording changes, and verified no code changes were needed (the parser
already implements the rule via `re.split(r"\s{2,}", ...)`).

---

### [0.1.0-dev.3] — Docs & style: regex documentation rule

**What changed:**
- `CLAUDE.md` — new "Regex Documentation Rule" in the Code Style section:
  every regex must be accompanied by a multiline comment covering purpose,
  group breakdown, and edge cases
- `pyLedger/parser.py` — all four regexes (`_TXN_HEADER`, `_AMOUNT`, the
  date-check `re.match`, and the posting-split `re.split`) updated with full
  explanatory comments per the new rule

**Human:** Directed that all regexes must carry detailed explanatory comments
for debugging; specified the three required comment sections (purpose, groups,
edge cases).

**Claude:** Drafted the rule, wrote the worked example in `CLAUDE.md`, and
applied the rule retroactively to all existing regexes in `parser.py`.

---

### [0.1.0-dev.2] — Docs: transaction block structure

**What changed:**
- `docs/hledger-compatibility.md` — new "Transaction Block Structure" section
  with annotated diagram, fixed field-order rule, and delimiter rules
- `docs/api-spec.md` — models (`Amount`, `Posting`, `Transaction`, `Journal`,
  `ParseError`, `parse_string`, `parse_file`) marked `[IMPLEMENTED]`; wire→model
  mapping diagram added to `Transaction` section

**Human:** Requested that the docs be updated to make the transaction block
format (begin/end delimiters, optional field ordering) explicit before any
parser implementation, to serve as the canonical format reference.

**Claude:** Designed the annotated diagram and delimiter rule wording, applied
the `[IMPLEMENTED]` status updates, and wrote the wire→model mapping.

---

### [0.1.0-dev.1] — Feature: journal parser + tests

**What changed:**
- `pyLedger/parser.py` — `parse_string` and `parse_file` implemented;
  private helpers `_parse_txn_header`, `_parse_amount`, `_parse_posting` added
- `tests/test_parser.py` — created with 18 assertions across 10 test classes
  (happy paths: date/description/flag/code/comment/commodity/thousands;
  error paths: posting outside block, two elided amounts)

**Human:** Specified the required test cases, the at-most-one-elided-amount
rule, and the decision to accept unbalanced transactions silently in the parser
(deferred to reports layer).

**Claude:** Designed the line-by-line state machine, wrote the regex patterns,
implemented all helpers, and authored the test file.

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
