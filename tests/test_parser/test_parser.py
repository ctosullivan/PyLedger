"""Tests for PyLedger.parser — core transaction and amount parsing."""

import datetime
import os
import pathlib
import unittest
from decimal import Decimal

from PyLedger.models import Amount, Journal, Posting, Transaction
from PyLedger.parser import ParseError, parse_string, parse_string_lenient, resolve_elision

FIXTURES = os.path.join(os.path.dirname(__file__), "..", "fixtures")
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
        assert amount is not None
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
        assert amount is not None
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
        assert amount is not None
        self.assertEqual(amount.quantity, Decimal("-5.00"))
        self.assertEqual(amount.commodity, "£")

    def test_negative_suffix(self):
        journal = parse_string(
            "2024-01-10 Refund\n"
            "    assets:bank  -30.00 EUR\n"
            "    expenses:food  30.00 EUR\n"
        )
        amount = journal.transactions[0].postings[0].amount
        assert amount is not None
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
        assert amount is not None
        self.assertEqual(amount.quantity, Decimal("1234.56"))
        self.assertEqual(amount.commodity, "£")


class TestTrailingDecimal(unittest.TestCase):
    """Test 7b: trailing decimal point with no fractional digits ($1,000.)."""

    def test_trailing_decimal_period(self):
        """Amount with trailing period and no fractional digits is valid."""
        journal = parse_string(
            "2024-01-05 Large transfer\n"
            "    assets:bank  $1,350,000.\n"
            "    income:salary  -$1,350,000.\n"
        )
        amount = journal.transactions[0].postings[0].amount
        assert amount is not None
        self.assertEqual(amount.quantity, Decimal("1350000"))
        self.assertEqual(amount.commodity, "$")

    def test_trailing_decimal_comma_mode(self):
        """Amount with trailing comma (comma-decimal mode) and no fractional digits is valid."""
        journal = parse_string(
            "decimal-mark ,\n"
            "2024-01-05 Large transfer\n"
            "    assets:bank  1.350.000, EUR\n"
            "    income:salary  -1.350.000, EUR\n"
        )
        amount = journal.transactions[0].postings[0].amount
        assert amount is not None
        self.assertEqual(amount.quantity, Decimal("1350000"))
        self.assertEqual(amount.commodity, "EUR")


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
# resolve_elision()
# ---------------------------------------------------------------------------

def _make_txn(postings: list[tuple[str, str | None]]) -> Transaction:
    """Build a Transaction with simple postings for resolve_elision tests."""
    ps = []
    for acct, amt_str in postings:
        if amt_str is None:
            ps.append(Posting(account=acct, source_line=1))
        else:
            neg = amt_str.startswith("-")
            inner = amt_str.lstrip("-")
            if inner and not inner[0].isdigit():
                # Symbol-prefixed: e.g. "£10.00" or "-£10.00"
                for i, ch in enumerate(inner):
                    if ch.isdigit():
                        sym = inner[:i]
                        qty_s = inner[i:]
                        break
                else:
                    sym = inner
                    qty_s = "0"
                qty = Decimal(qty_s) * (-1 if neg else 1)
            else:
                # Post-fix symbol: e.g. "20.00 EUR" or "5.00"
                parts = amt_str.split()
                qty = Decimal(parts[0])
                sym = parts[1] if len(parts) > 1 else ""
            ps.append(Posting(account=acct, amount=Amount(qty, sym), source_line=1))
    import datetime as _dt
    return Transaction(date=_dt.date(2024, 1, 1), description="Test", postings=ps)


