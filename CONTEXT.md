# Context — 2026-05-03

## Current Task
Milestone 2 complete. Starting Milestone 3 planning.

## Where We Are
Milestone 2 marked `[DONE]`. Version bumped to 0.3.0. All changes committed.
Milestone 3 scope partially confirmed: limited multi-commodity support confirmed in;
full scope not yet agreed.

## Decisions In Flight
- Balance assignments (`= AMOUNT` with no preceding posting amount) deferred to
  a future milestone. See `knowledge/DECISIONS.md`.
- Milestone 3 full scope not yet confirmed by user — see ROADMAP.md candidate list.

## Files Currently Relevant
- `ROADMAP.md` — Milestone 3 candidate scope (partially confirmed)
- `PyLedger/reports.py` — `balance()` returns `dict[str, Decimal]`; will need
  rework for multi-commodity support
- `PyLedger/cli.py` — balance/register display assumes single commodity via
  `_primary_commodity`

## Blockers / Open Questions
- Milestone 3 full scope needs user confirmation before implementation begins.
- What "limited multi-commodity" means precisely:
  - Does `balance` return `dict[str, dict[str, Decimal]]` (account → commodity → amount)?
  - Or a list of `(account, commodity, amount)` rows?
  - Does the CLI show one row per commodity per account?

## What NOT To Revisit
- `assertions` is basic tier (not other tier) — see `knowledge/DECISIONS.md`.
- `RegisterRow` date+description continuation key is a known limitation (EC-012).
- Balance assignments (amount inferred from assertion) deferred — tracked in DECISIONS.md.

## Recent Git State
```
(will be filled after commit)
```
