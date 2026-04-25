"""Validation checks for PyLedger journals.

Each check function accepts a Journal and returns a (possibly empty) list of
CheckError instances. An empty list means the check passed. Checks do not
print anything; callers (e.g. cli.py) format and display the errors.

Check tiers mirror hledger's classification:
  basic  — run by default on every CLI command
  strict — run when -s/--strict is given (in addition to basic)
  other  — run only when explicitly named in the `check` command
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass
from decimal import Decimal

from PyLedger.models import Journal, Transaction


# ---------------------------------------------------------------------------
# Public constants
# ---------------------------------------------------------------------------

BASIC_CHECK_NAMES: tuple[str, ...] = ("parseable", "autobalanced")
STRICT_CHECK_NAMES: tuple[str, ...] = ("accounts", "commodities")
OTHER_CHECK_NAMES: tuple[str, ...] = ("payees", "ordereddates", "uniqueleafnames")

ALL_CHECK_NAMES: tuple[str, ...] = (
    BASIC_CHECK_NAMES + STRICT_CHECK_NAMES + OTHER_CHECK_NAMES
)


# ---------------------------------------------------------------------------
# Error type
# ---------------------------------------------------------------------------

@dataclass
class CheckError:
    """A single validation failure produced by a check function.

    Attributes:
        check_name: Identifier of the check that raised this error (e.g.
                    "autobalanced").
        message:    Human-readable description of the failure. May be
                    multi-line (e.g. strict checks include source context).
    """

    check_name: str
    message: str


# ---------------------------------------------------------------------------
# Basic checks
# ---------------------------------------------------------------------------

def check_parseable(journal: Journal) -> list[CheckError]:
    """Check that the journal was parseable — always passes at this point."""
    return []


def check_autobalanced(journal: Journal) -> list[CheckError]:
    """Check that every transaction's postings net to zero per commodity.

    One elided posting (amount=None) is allowed per transaction; its amount
    is implicitly inferred as the negative sum of the remaining postings.
    When an elided posting is present the transaction is always considered
    balanced (the elision defines the missing amount). When no postings are
    elided, every commodity's net must be exactly zero.

    Multi-commodity transactions with an elided posting are flagged as an
    error because the inferred amount is ambiguous.

    Args:
        journal: The journal to check.

    Returns:
        List of CheckError, one per unbalanced transaction.
    """
    errors: list[CheckError] = []
    for txn in journal.transactions:
        errs = _check_txn_balanced(txn)
        errors.extend(errs)
    return errors


def _check_txn_balanced(txn: Transaction) -> list[CheckError]:
    """Return CheckError list for a single transaction."""
    given = [p for p in txn.postings if p.amount is not None]
    elided = [p for p in txn.postings if p.amount is None]

    label = f"transaction on {txn.date} ({txn.description!r})"

    if len(elided) > 1:
        return [CheckError(
            check_name="autobalanced",
            message=f"{label}: multiple elided postings (autobalanced)",
        )]

    # Build per-commodity sums
    commodity_sums: dict[str, Decimal] = {}
    for p in given:
        c = p.amount.commodity  # type: ignore[union-attr]
        commodity_sums[c] = commodity_sums.get(c, Decimal(0)) + p.amount.quantity  # type: ignore[union-attr]

    if len(elided) == 1:
        if len(commodity_sums) > 1:
            commodities = ", ".join(sorted(commodity_sums))
            return [CheckError(
                check_name="autobalanced",
                message=(
                    f"{label}: elided posting is ambiguous — "
                    f"multiple commodities present ({commodities})"
                ),
            )]
        # Single elided posting with one commodity → always balanced by definition
        return []

    # Zero elided postings — all commodity nets must be zero
    errors: list[CheckError] = []
    for commodity, net in sorted(commodity_sums.items()):
        if net != 0:
            errors.append(CheckError(
                check_name="autobalanced",
                message=f"{label}: not balanced — net {net:+} {commodity}",
            ))
    return errors


# ---------------------------------------------------------------------------
# Source-context formatting helpers (used by strict checks)
# ---------------------------------------------------------------------------

def _fmt_txn_header(txn: Transaction) -> str:
    """Reconstruct a transaction header line from its model fields."""
    parts = [str(txn.date)]
    if txn.cleared:
        parts.append("*")
    elif txn.pending:
        parts.append("!")
    if txn.code:
        parts.append(f"({txn.code})")
    if txn.description:
        parts.append(txn.description)
    result = " ".join(parts)
    if txn.comment:
        result += f"  ; {txn.comment}"
    return result


def _fmt_amount(amount: "Amount | None") -> str:
    """Format an Amount back to a compact display string."""
    if amount is None:
        return ""
    qty = amount.quantity
    sym = amount.commodity
    if not sym:
        return str(qty)
    if sym[0].isalpha():
        return f"{qty} {sym}"
    if qty < 0:
        return f"-{sym}{-qty}"
    return f"{sym}{qty}"


def _fmt_posting(posting: "Posting") -> str:
    """Reconstruct a posting line with standard 4-space indent."""
    if posting.amount is None:
        return f"    {posting.account}"
    return f"    {posting.account}  {_fmt_amount(posting.amount)}"


def _build_strict_context(
    journal: Journal,
    txn: Transaction,
    bad_posting: "Posting",
    caret_offset: int,
    caret_len: int,
) -> list[str]:
    """Build the source-context block used by strict check error messages.

    Returns a list of lines:
        {pad} | {txn_header}
        {N}   | {posting_with_issue}
        {pad} | {carets}
        {pad} | {other_posting}
        ...
    """
    source_file = journal.source_file or "<unknown>"
    p_line = bad_posting.source_line
    line_str = str(p_line) if p_line is not None else "?"
    num_w = max(len(line_str), 1)
    pad = " " * num_w

    lines = [f"Error: {source_file}:{line_str}:"]
    lines.append(f"{pad} | {_fmt_txn_header(txn)}")

    for p in txn.postings:
        ptext = _fmt_posting(p)
        if p is bad_posting:
            lines.append(f"{line_str} | {ptext}")
            carets = " " * caret_offset + "^" * caret_len
            lines.append(f"{pad} | {carets}")
        else:
            lines.append(f"{pad} | {ptext}")

    return lines


# ---------------------------------------------------------------------------
# Strict checks
# ---------------------------------------------------------------------------

def check_accounts(journal: Journal) -> list[CheckError]:
    """Check that every posting account has been declared.

    Stops at the first undeclared account found (by transaction then posting
    order), matching hledger behaviour. Comparison is case-sensitive.
    When declared_accounts is empty (no account directives were used),
    all posting accounts are considered undeclared.

    Args:
        journal: The journal to check.

    Returns:
        A list containing at most one CheckError with source context, or
        an empty list when all accounts are declared.
    """
    declared = set(journal.declared_accounts)
    for txn in journal.transactions:
        for posting in txn.postings:
            if posting.account not in declared:
                # Carets underline the account name in the posting line.
                # _fmt_posting produces "    {account}  {amount}". The display
                # format is "N | {ptext}", so account starts 4 chars into ptext.
                caret_offset = 4   # 4 spaces indent in _fmt_posting
                caret_len = len(posting.account)
                ctx = _build_strict_context(
                    journal, txn, posting, caret_offset, caret_len
                )
                ctx += [
                    "",
                    "Strict account checking is enabled, and",
                    f'account "{posting.account}" has not been declared.',
                    "Consider adding an account directive. Examples:",
                    "",
                    f"account {posting.account}",
                    f"account {posting.account}    ; type:A  ; (L,E,R,X,C,V)",
                ]
                return [CheckError(check_name="accounts", message="\n".join(ctx))]
    return []


def check_commodities(journal: Journal) -> list[CheckError]:
    """Check that every commodity symbol in use has been declared.

    Stops at the first undeclared commodity found, matching hledger behaviour.
    Zero-amount postings (commodity symbol == "") are always exempt.
    When declared_commodities is empty, all non-empty symbols are undeclared.

    Args:
        journal: The journal to check.

    Returns:
        A list containing at most one CheckError with source context, or
        an empty list when all commodities are declared.
    """
    declared = set(journal.declared_commodities)
    for txn in journal.transactions:
        for posting in txn.postings:
            if posting.amount is None:
                continue
            sym = posting.amount.commodity
            if sym == "":
                continue  # zero-amount postings are exempt
            if sym not in declared:
                # Carets underline the amount (commodity + quantity) in the
                # posting line. _fmt_posting gives "    {account}  {amount}",
                # so amount starts at 4 + len(account) + 2 into the ptext.
                amt_str = _fmt_amount(posting.amount)
                caret_offset = 4 + len(posting.account) + 2  # indent + account + 2-space sep
                caret_len = max(len(amt_str), 1)
                ctx = _build_strict_context(
                    journal, txn, posting, caret_offset, caret_len
                )
                ctx += [
                    "",
                    "Strict commodity checking is enabled, and",
                    f'commodity "{sym}" has not been declared.',
                    "Consider adding a commodity directive. Examples:",
                    "",
                    f"commodity {sym}",
                    f"commodity {amt_str}",
                ]
                return [CheckError(check_name="commodities", message="\n".join(ctx))]
    return []


# ---------------------------------------------------------------------------
# Other checks
# ---------------------------------------------------------------------------

def check_payees(journal: Journal) -> list[CheckError]:
    """Check that every transaction description is a declared payee.

    When declared_payees is empty (no payee directives), all descriptions
    are considered undeclared.

    Args:
        journal: The journal to check.

    Returns:
        List of CheckError, one per undeclared payee name.
    """
    declared = set(journal.declared_payees)

    errors: list[CheckError] = []
    seen_undeclared: set[str] = set()
    for txn in journal.transactions:
        name = txn.description
        if name not in declared and name not in seen_undeclared:
            seen_undeclared.add(name)
            errors.append(CheckError(
                check_name="payees",
                message=f"payee not declared: {name!r} (payees check)",
            ))
    return errors


def check_ordereddates(journal: Journal) -> list[CheckError]:
    """Check that transactions are in non-decreasing date order.

    hledger evaluates this per-file, but since PyLedger merges included
    files before parsing, this check operates on the full merged transaction
    list in journal order.

    Args:
        journal: The journal to check.

    Returns:
        List of CheckError, one per out-of-order transaction.
    """
    errors: list[CheckError] = []
    prev_date: datetime.date | None = None
    for txn in journal.transactions:
        if prev_date is not None and txn.date < prev_date:
            errors.append(CheckError(
                check_name="ordereddates",
                message=(
                    f"transaction on {txn.date} ({txn.description!r}) is out of order "
                    f"— appears after {prev_date} (ordereddates check)"
                ),
            ))
        else:
            prev_date = txn.date
    return errors


def check_uniqueleafnames(journal: Journal) -> list[CheckError]:
    """Check that no two accounts share the same last colon-segment.

    hledger uses the last colon-segment (leaf) for short account name
    matching, so duplicate leaves make disambiguation impossible.

    Args:
        journal: The journal to check.

    Returns:
        List of CheckError, one per duplicate leaf name.
    """
    all_accounts = {p.account for t in journal.transactions for p in t.postings}

    leaf_to_accounts: dict[str, list[str]] = {}
    for acct in all_accounts:
        leaf = acct.rsplit(":", 1)[-1]
        leaf_to_accounts.setdefault(leaf, []).append(acct)

    errors: list[CheckError] = []
    for leaf, accounts in sorted(leaf_to_accounts.items()):
        if len(accounts) > 1:
            dupes = ", ".join(sorted(accounts))
            errors.append(CheckError(
                check_name="uniqueleafnames",
                message=(
                    f"duplicate leaf account name {leaf!r}: {dupes} "
                    f"(uniqueleafnames check)"
                ),
            ))
    return errors


# ---------------------------------------------------------------------------
# Check registry and runners
# ---------------------------------------------------------------------------

_CHECK_FN = {
    "parseable": check_parseable,
    "autobalanced": check_autobalanced,
    "accounts": check_accounts,
    "commodities": check_commodities,
    "payees": check_payees,
    "ordereddates": check_ordereddates,
    "uniqueleafnames": check_uniqueleafnames,
}


def run_basic_checks(journal: Journal) -> list[CheckError]:
    """Run the basic checks (parseable, autobalanced) and return all errors."""
    errors: list[CheckError] = []
    for name in BASIC_CHECK_NAMES:
        errors.extend(_CHECK_FN[name](journal))
    return errors


def run_strict_checks(journal: Journal) -> list[CheckError]:
    """Run basic + strict checks and return all errors."""
    errors = run_basic_checks(journal)
    for name in STRICT_CHECK_NAMES:
        errors.extend(_CHECK_FN[name](journal))
    return errors


def run_checks(
    journal: Journal,
    names: list[str] | None = None,
    *,
    strict: bool = False,
) -> list[CheckError]:
    """Run checks and return all errors.

    Always runs basic checks. When strict=True, also runs strict checks.
    Any names in `names` that are not already in the basic/strict tier are
    run in addition.

    Args:
        journal: The journal to check.
        names: Optional list of additional check names to run (from
               OTHER_CHECK_NAMES, or any valid check name).
        strict: If True, run strict checks in addition to basic.

    Returns:
        Combined list of CheckError from all requested checks.

    Raises:
        ValueError: if a name in `names` is not a recognised check.
    """
    names = names or []
    for name in names:
        if name not in _CHECK_FN:
            raise ValueError(
                f"unknown check {name!r}; available: {', '.join(sorted(_CHECK_FN))}"
            )

    errors = run_basic_checks(journal)

    if strict:
        for name in STRICT_CHECK_NAMES:
            errors.extend(_CHECK_FN[name](journal))

    already_run = set(BASIC_CHECK_NAMES)
    if strict:
        already_run |= set(STRICT_CHECK_NAMES)

    for name in names:
        if name not in already_run:
            errors.extend(_CHECK_FN[name](journal))
            already_run.add(name)

    return errors
