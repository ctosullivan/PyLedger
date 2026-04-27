# Context — 2026-04-27

## Current Task

Starting Milestone 2: implement the three remaining report functions (`accounts`, `balance`, `register`) in `PyLedger/reports.py`.

## Where We Are

All three functions currently raise `NotImplementedError`. The next step is to implement `accounts()` first (simplest — deduplicate account names from all postings), then `balance()` (net sum per account), then `register()` (chronological register rows with running balance).

## Decisions In Flight

None — all session decisions have been logged to `knowledge/DECISIONS.md`.

## Files Currently Relevant

- [PyLedger/reports.py](PyLedger/reports.py) — `accounts()`, `balance()`, `register()` all stub `NotImplementedError`
- [tests/test_reports.py](tests/test_reports.py) — existing `stats()` tests; new report tests go here
- [PyLedger/models.py](PyLedger/models.py) — `Journal`, `Amount`, `Posting`, `Transaction`, `PriceDirective`
- [dev-docs/api-spec.md](dev-docs/api-spec.md) — contracts for all three functions (mark `[IMPLEMENTED]` when done)
- [ROADMAP.md](ROADMAP.md) — Milestone 2 candidate scope and exit criteria

## Blockers / Open Questions

- **Commodity valuation scope for `balance()`/`register()`:** ROADMAP notes "scope behaviour (file-local vs propagated via `include`) to be confirmed at implementation." Needs a user decision before commodity conversion is implemented.
- **`balance()` output for multi-commodity accounts:** Does the function return one entry per (account, commodity) pair, or a single `Decimal` per account? Needs confirmation.

## What NOT To Revisit

- Parser does not validate balance — that is `checks.py`'s job (see `knowledge/DECISIONS.md`).
- `stats()` is already implemented and tested — do not refactor it while working on the other three.
- Test subdirectories require `__init__.py` — do not remove them (Python 3.13 `unittest discover` silently skips namespace-package subdirectories).

## Recent Git State

```
1493424 chore: bump version number & mark Milestone 2 as in progress
9385430 chore: complete Milestone 1 & update project roadmap
695ee5e test: guard Optional amount access with assert-not-None
33d2257 chore: refactor test suite into subfolders and add Black config
92af4d7 feat: implement alias directive (account name rewriting)
```
