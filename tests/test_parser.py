"""Tests for PyLedger.parser — parse_string."""

import datetime
import os
import pathlib
import unittest
from decimal import Decimal

from PyLedger.models import Amount, Journal, Posting, Transaction
from PyLedger.parser import ParseError, parse_string

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
SAMPLE_JOURNAL = os.path.join(FIXTURES, "sample.journal")


class TestParseStringSampleJournal(unittest.TestCase):
    """Test 1: parse the full sample.journal end-to-end via parse_string."""

    def setUp(self):
        self.journal = parse_string(
            pathlib.Path(SAMPLE_JOURNAL).read_text(encoding="utf-8")
        )

    def test_transaction_count(self):
        self.assertEqual(len(self.journal.transactions), 5)

    def test_dates(self):
        expected = [
            datetime.date(2024, 1, 1),
            datetime.date(2024, 1, 5),
            datetime.date(2024, 1, 10),
            datetime.date(2024, 1, 15),
            datetime.date(2024, 1, 20),
        ]
        actual = [t.date for t in self.journal.transactions]
        self.assertEqual(actual, expected)

    def test_descriptions(self):
        expected = [
            "Opening balance",
            "Salary",
            "Supermarket",
            "Transfer to savings",
            "Coffee shop",
        ]
        actual = [t.description for t in self.journal.transactions]
        self.assertEqual(actual, expected)


class TestStatusFlags(unittest.TestCase):
    """Test 2: cleared (*) and pending (!) flags."""

    def test_cleared_flag(self):
        journal = parse_string("2024-01-05 * Salary\n    income:salary  -£100\n    assets:bank  £100\n")
        self.assertTrue(journal.transactions[0].cleared)
        self.assertFalse(journal.transactions[0].pending)

    def test_pending_flag(self):
        journal = parse_string("2024-01-15 ! Transfer\n    assets:savings  £50\n    assets:bank  -£50\n")
        self.assertTrue(journal.transactions[0].pending)
        self.assertFalse(journal.transactions[0].cleared)

    def test_no_flag(self):
        journal = parse_string("2024-01-10 Groceries\n    expenses:food  £30\n    assets:bank  -£30\n")
        self.assertFalse(journal.transactions[0].cleared)
        self.assertFalse(journal.transactions[0].pending)


class TestElidedAmount(unittest.TestCase):
    """Test 3: a posting with no amount has amount=None."""

    def test_elided_amount_is_none(self):
        journal = parse_string(
            "2024-01-10 Groceries\n"
            "    expenses:food  £30.00\n"
            "    assets:bank\n"
        )
        postings = journal.transactions[0].postings
        self.assertIsNotNone(postings[0].amount)
        self.assertIsNone(postings[1].amount)


class TestPrefixCommodity(unittest.TestCase):
    """Test 4: prefix commodity symbol (£30.00)."""

    def test_prefix_symbol(self):
        journal = parse_string(
            "2024-01-10 Groceries\n"
            "    expenses:food  £30.00\n"
            "    assets:bank  -£30.00\n"
        )
        amount = journal.transactions[0].postings[0].amount
        self.assertEqual(amount.quantity, Decimal("30.00"))
        self.assertEqual(amount.commodity, "£")


class TestSuffixCommodity(unittest.TestCase):
    """Test 5: suffix commodity symbol (30.00 EUR)."""

    def test_suffix_symbol(self):
        journal = parse_string(
            "2024-01-10 Exchange\n"
            "    assets:eur  30.00 EUR\n"
            "    assets:bank  -30.00 EUR\n"
        )
        amount = journal.transactions[0].postings[0].amount
        self.assertEqual(amount.quantity, Decimal("30.00"))
        self.assertEqual(amount.commodity, "EUR")


class TestNegativeAmount(unittest.TestCase):
    """Test 6: negative amounts (-£5.00)."""

    def test_negative_prefix(self):
        journal = parse_string(
            "2024-01-10 Refund\n"
            "    assets:bank  -£5.00\n"
            "    expenses:food  £5.00\n"
        )
        amount = journal.transactions[0].postings[0].amount
        self.assertEqual(amount.quantity, Decimal("-5.00"))
        self.assertEqual(amount.commodity, "£")

    def test_negative_suffix(self):
        journal = parse_string(
            "2024-01-10 Refund\n"
            "    assets:bank  -30.00 EUR\n"
            "    expenses:food  30.00 EUR\n"
        )
        amount = journal.transactions[0].postings[0].amount
        self.assertEqual(amount.quantity, Decimal("-30.00"))
        self.assertEqual(amount.commodity, "EUR")


