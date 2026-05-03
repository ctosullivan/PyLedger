# Context — 2026-05-03

## Current Task
Milestone 3 implementation complete — awaiting user review and commit.

## Where We Are
All Milestone 3 code, tests, and docs are done. 405 tests pass. Uncommitted.
Next: user reviews, commits, and (optionally) marks Milestone 3 done in ROADMAP.md.

## Decisions In Flight
- `balance_from_spec` retains `dict[str, Decimal]` (multi-commodity deferred) — see plan.
- `register()` running_balance stays `Decimal` (changing `RegisterRow` out of scope).

## Files Currently Relevant
All Milestone 3 files are ready:
- `PyLedger/models.py` — Posting.inferred, BalanceRow added
- `PyLedger/parser.py` — resolve_elision(), _parse_string_impl(), parse_string_lenient()
- `PyLedger/checks.py` — CheckError.line_number, _check_txn_balanced rewritten
- `PyLedger/reports.py` — balance() now dict[str, dict[str, Decimal]], tree mode
- `PyLedger/cli.py` — hledger-style multi-commodity balance display
- `PyLedger/__init__.py` — new exports, version 0.4.0
- `tests/fixtures/multicommodity.journal` — new multi-commodity fixture
- `tests/test_parser/test_parser.py` — TestResolveElision, TestParseStringLenient
- `tests/test_checks/test_checks.py` — TestCheckErrorLineNumber
- `tests/test_reports.py` — TestBalanceMultiCommodity, updated assertions
- `dev-docs/api-spec.md` — updated for all Milestone 3 changes
- `CHANGELOG.md` — new [Unreleased] entry

## Blockers / Open Questions
None — awaiting user review and commit.

## What NOT To Revisit
- `balance()` return type change (`dict[str, Decimal]` → `dict[str, dict[str, Decimal]]`)
  is a confirmed breaking change, approved as Milestone 3 scope.
- CLI balance format: account name only on LAST commodity line per account (hledger style).
- `_check_txn_balanced` does NOT call `resolve_elision` — it only checks structure.
- `balance_from_spec` multi-commodity support deferred — out of Milestone 3 scope.

## Recent Git State
```
d012bfe chore: release v0.3.0 and mark Milestone 2 done
6ca9fb0 chore: release v0.3.0 and mark Milestone 2 done
786a198 fix: accept trailing decimal point in amounts ($1,350,000.)
5b9d383 feat: implement balance assertions (=, ==, =*, ==*)
acc93a3 feat: Milestone 2 core reports and hledger-aligned CLI output
```