class TestResolveElision(unittest.TestCase):
    """Tests for resolve_elision()."""

    def test_no_elided_returns_postings_unchanged(self):
        txn = _make_txn([("assets", "£10.00"), ("income", "-£10.00")])
        result = resolve_elision(txn)
        self.assertEqual(len(result), 2)
        self.assertFalse(any(p.inferred for p in result))

    def test_single_elided_single_commodity_infers_correct_amount(self):
        # assets £10 + income £-10 → elided should get £0... wait:
        # income:salary has elided amount; given = assets:bank £3000
        # inferred = -£3000 for income:salary
        txn = _make_txn([("assets:bank", "£3000.00"), ("income:salary", None)])
        result = resolve_elision(txn)
        self.assertEqual(len(result), 2)
        elided_resolved = next(p for p in result if p.account == "income:salary")
        self.assertEqual(elided_resolved.amount, Amount(Decimal("-3000.00"), "£"))
        self.assertTrue(elided_resolved.inferred)

    def test_single_elided_two_commodities_produces_two_postings(self):
        txn = _make_txn([("a", "£10.00"), ("b", "$5.00"), ("equity", None)])
        result = resolve_elision(txn)
        # equity should become 2 postings: one for £, one for $
        self.assertEqual(len(result), 4)
        inferred = [p for p in result if p.inferred]
        self.assertEqual(len(inferred), 2)
        commodities = {p.amount.commodity for p in inferred}
        self.assertEqual(commodities, {"£", "$"})

    def test_inferred_posting_has_inferred_true(self):
        txn = _make_txn([("a", "£10.00"), ("equity", None)])
        result = resolve_elision(txn)
        inferred = [p for p in result if p.inferred]
        self.assertEqual(len(inferred), 1)
        self.assertTrue(inferred[0].inferred)

    def test_non_elided_postings_have_inferred_false(self):
        txn = _make_txn([("a", "£10.00"), ("equity", None)])
        result = resolve_elision(txn)
        non_inferred = [p for p in result if not p.inferred]
        self.assertEqual(len(non_inferred), 1)
        self.assertFalse(non_inferred[0].inferred)

    def test_inferred_amounts_are_negations(self):
        txn = _make_txn([("a", "£10.00"), ("b", "$5.00"), ("equity", None)])
        result = resolve_elision(txn)
        inferred = sorted([p for p in result if p.inferred],
                          key=lambda p: p.amount.commodity)
        # Sorted alphabetically: $, £
        self.assertEqual(inferred[0].amount, Amount(Decimal("-5.00"), "$"))
        self.assertEqual(inferred[1].amount, Amount(Decimal("-10.00"), "£"))

    def test_commodity_sort_order(self):
        txn = _make_txn([("a", "£10.00"), ("b", "$5.00"),
                          ("c", "20.00 EUR"), ("equity", None)])
        result = resolve_elision(txn)
        inferred = [p for p in result if p.inferred]
        self.assertEqual(
            [p.amount.commodity for p in inferred],
            sorted(["EUR", "$", "£"]),
        )

    def test_elided_position_preserved_in_middle(self):
        txn = _make_txn([("a", "£10.00"), ("equity", None), ("b", "-£10.00")])
        result = resolve_elision(txn)
        # equity (index 1) gets replaced; a stays at 0, b stays at last
        self.assertEqual(result[0].account, "a")
        self.assertEqual(result[-1].account, "b")
        middle = result[1]
        self.assertEqual(middle.account, "equity")
        self.assertTrue(middle.inferred)

    def test_two_elided_returns_unchanged(self):
        txn = _make_txn([("a", "£10.00"), ("x", None), ("y", None)])
        result = resolve_elision(txn)
        # 2 elided → unchanged
        self.assertEqual(len(result), 3)
        self.assertFalse(any(p.inferred for p in result))

    def test_empty_given_returns_unchanged(self):
        txn = _make_txn([("equity", None)])
        result = resolve_elision(txn)
        self.assertEqual(len(result), 1)
        self.assertFalse(result[0].inferred)

    def test_inferred_posting_inherits_source_line(self):
        txn = _make_txn([("a", "£10.00"), ("equity", None)])
        # source_line is set to 1 by _make_txn for all postings
        result = resolve_elision(txn)
        inferred = next(p for p in result if p.inferred)
        self.assertEqual(inferred.source_line, 1)


# ---------------------------------------------------------------------------
# parse_string_lenient()
# ---------------------------------------------------------------------------

