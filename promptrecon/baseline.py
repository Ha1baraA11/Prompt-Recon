"""Versioned, non-plaintext baseline support."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .models import Finding

BASELINE_VERSION = 1


@dataclass(frozen=True)
class Baseline:
    entries: frozenset[str]

    def contains(self, finding: Finding) -> bool:
        return finding.fingerprint in self.entries


def load_baseline(path: Path | None) -> Baseline:
    if path is None or not path.exists():
        return Baseline(frozenset())
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid baseline {path}: {exc}") from exc
    if payload.get("version") != BASELINE_VERSION or not isinstance(payload.get("entries"), list):
        raise ValueError(f"unsupported baseline format: {path}")
    entries = payload["entries"]
    if not all(isinstance(entry, str) and len(entry) == 64 for entry in entries):
        raise ValueError(f"invalid baseline fingerprints: {path}")
    return Baseline(frozenset(entries))


def write_baseline(path: Path, findings: list[Finding], *, force: bool = False) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"baseline already exists: {path}; use --force to replace it")
    payload = {
        "version": BASELINE_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "entries": sorted({finding.fingerprint for finding in findings}),
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
