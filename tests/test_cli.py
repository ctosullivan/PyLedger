"""Tests for PyLedger.cli — -f/--file flag, _resolve_files, and multi-file loading."""

import os
import pathlib
import sys
import tempfile
import textwrap
import unittest
from io import StringIO
from unittest.mock import patch

from PyLedger.cli import _resolve_files, main

FIXTURES = pathlib.Path(__file__).parent / "fixtures"
SAMPLE_JOURNAL = FIXTURES / "sample.journal"

_SIMPLE_JOURNAL = textwrap.dedent("""\
    2024-01-01 Simple
        assets:bank  £10.00
        income:other  -£10.00
""")

_SIMPLE_JOURNAL_2 = textwrap.dedent("""\
    2024-02-01 Another
        assets:bank  £5.00
        income:other  -£5.00
""")


def _write_temp(content: str, suffix: str = ".journal") -> pathlib.Path:
    f = tempfile.NamedTemporaryFile(
        suffix=suffix, mode="w", encoding="utf-8", delete=False
    )
    f.write(content)
    f.close()
    return pathlib.Path(f.name)


class _FakeArgs:
    """Minimal stand-in for argparse.Namespace for _resolve_files tests."""

    def __init__(self, files=None, journal=None, command="stats"):
        self.files = files
        # journal is now a list (nargs="*") — default to empty list
        self.journal = journal if journal is not None else []
        self.command = command


class TestResolveFiles(unittest.TestCase):
    """Unit tests for the _resolve_files helper."""

    def test_files_flag_returned(self):
        args = _FakeArgs(files=["/a.journal", "/b.journal"])
        self.assertEqual(_resolve_files(args), ["/a.journal", "/b.journal"])

    def test_positional_returned(self):
        args = _FakeArgs(journal=["/a.journal"])
        self.assertEqual(_resolve_files(args), ["/a.journal"])

    def test_both_flags_raises(self):
        args = _FakeArgs(files=["/a.journal"], journal=["/b.journal"])
        with self.assertRaises(SystemExit) as ctx:
            _resolve_files(args)
        self.assertEqual(ctx.exception.code, 1)

    def test_env_ledger_file_used(self):
        args = _FakeArgs()
        with patch.dict(os.environ, {"LEDGER_FILE": "/env.journal"}, clear=False):
            result = _resolve_files(args)
        self.assertEqual(result, ["/env.journal"])

    def test_no_file_no_env_raises(self):
        args = _FakeArgs()
        with patch.dict(os.environ, {}, clear=True):
            # Patch Path.home() so ~/.hledger.journal won't accidentally exist
            with patch("PyLedger.cli.Path") as mock_path_cls:
                mock_home = mock_path_cls.home.return_value
                mock_home.__truediv__ = lambda self, other: mock_home
                mock_home.exists.return_value = False
                with self.assertRaises(SystemExit) as ctx:
                    _resolve_files(args)
        self.assertEqual(ctx.exception.code, 1)

    def test_env_takes_precedence_over_default(self):
        args = _FakeArgs()
        with patch.dict(os.environ, {"LEDGER_FILE": "/env.journal"}, clear=False):
            result = _resolve_files(args)
        self.assertEqual(result[0], "/env.journal")


class TestFileFlagCLI(unittest.TestCase):
    """Integration tests for the -f/--file flag via main()."""

    def test_f_flag_loads_journal(self):
        code = main(["-f", str(SAMPLE_JOURNAL), "stats"])
        self.assertEqual(code, 0)

    def test_f_flag_long_form(self):
        code = main(["--file", str(SAMPLE_JOURNAL), "stats"])
        self.assertEqual(code, 0)

    def test_positional_still_works(self):
        code = main(["stats", str(SAMPLE_JOURNAL)])
        self.assertEqual(code, 0)

    def test_f_flag_multiple_merges(self):
        tmp1 = _write_temp(_SIMPLE_JOURNAL)
        tmp2 = _write_temp(_SIMPLE_JOURNAL_2)
        try:
            buf = StringIO()
            with patch("sys.stdout", buf):
                code = main(["-f", str(tmp1), "-f", str(tmp2), "print"])
            self.assertEqual(code, 0)
            output = buf.getvalue()
            self.assertIn("Simple", output)
            self.assertIn("Another", output)
        finally:
            os.unlink(str(tmp1))
            os.unlink(str(tmp2))

    def test_f_flag_and_positional_errors(self):
        code = main(["-f", str(SAMPLE_JOURNAL), "stats", str(SAMPLE_JOURNAL)])
        self.assertEqual(code, 1)

    def test_f_flag_nonexistent_file_errors(self):
        code = main(["-f", "/no/such/file.journal", "stats"])
        self.assertEqual(code, 1)

    def test_f_flag_stdin(self):
        with patch("sys.stdin", StringIO(_SIMPLE_JOURNAL)):
            buf = StringIO()
            with patch("sys.stdout", buf):
                code = main(["-f", "-", "print"])
        self.assertEqual(code, 0)
        self.assertIn("Simple", buf.getvalue())

    def test_env_fallback_ledger_file(self):
        tmp = _write_temp(_SIMPLE_JOURNAL)
        try:
            with patch.dict(os.environ, {"LEDGER_FILE": str(tmp)}, clear=False):
                code = main(["stats"])
            self.assertEqual(code, 0)
        finally:
            os.unlink(str(tmp))

    def test_no_file_no_env_exits_with_message(self):
        with patch.dict(os.environ, {}, clear=True):
            with patch("PyLedger.cli.Path") as mock_path_cls:
                mock_home = mock_path_cls.home.return_value
                mock_home.__truediv__ = lambda self, other: mock_home
                mock_home.exists.return_value = False
                buf = StringIO()
                with patch("sys.stderr", buf):
                    code = main(["stats"])
        self.assertEqual(code, 1)
        self.assertIn("no journal file specified", buf.getvalue())


class TestFileFlagOutput(unittest.TestCase):
    """Verify output content when using -f flag."""

    def test_stats_source_file_reflects_f_flag(self):
        buf = StringIO()
        with patch("sys.stdout", buf):
            main(["-f", str(SAMPLE_JOURNAL), "stats"])
        output = buf.getvalue()
        self.assertIn("Main file", output)

    def test_multiple_f_included_files_summed(self):
        root = FIXTURES / "root_with_include.journal"
        buf = StringIO()
        with patch("sys.stdout", buf):
            main(["-f", str(SAMPLE_JOURNAL), "-f", str(root), "stats"])
        output = buf.getvalue()
        # root_with_include has 1 included file; sample has 0 → total 1
        self.assertIn("Included files      : 1", output)


if __name__ == "__main__":
    unittest.main()
