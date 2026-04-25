"""Core data models for PyLedger.

Defines the canonical Python data structures for journal entries.
No parsing or reporting logic lives here.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PyLedger.reports import JournalStats


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
    source_line: int | None = field(default=None, repr=False)


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
    source_line: int | None = field(default=None, repr=False)


@dataclass
class PriceDirective:
    """A P directive declaring a commodity market price on a given date.

    Example journal line: P 2024-03-01 AAPL $179.00
    Stored in Journal.prices for use by valuation reports.
    """

    date: datetime.date
    commodity: str           # The commodity being priced (e.g. "AAPL", "EUR")
    price: Amount            # The price expressed as an Amount (quantity + currency)


@dataclass
class Journal:
    """Top-level container for all parsed journal data.

    Returned by parse_string() and parse_file(). Report methods on this class
    delegate to PyLedger.reports and use lazy imports to avoid circular
    dependencies between models.py and reports.py.
    """

    transactions: list[Transaction] = field(default_factory=list)
    prices: list[PriceDirective] = field(default_factory=list)
    declared_accounts: list[str] = field(default_factory=list)
    declared_commodities: list[str] = field(default_factory=list)
    declared_payees: list[str] = field(default_factory=list)
    declared_tags: list[str] = field(default_factory=list)
    source_file: str | None = None
    included_files: int = 0

    # ------------------------------------------------------------------
    # Report methods — thin wrappers that delegate to PyLedger.reports.
    # Lazy imports are used to avoid a circular dependency:
    #   models.py → reports.py → models.py
    # ------------------------------------------------------------------

    def balance(self, accounts: list[str] | None = None) -> dict[str, Decimal]:
        """Return a mapping of account name to net balance.

        Args:
            accounts: Optional list of account name prefixes to filter by.
                      If None, all accounts are included.
        """
        from PyLedger.reports import balance as _balance
        return _balance(self, accounts)

    def register(self, accounts: list[str] | None = None):
        """Return a chronological list of RegisterRow objects.

        Args:
            accounts: Optional list of account name prefixes to filter by.
        """
        from PyLedger.reports import register as _register
        return _register(self, accounts)

    def accounts(self) -> list[str]:
        """Return a sorted list of all unique account names in the journal."""
        from PyLedger.reports import accounts as _accounts
        return _accounts(self)

    def stats(self) -> JournalStats:
        """Return a JournalStats object with summary statistics."""
        from PyLedger.reports import stats as _stats
        return _stats(self)
