#!/usr/bin/env python3
"""Deprecated compatibility wrapper for ``promptrecon hook install``."""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from promptrecon.cli import main  # noqa: E402

if __name__ == "__main__":
    main(["hook", "install"])