class TestThousandsSeparator(unittest.TestCase):
    """Test 7: thousands separator commas (£1,234.56)."""

    def test_thousands_comma(self):
        journal = parse_string(
            "2024-01-05 Salary\n"
            "    assets:bank  £1,234.56\n"
            "    income:salary  -£1,234.56\n"
        )
        amount = journal.transactions[0].postings[0].amount
        self.assertEqual(amount.quantity, Decimal("1234.56"))
        self.assertEqual(amount.commodity, "£")


class TestComments(unittest.TestCase):
    """Test 8: comment lines are ignored; inline comments are captured."""

    def test_whole_line_semicolon_comment_ignored(self):
        journal = parse_string(
            "; this whole line is a comment\n"
            "2024-01-10 Groceries\n"
            "    expenses:food  £30.00\n"
            "    assets:bank  -£30.00\n"
        )
        self.assertEqual(len(journal.transactions), 1)

    def test_whole_line_hash_comment_ignored(self):
        journal = parse_string(
            "# another comment style\n"
            "2024-01-10 Groceries\n"
            "    expenses:food  £30.00\n"
            "    assets:bank  -£30.00\n"
        )
        self.assertEqual(len(journal.transactions), 1)

    def test_inline_comment_on_header_captured(self):
        journal = parse_string(
            "2024-01-20 Coffee shop  ; business meeting\n"
            "    expenses:food  £4.50\n"
            "    assets:bank  -£4.50\n"
        )
        self.assertEqual(journal.transactions[0].comment, "business meeting")


class TestPostingBeforeTransaction(unittest.TestCase):
    """Test 9: a posting line outside a transaction block raises ParseError."""

    def test_posting_outside_block_raises(self):
        with self.assertRaises(ParseError) as ctx:
            parse_string("    expenses:food  £30.00\n")
        self.assertIn("outside a transaction block", str(ctx.exception))


class TestTwoElidedAmounts(unittest.TestCase):
    """Test 10: two elided amounts in one block raises ParseError."""

    def test_two_elided_raises(self):
        with self.assertRaises(ParseError) as ctx:
            parse_string(
                "2024-01-10 Groceries\n"
                "    expenses:food\n"
                "    assets:bank\n"
            )
        self.assertIn("at most one elided amount", str(ctx.exception))


class TestBlockComments(unittest.TestCase):
    """Tests for the comment / end comment block-comment directive."""

    def test_block_comment_between_transactions(self):
        """Content inside a block comment is not parsed as transactions."""
        journal = parse_string(
            "2024-01-01 Before\n"
            "    expenses:food  £10.00\n"
            "    assets:bank  -£10.00\n"
            "\n"
            "comment\n"
            "2024-01-02 Inside — should be ignored\n"
            "    expenses:food  £99.00\n"
            "end comment\n"
            "\n"
            "2024-01-03 After\n"
            "    expenses:food  £20.00\n"
            "    assets:bank  -£20.00\n"
        )
        self.assertEqual(len(journal.transactions), 2)
        self.assertEqual(journal.transactions[0].description, "Before")
        self.assertEqual(journal.transactions[1].description, "After")

    def test_block_comment_at_start_of_file(self):
        """Block comment at file start does not produce transactions."""
        journal = parse_string(
            "comment\n"
            "This file begins with a block comment.\n"
            "end comment\n"
            "\n"
            "2024-01-05 Salary\n"
            "    assets:bank  £100.00\n"
            "    income:salary  -£100.00\n"
        )
        self.assertEqual(len(journal.transactions), 1)
        self.assertEqual(journal.transactions[0].description, "Salary")

    def test_unclosed_block_comment_runs_to_eof(self):
        """A block comment without end comment silently consumes the rest of the file."""
        journal = parse_string(
            "2024-01-01 Real\n"
            "    expenses:food  £5.00\n"
            "    assets:bank  -£5.00\n"
            "\n"
            "comment\n"
            "2024-01-02 Ignored\n"
            "    expenses:food  £999.00\n"
        )
        self.assertEqual(len(journal.transactions), 1)
        self.assertEqual(journal.transactions[0].description, "Real")

    def test_follow_on_comment_line_skipped(self):
        """Indented ; lines inside a transaction block are silently skipped."""
        journal = parse_string(
            "2024-01-10 Groceries\n"
            "    ; this is a follow-on comment\n"
            "    expenses:food  £30.00\n"
            "    assets:bank  -£30.00\n"
        )
        self.assertEqual(len(journal.transactions[0].postings), 2)

    def test_end_comment_outside_block_silently_ignored(self):
        """end comment appearing outside a block comment is silently skipped."""
        journal = parse_string(
            "end comment\n"
            "2024-01-01 Txn\n"
            "    expenses:food  £5.00\n"
            "    assets:bank  -£5.00\n"
        )
        self.assertEqual(len(journal.transactions), 1)


