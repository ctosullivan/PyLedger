"""Journal file parser for PyLedger.

Converts raw .journal text into Journal/Transaction/Posting objects.
See docs/hledger-compatibility.md for the transaction block structure and
the list of supported format features.
"""

from __future__ import annotations

import datetime
import re
from decimal import Decimal, InvalidOperation

from PyLedger.models import Amount, Journal, Posting, Transaction


# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

# Matches the two-or-more-space+semicolon comment separator used in directives.
#
# Purpose: split directive lines on the boundary between directive body and
#          inline comment, per hledger's rule that a single space may appear
#          inside a body value (e.g. an account name like "expenses:fun money")
#          but two or more spaces before a semicolon always begin a comment.
#
# Pattern: \s{2,};
#   \s{2,} — two or more whitespace characters (spaces or tabs)
#   ;      — the semicolon that opens the comment
#
# Edge cases:
#   - A single space before ';' is NOT a separator (the ';' belongs to the body)
#   - Only the FIRST match is used (re.split with maxsplit=1)
#   - Lines with no such pattern return the original body unchanged
_TWO_SPACE_SEP = re.compile(r"\s{2,};")


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
        source_line=lineno,
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


def _strip_directive_comment(raw: str) -> str:
    """Strip an inline comment from a directive body using the 2-space rule.

    Returns the body text before the first '  ;' sequence, stripped of
    surrounding whitespace. If no such sequence exists, returns the stripped
    input unchanged.
    """
    parts = _TWO_SPACE_SEP.split(raw, maxsplit=1)
    return parts[0].strip()


# Matches the numeric-and-optional-suffix part of a commodity sample amount.
#
# Purpose: extract the commodity symbol from a commodity directive whose body
#          is an amount token (e.g. "$1,000.00", "1,000.00 EUR", "1000. AAAA").
#          Also handles a bare symbol (e.g. "$", "INR") where no digits follow.
#
# Group breakdown:
#   (1) [^\d,.\s"-]*  — prefix symbol: any run of chars that are NOT digits,
#                       commas, dots, whitespace, quotes, or minus; captures
#                       '$', '£', '€', etc. when they lead the token; empty
#                       string when the commodity is a suffix token
#   (2) [\d,. ]*      — numeric portion: digits, commas, dots, and spaces
#                       (thousands-separated amounts can contain internal spaces)
#   (3) \s*([^\d,.\s]*)  — suffix symbol: any non-numeric run after the numeric
#                          portion, stripped of leading whitespace; captures
#                          'EUR', 'USD', 'AAPL' etc.; empty when prefix symbol
#
# Edge cases:
#   - "1000. AAAA"  → prefix='' numeric='1000. ' suffix='AAAA'
#   - "$1,000.00"   → prefix='$' numeric='1,000.00' suffix=''
#   - "$"           → prefix='$' numeric='' suffix=''
#   - "INR"         → prefix='' numeric='' suffix='INR'  (falls through to bare-symbol path)
#   - '1 000 000.0000' → internal spaces handled by numeric group
_COMMODITY_AMOUNT = re.compile(
    r'^([^\d,.\s"-]*)'
    r'([\d,. ]*)'
    r'\s*([^\d,.\s]*)'
    r'$'
)


