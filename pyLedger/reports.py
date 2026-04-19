"""Report generators for PyLedger.

Each function accepts a Journal and returns structured data — not formatted
strings. Formatting is handled by cli.py.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass
from decimal import Decimal

from PyLedger.models import Amount, Journal


@dataclass
class RegisterRow:
    """One row in a register report."""

    date: datetime.date
    description: str
    account: str
    amount: Amount
    running_balance: Decimal


@dataclass
class JournalStats:
    """Summary statistics for a journal.

    Contains only deterministic journal data. Runtime stats (elapsed time,
    txns/s) are measured and formatted by the CLI layer, not stored here.
    """

    source_file: str | None
    included_files: int  # 0 until include directive is implemented
    transaction_count: int
    date_range: tuple[datetime.date, datetime.date] | None  # (first, last)
    last_txn_date: datetime.date | None
    last_txn_days_ago: int | None  # (today - last_txn_date).days
    txns_span_days: int | None  # (last - first).days + 1
    txns_per_day: float  # transaction_count / txns_span_days, else 0.0
    txns_last_30_days: int
    txns_per_day_last_30: float
    txns_last_7_days: int
    txns_per_day_last_7: float
    payee_count: int  # unique descriptions
    account_count: int
    account_depth: int  # max colon-segment depth across all accounts
    commodity_count: int
    commodities: list[str]  # sorted commodity symbols (shown in verbose mode)
    price_count: int  # len(journal.prices)


def balance(
    journal: Journal,
    accounts: list[str] | None = None,
) -> dict[str, Decimal]:
    """Return a mapping of account name to net balance.

    Args:
        journal: The parsed journal.
        accounts: Optional list of account name prefixes to filter by.
                  If None, all accounts are included.

    Returns:
        Dict mapping each account name to its net balance as a Decimal.
    """
    raise NotImplementedError("balance is not yet implemented")


def register(
    journal: Journal,
    accounts: list[str] | None = None,
) -> list[RegisterRow]:
    """Return a chronological list of register rows.

    Args:
        journal: The parsed journal.
        accounts: Optional list of account name prefixes to filter by.
    """
    raise NotImplementedError("register is not yet implemented")


def accounts(journal: Journal) -> list[str]:
    """Return a sorted list of all unique account names in the journal."""
    raise NotImplementedError("accounts is not yet implemented")


def stats(journal: Journal) -> JournalStats:
    """Return summary statistics for the journal."""
    today = datetime.date.today()
    txns = journal.transactions

    all_accounts: set[str] = {p.account for t in txns for p in t.postings}
    all_commodities: set[str] = {
        p.amount.commodity for t in txns for p in t.postings if p.amount is not None
    }
    dates = [t.date for t in txns]
    date_range = (min(dates), max(dates)) if dates else None
    last_txn_date = max(dates) if dates else None
    span_days = (date_range[1] - date_range[0]).days + 1 if date_range else None

    cutoff_30 = today - datetime.timedelta(days=30)
    cutoff_7 = today - datetime.timedelta(days=7)
    txns_30 = sum(1 for t in txns if t.date >= cutoff_30)
    txns_7 = sum(1 for t in txns if t.date >= cutoff_7)

    depth = max((len(a.split(":")) for a in all_accounts), default=0)

    return JournalStats(
        source_file=journal.source_file,
        included_files=0,
        transaction_count=len(txns),
        date_range=date_range,
        last_txn_date=last_txn_date,
        last_txn_days_ago=(today - last_txn_date).days if last_txn_date else None,
        txns_span_days=span_days,
        txns_per_day=len(txns) / span_days if span_days else 0.0,
        txns_last_30_days=txns_30,
        txns_per_day_last_30=txns_30 / 30,
        txns_last_7_days=txns_7,
        txns_per_day_last_7=txns_7 / 7,
        payee_count=len({t.description for t in txns}),
        account_count=len(all_accounts),
        account_depth=depth,
        commodity_count=len(all_commodities),
        commodities=sorted(all_commodities),
        price_count=len(journal.prices),
    )