class TestSimpleDateFormats(unittest.TestCase):
    """Test suite for all accepted simple date formats."""

    def _single_txn(self, date_line: str) -> datetime.date:
        """Helper: parse a minimal transaction with the given date line."""
        journal = parse_string(
            f"{date_line} Test\n"
            "    expenses:food  £10.00\n"
            "    assets:bank  -£10.00\n"
        )
        return journal.transactions[0].date

    def test_iso_hyphen(self):
        """YYYY-MM-DD — baseline ISO format."""
        self.assertEqual(self._single_txn("2024-01-15"), datetime.date(2024, 1, 15))

    def test_slash_separator(self):
        """YYYY/MM/DD — forward-slash separator."""
        self.assertEqual(self._single_txn("2024/01/15"), datetime.date(2024, 1, 15))

    def test_dot_separator(self):
        """YYYY.MM.DD — dot separator."""
        self.assertEqual(self._single_txn("2024.01.15"), datetime.date(2024, 1, 15))

    def test_optional_leading_zeros(self):
        """YYYY.M.D — leading zeros omitted on month and day."""
        self.assertEqual(self._single_txn("2010.1.31"), datetime.date(2010, 1, 31))

    def test_year_omitted_slash(self):
        """M/DD — year omitted, inferred from default_year."""
        journal = parse_string(
            "1/31 Test\n"
            "    expenses:food  £10.00\n"
            "    assets:bank  -£10.00\n",
            default_year=2025,
        )
        self.assertEqual(journal.transactions[0].date, datetime.date(2025, 1, 31))

    def test_year_omitted_hyphen(self):
        """MM-DD — year omitted with hyphen separator."""
        journal = parse_string(
            "03-15 Test\n"
            "    expenses:food  £10.00\n"
            "    assets:bank  -£10.00\n",
            default_year=2024,
        )
        self.assertEqual(journal.transactions[0].date, datetime.date(2024, 3, 15))

    def test_year_omitted_defaults_to_current_year(self):
        """Year-omitted date with no default_year uses today's year."""
        journal = parse_string(
            "1/1 Test\n"
            "    expenses:food  £10.00\n"
            "    assets:bank  -£10.00\n",
        )
        expected_year = datetime.date.today().year
        self.assertEqual(journal.transactions[0].date.year, expected_year)

    def test_invalid_calendar_date_raises(self):
        """A syntactically valid but calendar-invalid date raises ParseError."""
        with self.assertRaises(ParseError):
            parse_string(
                "2024-13-01 Test\n"
                "    expenses:food  £10.00\n"
                "    assets:bank  -£10.00\n"
            )


# ---------------------------------------------------------------------------
# account directive
# ---------------------------------------------------------------------------

class TestAccountDirective(unittest.TestCase):
    def test_account_directive_stored(self):
        j = parse_string("account assets:bank\n")
        self.assertEqual(j.declared_accounts, ["assets:bank"])

    def test_multiple_account_directives(self):
        j = parse_string("account assets:bank\naccount income:salary\n")
        self.assertEqual(j.declared_accounts, ["assets:bank", "income:salary"])

    def test_account_inline_comment_stripped(self):
        j = parse_string("account assets:bank  ; checking account\n")
        self.assertEqual(j.declared_accounts, ["assets:bank"])

    def test_account_single_space_semicolon_in_name(self):
        # Single space before ';' → ';' is part of the name (no separator)
        j = parse_string("account a:b ; note\n")
        self.assertEqual(j.declared_accounts, ["a:b ; note"])

    def test_account_subdirectives_skipped(self):
        text = "account assets:bank\n    format something\n    ; a note\n"
        j = parse_string(text)
        # Only the account name is stored; subdirectives do not create extra entries
        self.assertEqual(j.declared_accounts, ["assets:bank"])

    def test_account_directive_inside_block_comment_ignored(self):
        text = "comment\naccount assets:bank\nend comment\n"
        j = parse_string(text)
        self.assertEqual(j.declared_accounts, [])

    def test_account_directive_does_not_affect_transactions(self):
        text = (
            "account assets:bank\n"
            "account income:salary\n"
            "\n"
            "2024-01-01 Pay\n"
            "    assets:bank  £10.00\n"
            "    income:salary  -£10.00\n"
        )
        j = parse_string(text)
        self.assertEqual(len(j.transactions), 1)
        self.assertEqual(j.declared_accounts, ["assets:bank", "income:salary"])


