"""PyLedger: a Python implementation of the hledger plain-text accounting tool."""

from PyLedger.parser import parse_file as load

__version__ = "0.1.0"
__all__ = ["load", "__version__"]