class TestParseStringLenient(unittest.TestCase):
    """Tests for parse_string_lenient()."""

    def test_valid_journal_returns_no_errors(self):
        text = "2024-01-01 Test\n    assets  £10\n    income  -£10\n"
        journal, errors = parse_string_lenient(text)
        self.assertEqual(errors, [])
        self.assertEqual(len(journal.transactions), 1)

    def test_lenient_never_raises(self):
        for bad_input in [
            "not a journal at all",
            "2024-01-01 Test\n    bad amount !!!\n",
            "\x00\xff garbage",
            "2024-13-45 Invalid date\n    assets £10\n",
            "    indented with no block",
        ]:
            try:
                journal, errors = parse_string_lenient(bad_input)
            except Exception as exc:
                self.fail(f"parse_string_lenient raised {exc!r} for input {bad_input!r}")

    def test_malformed_txn_discarded_valid_txn_kept(self):
        text = (
            "2024-01-01 Good\n"
            "    assets  £10\n"
            "    income  -£10\n"
            "\n"
            "2024-01-02 Bad\n"
            "    assets  NOT_AN_AMOUNT!!!\n"
            "\n"
            "2024-01-03 Also good\n"
            "    assets  £5\n"
            "    income  -£5\n"
        )
        journal, errors = parse_string_lenient(text)
        self.assertEqual(len(journal.transactions), 2)
        self.assertEqual(len(errors), 1)

    def test_recovery_continues_after_error(self):
        text = (
            "2024-01-01 Valid first\n"
            "    a  £10\n"
            "    b  -£10\n"
            "\n"
            "2024-13-01 Bad date\n"
            "    a  £5\n"
            "    b  -£5\n"
            "\n"
            "2024-03-01 Valid last\n"
            "    a  £20\n"
            "    b  -£20\n"
        )
        journal, errors = parse_string_lenient(text)
        self.assertEqual(len(errors), 1)
        self.assertEqual(len(journal.transactions), 2)
        self.assertEqual(journal.transactions[0].description, "Valid first")
        self.assertEqual(journal.transactions[1].description, "Valid last")

    def test_posting_outside_block_caught_leniently(self):
        text = "    orphan posting  £10\n\n2024-01-01 Valid\n    a  £5\n    b  -£5\n"
        journal, errors = parse_string_lenient(text)
        self.assertEqual(len(errors), 1)
        self.assertIn("posting found outside", str(errors[0]))
        self.assertEqual(len(journal.transactions), 1)

    def test_multiple_elided_in_one_txn_discarded(self):
        text = (
            "2024-01-01 Bad elision\n"
            "    a  £10\n"
            "    x\n"
            "    y\n"
            "\n"
            "2024-02-01 Good\n"
            "    a  £5\n"
            "    b  -£5\n"
        )
        journal, errors = parse_string_lenient(text)
        self.assertEqual(len(errors), 1)
        self.assertIn("at most one elided", str(errors[0]))
        self.assertEqual(len(journal.transactions), 1)
        self.assertEqual(journal.transactions[0].description, "Good")

    def test_errors_have_line_numbers(self):
        text = "2024-13-01 Bad\n    a £10\n    b -£10\n"
        _, errors = parse_string_lenient(text)
        self.assertEqual(len(errors), 1)
        self.assertIsNotNone(errors[0].line_number)

    def test_empty_string_returns_empty_journal(self):
        journal, errors = parse_string_lenient("")
        self.assertEqual(errors, [])
        self.assertEqual(len(journal.transactions), 0)

    def test_valid_journal_same_result_as_strict(self):
        text = (
            "2024-01-01 Opening\n"
            "    assets:bank  £1000.00\n"
            "    equity:opening\n"
            "\n"
        )
        strict = parse_string(text, default_year=2024)
        lenient, errors = parse_string_lenient(text, default_year=2024)
        self.assertEqual(errors, [])
        self.assertEqual(len(lenient.transactions), len(strict.transactions))

    def test_bad_txn_followed_directly_by_good_without_blank(self):
        # Two transactions with no blank line; first has a bad amount.
        text = (
            "2024-01-01 Bad\n"
            "    a  NOT_VALID\n"
            "2024-01-02 Good\n"
            "    a  £5\n"
            "    b  -£5\n"
        )
        journal, errors = parse_string_lenient(text)
        self.assertGreaterEqual(len(errors), 1)
        good = [t for t in journal.transactions if t.description == "Good"]
        self.assertEqual(len(good), 1)


if __name__ == "__main__":
    unittest.main()