# ---------------------------------------------------------------------------
# commodity directive
# ---------------------------------------------------------------------------

class TestCommodityDirective(unittest.TestCase):
    def test_prefix_symbol(self):
        j = parse_string("commodity £1,000.00\n")
        self.assertEqual(j.declared_commodities, ["£"])

    def test_prefix_dollar(self):
        j = parse_string("commodity $1,000.00\n")
        self.assertEqual(j.declared_commodities, ["$"])

    def test_suffix_symbol(self):
        j = parse_string("commodity 1,000.00 EUR\n")
        self.assertEqual(j.declared_commodities, ["EUR"])

    def test_suffix_symbol_USD(self):
        j = parse_string("commodity 1.00 USD\n")
        self.assertEqual(j.declared_commodities, ["USD"])

    def test_bare_symbol_sigil(self):
        j = parse_string("commodity $\n")
        self.assertEqual(j.declared_commodities, ["$"])

    def test_bare_symbol_word(self):
        j = parse_string("commodity INR\n")
        self.assertEqual(j.declared_commodities, ["INR"])

    def test_quoted_symbol(self):
        j = parse_string('commodity "AAPL 2023"\n')
        self.assertEqual(j.declared_commodities, ["AAPL 2023"])

    def test_quoted_empty_symbol(self):
        j = parse_string('commodity ""\n')
        self.assertEqual(j.declared_commodities, [""])

    def test_no_symbol_numeric_only(self):
        # e.g. "commodity 1000." declares the no-symbol commodity
        j = parse_string("commodity 1000.\n")
        self.assertEqual(j.declared_commodities, [""])

    def test_inline_comment_stripped(self):
        j = parse_string("commodity $  ; US dollar\n")
        self.assertEqual(j.declared_commodities, ["$"])

    def test_format_subdirective_skipped(self):
        text = "commodity INR\n    format INR 1,00,00,000.00\n"
        j = parse_string(text)
        self.assertEqual(j.declared_commodities, ["INR"])

    def test_commodity_inside_block_comment_ignored(self):
        text = "comment\ncommodity £\nend comment\n"
        j = parse_string(text)
        self.assertEqual(j.declared_commodities, [])


# ---------------------------------------------------------------------------
# payee directive
# ---------------------------------------------------------------------------

class TestPayeeDirective(unittest.TestCase):
    def test_payee_stored(self):
        j = parse_string("payee Whole Foods\n")
        self.assertEqual(j.declared_payees, ["Whole Foods"])

    def test_payee_inline_comment_stripped(self):
        j = parse_string("payee Whole Foods  ; grocery store\n")
        self.assertEqual(j.declared_payees, ["Whole Foods"])

    def test_payee_single_space_semicolon_kept(self):
        # Single space before ';' → ';' is NOT the 2-space separator
        j = parse_string("payee Smith & Jones ; law firm\n")
        self.assertEqual(j.declared_payees, ["Smith & Jones ; law firm"])

    def test_payee_quoted_empty(self):
        j = parse_string('payee ""\n')
        self.assertEqual(j.declared_payees, [""])

    def test_payee_quoted_name(self):
        j = parse_string('payee "Smith & Co"\n')
        self.assertEqual(j.declared_payees, ["Smith & Co"])

    def test_payee_inside_block_comment_ignored(self):
        text = "comment\npayee Supermarket\nend comment\n"
        j = parse_string(text)
        self.assertEqual(j.declared_payees, [])

    def test_multiple_payees(self):
        j = parse_string("payee Shop A\npayee Shop B\n")
        self.assertEqual(j.declared_payees, ["Shop A", "Shop B"])


# ---------------------------------------------------------------------------
# tag directive
# ---------------------------------------------------------------------------

