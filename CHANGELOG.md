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

### [0.1.0-dev.0] — Project scaffold + rename to PyLedger

**What changed:**
- Initial project structure created: `CLAUDE.md`, `README.md`, `pyproject.toml`,
  `docs/` (architecture, api-spec, hledger-compatibility, SYNC), `tests/`
  (fixtures, README), `pyLedger/` (models, parser stub, reports stub, cli stub)
- Project renamed from `hledger-python` → `PyLedger`; package folder renamed
  `hledger/` → `pyLedger/`; CLI command renamed `hledger-py` → `pyLedger`;
  all internal references updated
- `.gitignore` added covering secrets/credentials, Python build artefacts,
  virtual environments, IDEs, and private `.journal` files

**Human:** Defined the full project brief: module structure, CLAUDE.md contract
rules (doc-sync, unauthorised-change, testing, code style, hledger compatibility),
and directed the rename to PyLedger.

**Claude:** Generated all scaffold files, wrote the initial docs, implemented
the data models (`Amount`, `Posting`, `Transaction`, `Journal`), created CLI
argument parsing and the `print` command stub, authored the `.gitignore`, and
applied all rename changes across every file and import.

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

1. **Create an archive file** at `docs/changelog/MILESTONE-N.md` (e.g.
   `docs/changelog/MILESTONE-1.md`), using this structure:

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

Full detail: [docs/changelog/MILESTONE-N.md](docs/changelog/MILESTONE-N.md)

**Summary:** One or two sentences describing what the milestone delivered.
```

3. **Update `ROADMAP.md`** to mark the milestone `[DONE]` if not already done.

This keeps `CHANGELOG.md` scannable as the project grows while preserving the
full per-commit history in the archive files.
