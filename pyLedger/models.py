"""Core data models for PyLedger.

Defines the canonical Python data structures for journal entries.
No parsing or reporting logic lives here.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class Amount:
    """A numeric quantity paired with a commodity symbol.

    Examples:
        Amount(Decimal("30.00"), "£")
        Amount(Decimal("1500.00"), "EUR")
    """

    quantity: Decimal
    commodity: str


@dataclass
class Posting:
    """One line within a transaction: an account name and an optional amount.

    When `amount` is None the amount is inferred from the other postings
    in the same transaction (hledger elided-amount syntax).
    """

    account: str
    amount: Amount | None = None


@dataclass
class Transaction:
    """A complete journal transaction entry."""

    date: datetime.date
    description: str
    postings: list[Posting] = field(default_factory=list)
    cleared: bool = False    # True when marked with "*"
    pending: bool = False    # True when marked with "!"
    code: str = ""           # Optional code in parentheses before description
    comment: str = ""        # Inline or trailing comment text


@dataclass
class Journal:
    """Top-level container for all parsed journal data."""

    transactions: list[Transaction] = field(default_factory=list)
    source_file: str | None = None
