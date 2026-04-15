"""Journal file parser for PyLedger.

Converts raw .journal text into Journal/Transaction/Posting objects.
See docs/hledger-compatibility.md for the transaction block structure and
the list of supported format features.
"""

from __future__ import annotations

import datetime
import os
import re
from decimal import Decimal, InvalidOperation

from pyLedger.models import Amount, Journal, Posting, Transaction


class ParseError(ValueError):
    """Raised on malformed hledger journal input.

    Attributes:
        line_number: 1-based line number where the error was detected,
                     or None if not applicable.
    """

    def __init__(self, message: str, line_number: int | None = None) -> None:
        self.line_number = line_number
        location = f" (line {line_number})" if line_number is not None else ""
        super().__init__(f"{message}{location}")


# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

# Matches a transaction header line in hledger journal format.
#
# Purpose: extract date, optional status flag, optional transaction code,
#          description text, and optional inline comment from a single
#          non-indented line that begins a transaction block.
#
# Group breakdown:
#   (1) simple date             — captured as a raw string and passed to
#                                 _parse_simple_date; see _SIMPLE_DATE for detail.
#                                 Handles YYYY-MM-DD, YYYY/MM/DD, YYYY.MM.DD,
#                                 and year-omitted forms (M/DD, MM-DD, etc.);
#                                 leading zeros optional on month and day.
#   (2) [*!]?                  — status flag: '*' = cleared, '!' = pending;
#                                absent means uncleared
#   (3) (?:\(([^)]*)\))?       — transaction code in parentheses, e.g. (INV-42);
#                                outer parens consumed, only inner text captured;
#                                [^)]* prevents greedily crossing a closing paren
#   (4) .*?                    — description: lazy so the trailing comment anchor
#                                can match; stripped of surrounding whitespace
#                                after the match
#   (5) (?:\s*;\s*(.*))?       — inline comment following ';'; the ';' itself and
#                                surrounding spaces are consumed but not captured
#
# Edge cases:
#   - Description may be empty (e.g. "2024-01-01 *" with no text after the flag)
#   - Code may be absent even when a flag is present, and vice versa
#   - A bare ';' anywhere after the date is treated as the comment delimiter;
#     this matches hledger's own behaviour (first ';' ends the description)
#   - Mixed separators (e.g. "2024-01/15") are captured here without complaint;
#     _parse_simple_date accepts them since each separator pair is matched
#     independently
_TXN_HEADER = re.compile(
    r"^((?:\d{4}[-/.])?(?:\d{1,2})[-/.](?:\d{1,2}))"
    r"\s*([*!])?"
    r"\s*(?:\(([^)]*)\))?"
    r"\s*(.*?)"
    r"(?:\s*;\s*(.*))?$"
)

# Parses a simple date string captured by _TXN_HEADER into its year, month,
# and day components.
#
# Purpose: decompose a raw date token (any of the accepted formats) into
#          integer components so that datetime.date() can validate and
#          construct the final date object.
#
# Group breakdown:
#   (1) (\d{4})    — four-digit year; the entire (?:...) wrapper is optional,
#                    so this group is None when the year is omitted
#   [-/.]          — separator: hyphen, forward-slash, or dot; not captured
#   (2) (\d{1,2})  — month, 1–2 digits, leading zero optional
#   [-/.]          — separator (same character classes; mixing is tolerated)
#   (3) (\d{1,2})  — day of month, 1–2 digits, leading zero optional
#
# Edge cases:
#   - Year absent ("1/31", "01-31"): group 1 is None; caller supplies default_year
#   - Invalid calendar values ("2024-13-01"): regex matches but datetime.date()
#     raises ValueError, which _parse_simple_date converts to ParseError
#   - Dot separator ("2010.1.31"): matched by [-/.]; note this is unambiguous in
#     header context because amounts (which also use '.') are on indented lines
_SIMPLE_DATE = re.compile(
    r"^(?:(\d{4})[-/.])?(\d{1,2})[-/.](\d{1,2})$"
)

