# Context — 2026-05-03

## Current Task
Implement balance assertions (`=`, `==`, `=*`, `==*`) as part of Milestone 2.

## Where We Are
Implementation complete. 361 tests pass. All docs updated. Awaiting user commit
confirmation. Milestone 2 still awaiting explicit `[DONE]` confirmation from user.

## Decisions In Flight
- Balance assignments (`= AMOUNT` with no preceding posting amount) are parsed
  but not validated — deferred to a future milestone. See `knowledge/DECISIONS.md`.
- `balance()` still returns `dict[str, Decimal]` (no commodity); multi-commodity
  balance display deferred.

## Files Currently Relevant
- `PyLedger/models.py` — new `BalanceAssertion` dataclass; `Posting.balance_assertion` field
- `PyLedger/parser.py` — `_ASSERTION_MARKER_RE`; updated `_parse_posting`
- `PyLedger/checks.py` — `check_assertions`; updated constants/runners with `skip` param
- `PyLedger/cli.py` — `-I`/`--ignore-assertions` flag
- `tests/fixtures/assertions_pass.journal`, `tests/fixtures/assertions_fail.journal`
- `tests/test_checks/test_checks.py` — `TestCheckAssertions` (12 tests)
- `tests/test_cli/test_cli.py` — `TestBalanceAssertions` (6 tests)

## Blockers / Open Questions
- Milestone 2 `[DONE]` confirmation still pending from user.
- Balance assignments (amount inferred from assertion) deferred — tracked in DECISIONS.md.

## What NOT To Revisit
- `assertions` is basic tier (not other tier) — this is intentional; see DECISIONS.md.
- `RegisterRow` date+description continuation key is a known limitation (EC-012).
- CLI filter flag integration (`-b`/`-e` dates, `-A` account) is Milestone 3.
- Commodity valuation using `Journal.prices` is Milestone 3.

## Recent Git State
```
acc93a3 feat: Milestone 2 core reports and hledger-aligned CLI output
2bf467e chore: add knowledge base and CONTEXT.md session memory
1493424 chore: bump version number & mark Milestone 2 as in progress
9385430 chore: complete Milestone 1 & update project roadmap
695ee5e test: guard Optional amount access with assert-not-None
```
(Balance assertions work is uncommitted.)
