"""Report generators for PyLedger.

Each function accepts a Journal and returns structured data — not formatted
strings. Formatting is handled by cli.py.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass
from decimal import Decimal

from pyLedger.models import Amount, Journal


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
    """Summary statistics for a journal."""

    source_file: str | None
    transaction_count: int
    account_count: int
    date_range: tuple[datetime.date, datetime.date] | None  # (first, last)
    commodity_count: int


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
    raise NotImplementedError("stats is not yet implemented")
