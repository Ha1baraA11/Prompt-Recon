"""Compatibility module for Git's pre-commit hook."""

from promptrecon.cli import main

if __name__ == "__main__":
    main(["hook", "run"])
