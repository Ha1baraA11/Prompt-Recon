"""TOML configuration and data-only custom rules."""

from __future__ import annotations

import importlib
import re
from dataclasses import dataclass
from pathlib import Path

try:
    import tomllib  # type: ignore[import-not-found]
except ModuleNotFoundError:  # pragma: no cover - Python 3.10
    tomllib = importlib.import_module("tomli")

from .models import Rule, Severity


@dataclass(frozen=True)
class Config:
    excludes: tuple[str, ...] = ()
    disabled_rules: frozenset[str] = frozenset()
    rules: tuple[Rule, ...] = ()
    max_file_size: int = 2 * 1024 * 1024


def load_config(path: Path | None) -> Config:
    if path is None or not path.exists():
        return Config()
    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise ValueError(f"invalid config {path}: {exc}") from exc
    scan = raw.get("scan", {})
    if not isinstance(scan, dict):
        raise ValueError("[scan] must be a table")
    excludes = scan.get("exclude", [])
    disabled = scan.get("disable_rules", [])
    max_file_size = scan.get("max_file_size", 2 * 1024 * 1024)
    if not isinstance(excludes, list) or not all(isinstance(item, str) for item in excludes):
        raise ValueError("scan.exclude must be a list of strings")
    if not isinstance(disabled, list) or not all(isinstance(item, str) for item in disabled):
        raise ValueError("scan.disable_rules must be a list of strings")
    if not isinstance(max_file_size, int) or max_file_size <= 0:
        raise ValueError("scan.max_file_size must be a positive integer")
    rules: list[Rule] = []
    for raw_rule in raw.get("rule", []):
        if not isinstance(raw_rule, dict):
            raise ValueError("each [[rule]] must be a table")
        try:
            severity = Severity(raw_rule.get("severity", "medium"))
            rule = Rule(
                id=raw_rule["id"], description=raw_rule["description"], pattern=raw_rule["pattern"],
                severity=severity, confidence=float(raw_rule.get("confidence", 0.8)),
                secret_group=raw_rule.get("secret_group"),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"invalid custom rule: {exc}") from exc
        try:
            re.compile(rule.pattern, re.IGNORECASE | re.MULTILINE)
        except re.error as exc:
            raise ValueError(f"invalid pattern for {rule.id}: {exc}") from exc
        rules.append(rule)
    return Config(tuple(excludes), frozenset(disabled), tuple(rules), max_file_size)
