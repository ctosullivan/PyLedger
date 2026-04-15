# Changelog — Milestone 0: Project Foundation

Archived on: 2026-04-15
GitHub commits: pending initial commit

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