# Matches an hledger amount string in either prefix-symbol or suffix-symbol form.
#
# Purpose: parse the quantity and commodity out of an amount token that has
#          already been separated from the account name.  Supports both
#          '£30.00' (symbol before number) and '30.00 EUR' (symbol after number),
#          optional thousands-separator commas, and a leading minus sign.
#
# Group breakdown:
#   (1) (-?)                      — optional leading minus sign; always applied
#                                   to the quantity regardless of symbol position
#   (2) ([^\d,.\s-]*)             — prefix commodity: any run of characters that
#                                   are not digits, commas, dots, whitespace, or
#                                   minus; matches '£', '$', '€', etc.; empty
#                                   string when the commodity is a suffix
#   (3) ([\d,]+(?:\.\d+)?)        — numeric quantity: one or more digits/commas
#                                   followed by an optional decimal part; commas
#                                   are stripped before Decimal conversion
#   (4) ([A-Za-z][A-Za-z0-9]*)?   — suffix commodity: a letter-started alphanumeric
#                                   token (e.g. EUR, USD, AAPL); absent when the
#                                   commodity is a prefix symbol
#
# Edge cases:
#   - Exactly one of group 2 or group 4 must be non-empty; if both are empty
#     the caller raises ParseError (no commodity)
#   - A space between prefix symbol and quantity is allowed: '£ 30.00' matches
#     because \s* between groups 2 and 3 absorbs it
#   - Integer quantities ('£100') are valid; the decimal part is optional
#   - Negative suffix amounts ('-30.00 EUR'): the minus in group 1 precedes the
#     empty group 2, then the quantity in group 3, then EUR in group 4
_AMOUNT = re.compile(
    r"^(-?)"
    r"([^\d,.\s-]*)"
    r"\s*([\d,]+(?:\.\d+)?)"
    r"\s*([A-Za-z][A-Za-z0-9]*)?"
    r"$"
)


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _parse_simple_date(
    date_str: str, lineno: int, default_year: int
) -> datetime.date:
    """Parse a simple date string into a datetime.date.

    Accepts YYYY-MM-DD, YYYY/MM/DD, YYYY.MM.DD, and year-omitted forms such as
    M/DD or MM-DD. Leading zeros on month and day are optional. When the year is
    absent, default_year is used (typically the current calendar year).

    Raises:
        ParseError: if the string does not match the simple date pattern or the
                    resulting calendar date is invalid (e.g. month 13).
    """
    m = _SIMPLE_DATE.match(date_str)
    if not m:
        raise ParseError(f"invalid date {date_str!r}", lineno)
    year_str, month_str, day_str = m.groups()
    year = int(year_str) if year_str else default_year
    try:
        return datetime.date(year, int(month_str), int(day_str))
    except ValueError as exc:
        raise ParseError(f"invalid date {date_str!r}: {exc}", lineno)


def _parse_txn_header(line: str, lineno: int, default_year: int) -> Transaction:
    """Parse a transaction header line into a Transaction with no postings."""
    m = _TXN_HEADER.match(line)
    if not m:
        raise ParseError(f"invalid transaction header: {line!r}", lineno)

    date_str, flag, code, description, comment = m.groups()
    date = _parse_simple_date(date_str, lineno, default_year)

    return Transaction(
        date=date,
        description=(description or "").strip(),
        postings=[],
        cleared=(flag == "*"),
        pending=(flag == "!"),
        code=(code or "").strip(),
        comment=(comment or "").strip(),
    )


def _parse_amount(raw: str, lineno: int) -> Amount:
    """Parse a raw amount string into an Amount.

    Supports prefix commodity (£30.00), suffix commodity (30.00 EUR),
    negative amounts (-£5.00, -30.00 EUR), and thousands separators (1,234.56).
    """
    m = _AMOUNT.match(raw.strip())
    if not m:
        raise ParseError(f"invalid amount: {raw!r}", lineno)

    minus, prefix_sym, quantity_str, suffix_sym = m.groups()

    commodity = (prefix_sym or suffix_sym or "").strip()
    if not commodity:
        raise ParseError(f"amount has no commodity symbol: {raw!r}", lineno)

    # Strip thousands commas before converting
    quantity_clean = quantity_str.replace(",", "")
    try:
        quantity = Decimal(minus + quantity_clean)
    except InvalidOperation:
        raise ParseError(f"invalid numeric quantity in amount: {raw!r}", lineno)

    return Amount(quantity=quantity, commodity=commodity)