class TestTagDirective(unittest.TestCase):
    def test_tag_stored(self):
        j = parse_string("tag item-id\n")
        self.assertEqual(j.declared_tags, ["item-id"])

    def test_tag_inline_comment_stripped(self):
        j = parse_string("tag item-id  ; identifies purchase items\n")
        self.assertEqual(j.declared_tags, ["item-id"])

    def test_tag_single_space_semicolon_kept(self):
        # Single space before ';' is NOT the 2-space separator
        j = parse_string("tag weird;tag\n")
        self.assertEqual(j.declared_tags, ["weird;tag"])

    def test_tag_subdirective_skipped(self):
        text = "tag item-id\n    some subdirective\n"
        j = parse_string(text)
        self.assertEqual(j.declared_tags, ["item-id"])

    def test_multiple_tags(self):
        j = parse_string("tag receipt\ntag project\n")
        self.assertEqual(j.declared_tags, ["receipt", "project"])

    def test_tag_inside_block_comment_ignored(self):
        text = "comment\ntag should-be-ignored\nend comment\n"
        j = parse_string(text)
        self.assertEqual(j.declared_tags, [])


# ---------------------------------------------------------------------------
# decimal-mark directive
# ---------------------------------------------------------------------------

class TestDecimalMarkDirective(unittest.TestCase):
    def _simple_journal(self, amount_line: str) -> "Journal":
        text = (
            f"2024-01-01 Test\n"
            f"    assets  {amount_line}\n"
            f"    income  \n"
        )
        return parse_string(text)

    def test_default_period_decimal(self):
        j = parse_string("2024-01-01 T\n    a  £1,234.56\n    b\n")
        self.assertEqual(j.transactions[0].postings[0].amount.quantity, Decimal("1234.56"))

    def test_explicit_period_decimal(self):
        text = "decimal-mark .\n2024-01-01 T\n    a  £1,234.56\n    b\n"
        j = parse_string(text)
        self.assertEqual(j.transactions[0].postings[0].amount.quantity, Decimal("1234.56"))

    def test_comma_decimal_basic(self):
        text = "decimal-mark ,\n2024-01-01 T\n    a  £100,50\n    b\n"
        j = parse_string(text)
        self.assertEqual(j.transactions[0].postings[0].amount.quantity, Decimal("100.50"))

    def test_comma_decimal_with_thousands(self):
        text = "decimal-mark ,\n2024-01-01 T\n    a  £1.234,56\n    b\n"
        j = parse_string(text)
        self.assertEqual(j.transactions[0].postings[0].amount.quantity, Decimal("1234.56"))

    def test_comma_decimal_suffix_commodity(self):
        text = "decimal-mark ,\n2024-01-01 T\n    a  1.234,56 EUR\n    b\n"
        j = parse_string(text)
        p = j.transactions[0].postings[0]
        self.assertEqual(p.amount.quantity, Decimal("1234.56"))
        self.assertEqual(p.amount.commodity, "EUR")

    def test_comma_decimal_negative(self):
        text = "decimal-mark ,\n2024-01-01 T\n    a  £1,50\n    b  -£1,50\n"
        j = parse_string(text)
        self.assertEqual(j.transactions[0].postings[1].amount.quantity, Decimal("-1.50"))

    def test_decimal_mark_applies_from_directive_forward(self):
        # Postings before the directive use period-decimal, after use comma-decimal
        text = (
            "2024-01-01 Before\n"
            "    a  £1,234.56\n"
            "    b\n"
            "\n"
            "decimal-mark ,\n"
            "\n"
            "2024-01-02 After\n"
            "    a  £1.234,56\n"
            "    b\n"
        )
        j = parse_string(text)
        self.assertEqual(j.transactions[0].postings[0].amount.quantity, Decimal("1234.56"))
        self.assertEqual(j.transactions[1].postings[0].amount.quantity, Decimal("1234.56"))

    def test_invalid_decimal_mark_raises(self):
        from PyLedger.parser import ParseError
        with self.assertRaises(ParseError):
            parse_string("decimal-mark ;\n")

    def test_decimal_mark_inside_block_comment_ignored(self):
        # directive inside block comment must not change decimal_mark state
        text = (
            "comment\n"
            "decimal-mark ,\n"
            "end comment\n"
            "2024-01-01 T\n"
            "    a  £1,234.56\n"  # should still parse as period-decimal (default)
            "    b\n"
        )
        j = parse_string(text)
        self.assertEqual(j.transactions[0].postings[0].amount.quantity, Decimal("1234.56"))


if __name__ == "__main__":
    unittest.main()
