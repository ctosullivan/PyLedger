"""Command-line interface for PyLedger.

Parses arguments, loads the journal, calls reports, and formats output.
Entry point: main() — wired to `pyLedger` via pyproject.toml.
"""

from __future__ import annotations

import argparse
import contextlib
import sys
import time

# Captured as early as possible so elapsed time includes import overhead.
_PROGRAM_START = time.perf_counter()

from PyLedger import __version__


COMMANDS = ("balance", "register", "accounts", "print", "stats")


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="PyLedger",
        description="Plain-text accounting (hledger-compatible)",
    )
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    p.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show more detailed output (stats: commodity names)",
    )
    p.add_argument(
        "-1",
        dest="one_line",
        action="store_true",
        help="Show a single tab-separated line of output (stats only)",
    )
    p.add_argument(
        "-o", "--output-file",
        metavar="FILE",
        help="Write output to FILE instead of stdout",
    )
    p.add_argument(
        "command",
        choices=COMMANDS,
        help=f"Report to run: {', '.join(COMMANDS)}",
    )
    p.add_argument("journal", help="Path to the .journal file")
    return p


def main(argv: list[str] | None = None) -> int:
    """Entry point for the pyLedger CLI.

    Args:
        argv: Argument list (defaults to sys.argv[1:] when None).

    Returns:
        Exit code (0 = success, 1 = error).
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        from PyLedger.loader import load_journal
        journal = load_journal(args.journal)
    except FileNotFoundError:
        print(f"pyLedger: file not found: {args.journal}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"pyLedger: {exc}", file=sys.stderr)
        return 1

    outfile = None
    if args.output_file:
        try:
            outfile = open(args.output_file, "w", encoding="utf-8")
        except OSError as exc:
            print(f"pyLedger: cannot open output file: {exc}", file=sys.stderr)
            return 1

    try:
        import PyLedger.reports as reports

        with contextlib.redirect_stdout(outfile) if outfile else contextlib.nullcontext():
            if args.command == "balance":
                result = reports.balance(journal)
                for account, bal in sorted(result.items()):
                    print(f"  {bal:>12}  {account}")

            elif args.command == "register":
                rows = reports.register(journal)
                for row in rows:
                    print(
                        f"  {row.date}  {row.description:<30}  "
                        f"{row.account:<30}  {row.amount.quantity:>10} {row.amount.commodity}"
                    )

            elif args.command == "accounts":
                for name in reports.accounts(journal):
                    print(name)

            elif args.command == "print":
                for txn in journal.transactions:
                    flag = " * " if txn.cleared else " ! " if txn.pending else " "
                    print(f"{txn.date}{flag}{txn.description}")
                    for posting in txn.postings:
                        if posting.amount:
                            print(
                                f"    {posting.account:<40}"
                                f"  {posting.amount.commodity}{posting.amount.quantity}"
                            )
                        else:
                            print(f"    {posting.account}")
                    print()

            elif args.command == "stats":
                s = reports.stats(journal)
                elapsed = time.perf_counter() - _PROGRAM_START
                txns_per_s = s.transaction_count / elapsed if elapsed > 0 else 0.0

                span_str = (
                    f"{s.date_range[0]} to {s.date_range[1]} ({s.txns_span_days} days)"
                    if s.date_range else "(none)"
                )
                last_str = (
                    f"{s.last_txn_date} ({s.last_txn_days_ago} days ago)"
                    if s.last_txn_date else "(none)"
                )
                commodity_str = (
                    f"{s.commodity_count} ({', '.join(s.commodities)})"
                    if args.verbose and s.commodities else str(s.commodity_count)
                )

                elapsed_str = f"{elapsed:.2f}" if elapsed >= 0.01 else f"{elapsed:.3f}"
                if args.one_line:
                    print("\t".join([
                        __version__,
                        s.source_file or "(none)",
                        f"{elapsed_str} s elapsed",
                        f"{txns_per_s:.0f} txns/s",
                    ]))
                else:
                    print(f"Main file           : {s.source_file or '(none)'}")
                    print(f"Included files      : {s.included_files}")
                    print(f"Txns span           : {span_str}")
                    print(f"Last txn            : {last_str}")
                    print(f"Txns                : {s.transaction_count} ({s.txns_per_day:.1f} per day)")
                    print(f"Txns last 30 days   : {s.txns_last_30_days} ({s.txns_per_day_last_30:.1f} per day)")
                    print(f"Txns last 7 days    : {s.txns_last_7_days} ({s.txns_per_day_last_7:.1f} per day)")
                    print(f"Payees/descriptions : {s.payee_count}")
                    print(f"Accounts            : {s.account_count} (depth {s.account_depth})")
                    print(f"Commodities         : {commodity_str}")
                    print(f"Market prices       : {s.price_count}")
                    print(f"Runtime stats       : {elapsed_str} s elapsed, {txns_per_s:.0f} txns/s")

    except NotImplementedError:
        print(
            f"pyLedger: '{args.command}' is not yet implemented",
            file=sys.stderr,
        )
        return 1
    except Exception as exc:
        print(f"pyLedger: {exc}", file=sys.stderr)
        return 1
    finally:
        if outfile:
            outfile.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
