"""0.x compatibility adapter for built-in rules."""

from __future__ import annotations

import re

from .defaults import builtin_rules

RULE = {
    rule.id: {
        "description": rule.description,
        "regex": rule.pattern,
        "risk_score": {"low": 2.0, "medium": 5.0, "high": 8.0, "critical": 10.0}[rule.severity.value],
    }
    for rule in builtin_rules()
}


def load_builtin_rules():
    """Return the legacy dictionary shape used by 0.x integrations."""
    return {name: {**data, "regex": re.compile(data["regex"], re.IGNORECASE | re.MULTILINE)} for name, data in RULE.items()}
