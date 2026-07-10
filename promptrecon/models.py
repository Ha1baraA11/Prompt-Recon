"""Public data models for Prompt-Recon."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class Rule:
    id: str
    description: str
    pattern: str
    severity: Severity
    confidence: float = 1.0
    secret_group: int | None = None


@dataclass(frozen=True)
class Finding:
    rule_id: str
    path: str
    line: int
    severity: Severity
    confidence: float
    redacted: str
    fingerprint: str
    source: str = "worktree"
    commit: str | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "rule_id": self.rule_id,
            "path": self.path,
            "line": self.line,
            "severity": self.severity.value,
            "confidence": self.confidence,
            "redacted": self.redacted,
            "fingerprint": self.fingerprint,
            "source": self.source,
            "commit": self.commit,
            "file": self.path,
            "rule_name": self.rule_id,
        }


@dataclass
class ScanResult:
    findings: list[Finding] = field(default_factory=list)
    scanned_files: int = 0
    skipped_files: int = 0
    suppressed_findings: int = 0
    errors: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ScanOptions:
    root: Path
    max_file_size: int = 2 * 1024 * 1024
    source: str = "worktree"