def _extract_commodity_symbol(raw: str, lineno: int) -> str:
    """Extract the commodity symbol from a commodity directive body.

    Handles all hledger commodity directive forms:
      - Quoted:       "AAPL 2023"  →  AAPL 2023
      - Prefix+amt:   $1,000.00    →  $
      - Suffix+amt:   1,000.00 EUR →  EUR
      - Bare symbol:  INR          →  INR
      - Bare sigil:   $            →  $
      - Empty quoted: ""           →  (empty string, the no-symbol commodity)

    Raises:
        ParseError: if the body is empty after stripping.
    """
    body = raw.strip()
    if not body:
        raise ParseError("commodity directive has no symbol", lineno)

    # Quoted symbol: "AAPL 2023" or ""
    if body.startswith('"'):
        end = body.find('"', 1)
        if end == -1:
            raise ParseError(f"commodity directive has unterminated quoted symbol: {body!r}", lineno)
        return body[1:end]

    m = _COMMODITY_AMOUNT.match(body)
    if not m:
        raise ParseError(f"commodity directive: cannot parse symbol from {body!r}", lineno)

    prefix, numeric, suffix = m.group(1), m.group(2), m.group(3)

    if prefix:
        return prefix
    if suffix:
        return suffix.strip()
    # Numeric-only body (e.g. "1000.") — no symbol, no-symbol commodity
    return ""


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
        return Posting(account=account, amount=None, source_line=lineno)

    return Posting(account=account, amount=_parse_amount(amount_raw, lineno), source_line=lineno)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_string(text: str, default_year: int | None = None) -> Journal:
    """Parse a journal from a string and return a Journal object.

    Uses a line-by-line state machine. A transaction block begins on any
    non-indented line whose first token is a simple date and ends on the first
    subsequent blank line, or at EOF. Posting lines are conventionally indented
    with 2+ spaces or a tab, but indentation is not strictly required; any line
    inside an open transaction block that is not a blank line, comment, new
    transaction header, or recognised directive is treated as a posting.

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
    declared_accounts: list[str] = []
    declared_commodities: list[str] = []
    declared_payees: list[str] = []
    current_txn: Transaction | None = None
    in_block_comment = False
    in_subdirective = False  # True while consuming indented subdirective lines

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
            in_subdirective = False
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

        # --- Transaction header (non-indented line starting with a simple date) ---
        #
        # Purpose: quickly determine whether a non-indented line opens a new
        #          transaction block before handing off to _parse_txn_header.
        #          This check runs before posting detection so that a date-like
        #          token at column 0 is always treated as a new header, never as
        #          an un-indented posting inside an open block.
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
            in_subdirective = False
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
            in_subdirective = False
            in_block_comment = True
            continue

        # --- Subdirective lines (indented lines following account/commodity/payee) ---
        #
        # Purpose: consume Ledger-style indented subdirectives (e.g. "format …"
        #          below a commodity directive) without treating them as postings
        #          or raising ParseError.  in_subdirective is set to True whenever
        #          we finish processing an account/commodity/payee directive line;
        #          it is cleared on the next non-indented, non-blank line.
        #
        # Edge cases:
        #   - Blank lines above already clear in_subdirective via the blank-line
        #     branch (which sets current_txn=None and falls through; the next
        #     non-blank line will hit this check with in_subdirective still True
        #     only if there was no blank line — so blank lines naturally end the
        #     subdirective block)
        #   - An indented subdirective line that contains a valid posting syntax
        #     is still skipped here (subdirective wins); the containing file is
        #     expected to be well-formed per hledger conventions
        if in_subdirective:
            if line[0:1].isspace():
                continue  # consume indented subdirective silently
            in_subdirective = False
            # fall through to process this non-indented line normally

        # --- account directive ---
        #
        # Purpose: record a declared account name for strict-mode checking.
        #          The account name follows the keyword and may contain spaces
        #          and ';' characters; an inline comment is delimited by the
        #          first occurrence of two-or-more spaces followed by ';'.
        #          Indented lines that follow (Ledger-style subdirectives) are
        #          consumed silently via the in_subdirective flag.
        #
        # Edge cases:
        #   - "account a:b;c" (single space before ';') → name is "a:b;c"
        #   - "account a:b  ; note" → name is "a:b"
        #   - "accounts" does not match because \s+ requires whitespace after
        #     the exact word "account"
        if not line[0:1].isspace() and re.match(r"^account\s+", line):
            body = line[len("account"):].lstrip()
            account_name = _strip_directive_comment(body)
            if account_name:
                declared_accounts.append(account_name)
            in_subdirective = True
            continue

        # --- commodity directive ---
        #
        # Purpose: record a declared commodity symbol for strict-mode checking.
        #          Supports all hledger commodity directive forms: sample amount
        #          with prefix symbol ($1,000.00), sample amount with suffix
        #          symbol (1,000.00 EUR), bare symbol ($, INR), quoted symbol
        #          ("AAPL 2023"), empty-quoted no-symbol (""), and numeric-only
        #          (1000.) for format declarations.
        #
        # Edge cases:
        #   - "commodity" with no body raises ParseError (empty symbol)
        #   - Indented "format" subdirectives are consumed via in_subdirective
        #   - The same symbol may be declared more than once; deduplication is
        #     done at check time, not parse time
        if not line[0:1].isspace() and re.match(r"^commodity(\s|$)", line):
            rest = line[len("commodity"):].strip()
            body = _strip_directive_comment(rest)
            symbol = _extract_commodity_symbol(body, lineno)
            declared_commodities.append(symbol)
            in_subdirective = True
            continue

        # --- payee directive ---
        #
        # Purpose: record a declared payee name for strict-mode / payee checking.
        #          The payee name follows the keyword; inline comments are stripped
        #          with the 2-space rule. Quoted empty-string payee ("") is stored
        #          as the empty string. Tags in comments are ignored per the spec.
        #
        # Edge cases:
        #   - 'payee ""' → stored as "" (the no-payee sentinel)
        #   - "payee Whole Foods  ; comment" → "Whole Foods"
        #   - Indented Ledger-style subdirectives are consumed silently
        if not line[0:1].isspace() and re.match(r"^payee\s+", line):
            body = line[len("payee"):].lstrip()
            payee_name = _strip_directive_comment(body)
            # Unquote a quoted payee name (e.g. payee "" or payee "Smith & Co")
            if payee_name.startswith('"') and payee_name.endswith('"'):
                payee_name = payee_name[1:-1]
            declared_payees.append(payee_name)
            in_subdirective = True
            continue

        # --- Posting line ---
        #
        # Posting lines are conventionally written with 2+ leading spaces or a
        # tab, but indentation is not strictly required inside an open block.
        # Any line inside an open transaction block that has not been matched by
        # the blank-line, comment, transaction-header, or directive branches
        # above is treated as a posting.
        #
        # Indented lines (2+ spaces or tab) outside a transaction block still
        # raise ParseError — indentation unambiguously signals "this is a
        # posting", so encountering one with no open block is always an error.
        # Non-indented lines outside a block are silently skipped (directives,
        # stray text, etc.).
        if current_txn is None and (line.startswith("  ") or line.startswith("\t")):
            raise ParseError("posting found outside a transaction block", lineno)
        if current_txn is not None:
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

        # --- Any other line outside a transaction block: silently skip ---

    # Flush final block if file ends without a trailing blank line
    if current_txn is not None:
        transactions.append(current_txn)

    return Journal(
        transactions=transactions,
        declared_accounts=declared_accounts,
        declared_commodities=declared_commodities,
        declared_payees=declared_payees,
    )


