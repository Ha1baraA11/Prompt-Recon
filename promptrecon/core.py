"""The offline scanning engine shared by every Prompt-Recon entry point."""

from __future__ import annotations

import hashlib
import math
import re
from collections.abc import Iterable
from pathlib import Path

import pathspec

from .baseline import Baseline
from .models import Finding, Rule, ScanOptions, ScanResult

DEFAULT_IGNORES = (".git/", ".venv/", "venv/", "__pycache__/", "node_modules/", ".promptrecon.baseline.json", ".promptrecon.toml")
PLACEHOLDER_VALUES = {"changeme", "example", "placeholder", "your_token_here", "not-a-real-secret"}


def redact(secret: str) -> str:
    """Produce a stable safe representation without revealing the secret."""
    digest = hashlib.sha256(secret.encode("utf-8", "surrogateescape")).hexdigest()[:12]
    return f"[REDACTED len={len(secret)} sha256={digest}]"


def fingerprint(rule_id: str, path: str, secret: str) -> str:
    material = "\0".join((rule_id, path, secret)).encode("utf-8", "surrogateescape")
    return hashlib.sha256(material).hexdigest()


def _entropy(value: str) -> float:
    if not value:
        return 0.0
    counts = {char: value.count(char) for char in set(value)}
    length = len(value)
    return -sum((count / length) * math.log2(count / length) for count in counts.values())


def _has_allowlist(content: str, line: int) -> bool:
    lines = content.splitlines()
    current = lines[line - 1] if line <= len(lines) else ""
    previous = lines[line - 2] if line > 1 else ""
    return "promptrecon: allow" in current.lower() or "promptrecon: allow-next-line" in previous.lower()


def _extract_secret(match: re.Match[str], rule: Rule) -> str:
    if rule.secret_group is not None:
        return match.group(rule.secret_group)
    return match.group(0)


def scan_content(content: str | bytes, rules: Iterable[Rule], path: str, *, source: str = "worktree", commit: str | None = None) -> list[Finding]:
    """Scan content without retaining raw secrets in returned findings."""
    if isinstance(content, bytes):
        content = content.decode("utf-8", errors="replace")
    findings: list[Finding] = []
    for rule in rules:
        expression = re.compile(rule.pattern, re.IGNORECASE | re.MULTILINE)
        for match in expression.finditer(content):
            secret = _extract_secret(match, rule)
            line = content.count("\n", 0, match.start()) + 1
            if rule.id == "high_entropy" and (_entropy(secret) < 4.2 or len(set(secret)) < 10):
                continue
            if _has_allowlist(content, line) or secret.lower() in PLACEHOLDER_VALUES or "${" in secret:
                continue
            findings.append(Finding(
                rule_id=rule.id, path=path, line=line, severity=rule.severity, confidence=rule.confidence,
                redacted=redact(secret), fingerprint=fingerprint(rule.id, path, secret), source=source, commit=commit,
            ))
    return findings


def is_scannable_bytes(raw: bytes, max_file_size: int) -> bool:
    return len(raw) <= max_file_size and b"\0" not in raw[:4096]


def build_ignore_spec(root: Path, patterns: Iterable[str]) -> pathspec.PathSpec:
    combined = list(DEFAULT_IGNORES) + list(patterns)
    for filename in (".gitignore", ".promptignore"):
        candidate = root / filename
        if candidate.is_file():
            combined.extend(candidate.read_text(encoding="utf-8", errors="replace").splitlines())
    return pathspec.PathSpec.from_lines("gitwildmatch", combined)


def scan_worktree(options: ScanOptions, rules: Iterable[Rule], ignore_spec: pathspec.PathSpec, baseline: Baseline | None = None) -> ScanResult:
    root = options.root.resolve()
    result = ScanResult()
    for file_path in root.rglob("*"):
        if file_path.is_symlink() or not file_path.is_file():
            continue
        relative = file_path.relative_to(root).as_posix()
        if ignore_spec.match_file(relative):
            result.skipped_files += 1
            continue
        try:
            raw = file_path.read_bytes()
        except OSError as exc:
            result.errors.append(f"cannot read {relative}: {exc}")
            continue
        if not is_scannable_bytes(raw, options.max_file_size):
            result.skipped_files += 1
            continue
        result.scanned_files += 1
        for finding in scan_content(raw, rules, relative, source=options.source):
            if baseline and baseline.contains(finding):
                result.suppressed_findings += 1
            else:
                result.findings.append(finding)
    return result


# Compatibility adapters retained for callers from 0.x.
def load_ignore_patterns(ignorefile: str = ".promptignore") -> list[str]:
    path = Path(ignorefile)
    if not path.exists():
        return list(DEFAULT_IGNORES)
    return list(DEFAULT_IGNORES) + path.read_text(encoding="utf-8", errors="replace").splitlines()


def should_ignore(filepath: str, patterns: list[str]) -> bool:
    candidate = Path(filepath).as_posix()
    basename = Path(filepath).name
    if any(pattern.rstrip("/") == basename for pattern in patterns):
        return True
    return pathspec.PathSpec.from_lines("gitwildmatch", patterns).match_file(candidate) or pathspec.PathSpec.from_lines("gitwildmatch", patterns).match_file(candidate.lstrip("/"))


def scan_file(filepath: str, rules: object, display_root: str | None = None) -> list[dict[str, object]]:
    """Deprecated dict-returning adapter for 0.x integrations."""
    from .rules.defaults import builtin_rules
    path = Path(filepath)
    root = Path(display_root) if display_root else path.parent
    try:
        raw = path.read_bytes()
    except OSError:
        return []
    active_rules = builtin_rules() if not isinstance(rules, tuple) else rules
    findings = scan_content(raw, active_rules, path.resolve().relative_to(root.resolve()).as_posix())
    return [finding.as_dict() for finding in findings]
