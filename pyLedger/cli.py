"""Command-line interface for PyLedger.

Parses arguments, loads the journal, calls reports, and formats output.
Entry point: main() — wired to `pyLedger` via pyproject.toml.
"""

from __future__ import annotations

import argparse
import sys

from PyLedger import __version__


COMMANDS = ("balance", "register", "accounts", "print", "stats")


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="pyLedger",
        description="Plain-text accounting (hledger-compatible)",
    )
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
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
        from PyLedger.parser import parse_file
        journal = parse_file(args.journal)
    except FileNotFoundError:
        print(f"pyLedger: file not found: {args.journal}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"pyLedger: {exc}", file=sys.stderr)
        return 1

    try:
        import PyLedger.reports as reports

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
            print(f"Main file           : {s.source_file or '(none)'}")
            print(f"Transactions        : {s.transaction_count}")
            print(f"Accounts            : {s.account_count}")
            if s.date_range:
                print(f"Date range          : {s.date_range[0]} to {s.date_range[1]}")
            print(f"Commodities         : {s.commodity_count}")

    except NotImplementedError:
        print(
            f"pyLedger: '{args.command}' is not yet implemented",
            file=sys.stderr,
        )
        return 1
    except Exception as exc:
        print(f"hledger-py: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
