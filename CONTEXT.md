# Context — 2026-05-02

## Current Task
Align `balance` and `register` CLI output to hledger format — complete.

## Where We Are
Both `balance` and `register` display correctly. 342 tests pass. Next step is to
commit (user to confirm). Milestone 2 still awaiting explicit confirmation to mark
`[DONE]` in ROADMAP.md (CLAUDE.md rule).

## Decisions In Flight
- `balance()` returns `dict[str, Decimal]` (no commodity); CLI recovers commodity via
  `_primary_commodity()` which scans the first posting. Multi-commodity balance display
  is not yet supported and would require a deeper change to the return type.
- `stats()` has partial query support — date/payee filters applied, account-level deferred.

## Files Currently Relevant
- `PyLedger/cli.py` — `_primary_commodity`, `_fmt_amount`, `_fmt_balance`,
  `_abbreviate_account`; updated `balance` and `register` display loops
- `tests/test_cli/test_cli.py` — `TestBalanceOutput` and `TestRegisterOutput`
- `CHANGELOG.md` — two new unreleased entries

## Blockers / Open Questions
- Milestone 2 `[DONE]` confirmation still pending from user.
- Multi-commodity balance display deferred — `balance()` would need to return
  `dict[str, list[Amount]]` or similar to carry commodity info.

## What NOT To Revisit
- `RegisterRow` date+description continuation key is a known limitation (EC-012).
- CLI filter flag integration (`-b`/`-e` dates, `-A` account) is Milestone 3.
- Commodity valuation using `Journal.prices` is Milestone 3.

## Recent Git State
```
2bf467e chore: add knowledge base and CONTEXT.md session memory
1493424 chore: bump version number & mark Milestone 2 as in progress
9385430 chore: complete Milestone 1 & update project roadmap
695ee5e test: guard Optional amount access with assert-not-None
33d2257 chore: refactor test suite into subfolders and add Black config
```
(All changes since 2bf467e are uncommitted.)
