"""Tests for PyLedger.reports — stats() function."""

import datetime
import os
import unittest

from PyLedger.loader import load_journal
from PyLedger.parser import parse_string
from PyLedger.reports import stats, JournalStats


FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
SAMPLE_JOURNAL = os.path.join(FIXTURES_DIR, "sample.journal")


class TestStatsSampleJournal(unittest.TestCase):
    """stats() against tests/fixtures/sample.journal."""

    def setUp(self):
        self.journal = load_journal(SAMPLE_JOURNAL)
        self.s = stats(self.journal)

    def test_transaction_count(self):
        self.assertEqual(self.s.transaction_count, 5)

    def test_included_files(self):
        self.assertEqual(self.s.included_files, 0)

    def test_date_range(self):
        self.assertEqual(self.s.date_range, (datetime.date(2024, 1, 1), datetime.date(2024, 1, 20)))

    def test_txns_span_days(self):
        # 2024-01-01 to 2024-01-20 inclusive = 20 days
        self.assertEqual(self.s.txns_span_days, 20)

    def test_account_depth(self):
        # assets:bank:checking has depth 3
        self.assertGreaterEqual(self.s.account_depth, 3)

    def test_commodity_count(self):
        self.assertEqual(self.s.commodity_count, 1)

    def test_commodities_list(self):
        self.assertIn("£", self.s.commodities)

    def test_price_count(self):
        self.assertEqual(self.s.price_count, 0)

    def test_payee_count(self):
        # 5 unique descriptions in sample.journal
        self.assertEqual(self.s.payee_count, 5)

    def test_account_count(self):
        # assets:bank:checking, equity:opening-balances, income:salary,
        # expenses:food:groceries, assets:bank:savings, expenses:food:coffee = 6
        self.assertEqual(self.s.account_count, 6)

    def test_source_file_set(self):
        self.assertIsNotNone(self.s.source_file)


class TestStatsEmptyJournal(unittest.TestCase):
    """stats() with no transactions."""

    def setUp(self):
        self.s = stats(parse_string(""))

    def test_transaction_count(self):
        self.assertEqual(self.s.transaction_count, 0)

    def test_date_range_none(self):
        self.assertIsNone(self.s.date_range)

    def test_last_txn_date_none(self):
        self.assertIsNone(self.s.last_txn_date)

    def test_txns_span_days_none(self):
        self.assertIsNone(self.s.txns_span_days)

    def test_account_count_zero(self):
        self.assertEqual(self.s.account_count, 0)

    def test_commodity_count_zero(self):
        self.assertEqual(self.s.commodity_count, 0)

    def test_txns_per_day_zero(self):
        self.assertEqual(self.s.txns_per_day, 0.0)

    def test_payee_count_zero(self):
        self.assertEqual(self.s.payee_count, 0)


class TestStatsDateRangeAndSpan(unittest.TestCase):
    """date_range, txns_span_days, and txns_per_day computed correctly."""

    def setUp(self):
        journal_text = """\
2024-03-01 First
    assets:cash  £10.00
    equity:open  -£10.00

2024-03-11 Second
    assets:cash  £20.00
    equity:open  -£20.00
"""
        self.s = stats(parse_string(journal_text))

    def test_date_range(self):
        self.assertEqual(
            self.s.date_range,
            (datetime.date(2024, 3, 1), datetime.date(2024, 3, 11)),
        )

    def test_txns_span_days(self):
        # 2024-03-01 to 2024-03-11 inclusive = 11 days
        self.assertEqual(self.s.txns_span_days, 11)

    def test_txns_per_day(self):
        # 2 transactions over 11 days
        self.assertAlmostEqual(self.s.txns_per_day, 2 / 11)

    def test_last_txn_date(self):
        self.assertEqual(self.s.last_txn_date, datetime.date(2024, 3, 11))

    def test_last_txn_days_ago_non_negative(self):
        self.assertGreaterEqual(self.s.last_txn_days_ago, 0)


class TestStatsMultipleCommodities(unittest.TestCase):
    """commodity_count and commodities list with two symbols."""

    def setUp(self):
        journal_text = """\
2024-01-01 Sterling purchase
    assets:gbp   £100.00
    assets:usd   -150.00 USD

2024-01-02 Another
    assets:gbp   £50.00
    assets:usd   -75.00 USD
"""
        self.s = stats(parse_string(journal_text))

    def test_commodity_count(self):
        self.assertEqual(self.s.commodity_count, 2)

    def test_commodities_contains_both(self):
        self.assertIn("£", self.s.commodities)
        self.assertIn("USD", self.s.commodities)

    def test_commodities_sorted(self):
        self.assertEqual(self.s.commodities, sorted(self.s.commodities))


class TestStatsPayeeDeduplication(unittest.TestCase):
    """payee_count deduplicates repeated descriptions."""

    def setUp(self):
        journal_text = """\
2024-01-01 Coffee
    expenses:coffee  £3.00
    assets:cash      -£3.00

2024-01-02 Coffee
    expenses:coffee  £3.50
    assets:cash      -£3.50

2024-01-03 Lunch
    expenses:food  £8.00
    assets:cash    -£8.00
"""
        self.s = stats(parse_string(journal_text))

    def test_payee_count(self):
        # "Coffee" appears twice but counts once; "Lunch" is distinct → 2
        self.assertEqual(self.s.payee_count, 2)


class TestStatsAccountDepth(unittest.TestCase):
    """account_depth equals the maximum colon-segment depth."""

    def setUp(self):
        journal_text = """\
2024-01-01 Deep account
    a:b:c:d  £1.00
    equity   -£1.00
"""
        self.s = stats(parse_string(journal_text))

    def test_account_depth(self):
        # a:b:c:d has 4 segments; equity has 1
        self.assertEqual(self.s.account_depth, 4)


class TestStatsModuleLevel(unittest.TestCase):
    """journal.stats() (method on Journal) returns same result as reports.stats()."""

    def test_module_level_call(self):
        journal = load_journal(SAMPLE_JOURNAL)
        via_function = stats(journal)
        via_method = journal.stats()
        self.assertEqual(via_function.transaction_count, via_method.transaction_count)
        self.assertEqual(via_function.account_count, via_method.account_count)
        self.assertEqual(via_function.commodities, via_method.commodities)
        self.assertEqual(via_function.date_range, via_method.date_range)


if __name__ == "__main__":
    unittest.main()