def _parse_posting(line: str, lineno: int) -> Posting:
    """Parse a single posting line (already stripped of leading whitespace).

    Splits on two-or-more whitespace to separate account from amount.
    If no amount token is present the posting is elided (amount=None).
    """
    # Purpose: split the posting line into (account, amount) on the first run
    #          of two or more whitespace characters.  hledger requires at least
    #          two spaces to separate account from amount so that account names
    #          containing single spaces (e.g. "expenses:fun money") are preserved.
    # Pattern: \s{2,}
    #   \s{2,} — two or more whitespace characters (spaces or tabs)
    #   maxsplit=1 ensures only the first such gap is used as the delimiter;
    #             any further double-spaces inside the amount are left intact
    # Edge cases:
    #   - A posting with no amount ("  assets:bank") produces a single-element
    #     list; the caller treats this as an elided amount (None)
    #   - An account name with a single internal space ("expenses:fun money  £5")
    #     is correctly split because the delimiter requires two spaces
    parts = re.split(r"\s{2,}", line, maxsplit=1)
    account = parts[0].strip()

    if not account:
        raise ParseError("posting has no account name", lineno)

    # Strip inline comment from the amount portion
    amount_raw = ""
    if len(parts) > 1:
        amount_part = parts[1]
        # Remove trailing ; comment
        comment_idx = amount_part.find(";")
        if comment_idx != -1:
            amount_part = amount_part[:comment_idx]
        amount_raw = amount_part.strip()

    if not amount_raw:
        return Posting(account=account, amount=None)

    return Posting(account=account, amount=_parse_amount(amount_raw, lineno))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_string(text: str, default_year: int | None = None) -> Journal:
    """Parse a journal from a string and return a Journal object.

    Uses a line-by-line state machine. A transaction block begins on any
    non-indented line whose first token is a simple date and ends on the first
    subsequent blank line, or at EOF.

    Accepted date formats: YYYY-MM-DD, YYYY/MM/DD, YYYY.MM.DD, and year-omitted
    forms such as M/DD or MM-DD. Leading zeros on month and day are optional.
    When the year is omitted from a date, default_year is used; if default_year
    is None it defaults to the current calendar year at parse time.

    Raises:
        ParseError: if the input is not valid hledger journal syntax.
    """
    if default_year is None:
        default_year = datetime.date.today().year

    transactions: list[Transaction] = []
    current_txn: Transaction | None = None
    in_block_comment = False

    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.rstrip()

        # --- Block comment mode ---
        #
        # Purpose: skip every line between a `comment` directive and its
        #          matching `end comment` directive (or EOF).
        #
        # `comment` and `end comment` are non-indented directives. The
        # `comment` keyword may be followed by an inline comment but must be
        # the first word on the line. `end comment` is matched after stripping
        # any surrounding whitespace to be lenient about trailing spaces.
        #
        # Edge cases:
        #   - A `comment` block that reaches EOF without `end comment` is
        #     silently accepted; the parser simply consumes the rest of the file
        #   - A `comment` directive encountered mid-transaction flushes the open
        #     transaction first, then enters block-comment mode
        #   - `end comment` outside a block comment falls through to the
        #     "silently skip" branch (no error raised)
        #   - Nested `comment` directives inside a block comment are ignored
        if in_block_comment:
            if line.strip() == "end comment":
                in_block_comment = False
            continue

        # --- Blank line: end the current block ---
        if not line.strip():
            if current_txn is not None:
                transactions.append(current_txn)
                current_txn = None
            continue

        # --- Comment-only line (whole-line or indented follow-on `;` / `#`) ---
        #
        # lstrip() is applied before the startswith test so that both
        # whole-line comments ("# note") and indented follow-on comment lines
        # ("    ; posting note") are caught here, before the posting-line
        # branch below.
        stripped = line.lstrip()
        if stripped.startswith(";") or stripped.startswith("#"):
            continue

        # --- Posting line (2+ leading spaces or tab) ---
        if line.startswith("  ") or line.startswith("\t"):
            if current_txn is None:
                raise ParseError("posting found outside a transaction block", lineno)
            posting = _parse_posting(stripped, lineno)
            # Enforce at-most-one elided amount per block
            if posting.amount is None:
                elided = [p for p in current_txn.postings if p.amount is None]
                if elided:
                    raise ParseError(
                        "a transaction block may have at most one elided amount", lineno
                    )
            current_txn.postings.append(posting)
            continue

        # --- Transaction header (non-indented line starting with a simple date) ---
        #
        # Purpose: quickly determine whether a non-indented line opens a new
        #          transaction block before handing off to _parse_txn_header.
        # Pattern: ^(?:\d{4}[-/.])?(?:\d{1,2})[-/.](?:\d{1,2})(?=[\s*!(]|$)
        #   ^                         — anchored to start of the rstripped line
        #   (?:\d{4}[-/.])?           — optional four-digit year + separator
        #   (?:\d{1,2})[-/.]          — month (1–2 digits) + separator
        #   (?:\d{1,2})               — day (1–2 digits)
        #   (?=[\s*!(]|$)             — lookahead: must be followed by whitespace,
        #                               a status flag, the start of a code, or
        #                               end-of-line; prevents matching bare numeric
        #                               expressions that aren't transaction dates
        # Edge cases:
        #   - "2024-13-45 Bad" passes this check but fails in _parse_simple_date
        #     when datetime.date() rejects the invalid calendar values
        #   - "1.5" without a trailing space/flag does NOT match (lookahead fails),
        #     preventing accidental collision with decimal amounts on directive lines
        if re.match(r"^(?:\d{4}[-/.])?(?:\d{1,2})[-/.](?:\d{1,2})(?=[\s*!(]|$)", line):
            if current_txn is not None:
                # No blank line between transactions — flush previous block
                transactions.append(current_txn)
            current_txn = _parse_txn_header(line, lineno, default_year)
            continue

        # --- Block comment start (`comment` directive) ---
        #
        # A non-indented line whose first whitespace-delimited token is exactly
        # "comment" opens a block comment. Anything after "comment" on the same
        # line is ignored (treated as inline commentary on the directive itself).
        # Any open transaction is flushed before entering block-comment mode so
        # that a `comment` block sitting between transactions is parsed cleanly.
        if not line[0:1].isspace() and line.split()[0] == "comment":
            if current_txn is not None:
                transactions.append(current_txn)
                current_txn = None
            in_block_comment = True
            continue

        # --- Any other non-indented line: silently skip (directives, etc.) ---

    # Flush final block if file ends without a trailing blank line
    if current_txn is not None:
        transactions.append(current_txn)

    return Journal(transactions=transactions)


_SUPPORTED_EXTENSIONS = {".journal", ".ledger"}


def parse_file(path: str | os.PathLike) -> Journal:
    """Read a .journal or .ledger file from disk and return a Journal object.

    Supported extensions: .journal, .ledger
    See docs/hledger-compatibility.md for the full format support matrix.

    Raises:
        FileNotFoundError: if the path does not exist.
        ParseError: if the file extension is not supported, or if the file
                    contents are not valid hledger journal syntax.
    """
    path = os.fspath(path)
    _, ext = os.path.splitext(path)
    if ext.lower() not in _SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(_SUPPORTED_EXTENSIONS))
        raise ParseError(
            f"unsupported file format {ext!r} — PyLedger accepts: {supported}"
        )
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    journal = parse_string(text)
    journal.source_file = path
    return journal
