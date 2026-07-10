"""Git-backed scanners. They read blobs directly and never checkout revisions."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pathspec

from .baseline import Baseline
from .core import is_scannable_bytes, scan_content
from .models import Rule, ScanOptions, ScanResult


class GitError(RuntimeError):
    pass


def _git(root: Path, *args: str) -> bytes:
    result = subprocess.run(["git", *args], cwd=root, capture_output=True)
    if result.returncode:
        raise GitError(result.stderr.decode("utf-8", errors="replace").strip() or "git command failed")
    return result.stdout


def repo_root(root: Path) -> Path:
    return Path(_git(root, "rev-parse", "--show-toplevel").decode().strip())


def scan_staged(
    root: Path,
    options: ScanOptions,
    rules: tuple[Rule, ...],
    ignore_spec: pathspec.PathSpec,
    baseline: Baseline | None = None,
) -> ScanResult:
    root = repo_root(root)
    result = ScanResult()
    for encoded_path in _git(root, "diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z").split(b"\0"):
        if not encoded_path:
            continue
        path = encoded_path.decode("utf-8", errors="surrogateescape")
        if ignore_spec.match_file(path):
            result.skipped_files += 1
            continue
        raw = _git(root, "show", f":{path}")
        if not is_scannable_bytes(raw, options.max_file_size):
            result.skipped_files += 1
            continue
        result.scanned_files += 1
        for finding in scan_content(raw, rules, path, source="staged"):
            if baseline and baseline.contains(finding):
                result.suppressed_findings += 1
            else:
                result.findings.append(finding)
    return result


def scan_history(
    root: Path,
    options: ScanOptions,
    rules: tuple[Rule, ...],
    ignore_spec: pathspec.PathSpec,
    baseline: Baseline | None = None,
    ref: str = "--all",
) -> ScanResult:
    """Scan unique reachable blobs and resolve the introducing commit only on hits."""
    root = repo_root(root)
    result = ScanResult()
    seen: set[str] = set()
    for row in _git(root, "rev-list", "--objects", ref).decode("utf-8", errors="surrogateescape").splitlines():
        try:
            object_id, path = row.split(" ", 1)
        except ValueError:
            continue
        if object_id in seen or ignore_spec.match_file(path):
            continue
        seen.add(object_id)
        if _git(root, "cat-file", "-t", object_id).decode().strip() != "blob":
            continue
        raw = _git(root, "cat-file", "-p", object_id)
        if not is_scannable_bytes(raw, options.max_file_size):
            result.skipped_files += 1
            continue
        result.scanned_files += 1
        commits = (
            _git(root, "log", "--all", "--reverse", "--format=%H", f"--find-object={object_id}").decode().splitlines()
        )
        commit = commits[0] if commits else None
        for finding in scan_content(raw, rules, path, source="history", commit=commit):
            if baseline and baseline.contains(finding):
                result.suppressed_findings += 1
            else:
                result.findings.append(finding)
    return result
