"""Prompt-Recon's safe command-line interface."""

from __future__ import annotations

import argparse
import csv
import json
import os
import stat
import sys
import tempfile
import warnings
from pathlib import Path

from rich.console import Console
from rich.table import Table

from .baseline import load_baseline, write_baseline
from .config import load_config
from .core import build_ignore_spec, scan_worktree
from .git import GitError, repo_root, scan_history, scan_staged
from .models import Finding, ScanOptions, ScanResult
from .rules.defaults import builtin_rules


def _rules(config, rules_dir: str | None):
    if rules_dir:
        warnings.warn("--rules-dir executes Python and is deprecated; use [[rule]] in .promptrecon.toml", stacklevel=2)
    rules = list(builtin_rules()) + list(config.rules)
    return tuple(rule for rule in rules if rule.id not in config.disabled_rules)


def _render(result: ScanResult, fmt: str, output: str | None) -> None:
    records = [finding.as_dict() for finding in result.findings]
    if fmt == "console":
        console = Console()
        if not records:
            console.print("[green]Scan complete. No new secrets found.[/green]")
        else:
            table = Table(title="Prompt-Recon findings", show_lines=True)
            for column in ("Severity", "Rule", "File", "Line", "Value", "Source"):
                table.add_column(column)
            for finding in result.findings:
                table.add_row(finding.severity.value, finding.rule_id, finding.path, str(finding.line), finding.redacted, finding.source)
            console.print(table)
        console.print(f"Scanned {result.scanned_files} file(s); suppressed {result.suppressed_findings}; skipped {result.skipped_files}.")
        return
    if not output:
        raise ValueError(f"--output is required for {fmt}")
    destination = Path(output)
    if fmt == "jsonl":
        destination.write_text("".join(json.dumps(item, sort_keys=True) + "\n" for item in records), encoding="utf-8")
    elif fmt == "csv":
        with destination.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(Finding.__dataclass_fields__))
            writer.writeheader()
            writer.writerows(records)
    elif fmt == "markdown":
        rows = ["# Prompt-Recon Scan Report", "", f"**Total:** {len(records)}", "", "| Severity | Rule | File | Line | Value |", "| :--- | :--- | :--- | ---: | :--- |"]
        rows.extend(f"| {item['severity']} | {item['rule_id']} | {item['path']} | {item['line']} | {item['redacted']} |" for item in records)
        destination.write_text("\n".join(rows) + "\n", encoding="utf-8")
    elif fmt == "sarif":
        sarif_results = []
        for item in records:
            sarif_results.append({
                "ruleId": item["rule_id"],
                "level": item["severity"],
                "message": {"text": item["redacted"]},
                "locations": [{"physicalLocation": {"artifactLocation": {"uri": item["path"]}, "region": {"startLine": item["line"]}}}],
            })
        payload = {"version": "2.1.0", "$schema": "https://json.schemastore.org/sarif-2.1.0.json", "runs": [{"tool": {"driver": {"name": "Prompt-Recon"}}, "results": sarif_results}]}
        destination.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _scan(args: argparse.Namespace) -> ScanResult:
    root = Path(getattr(args, "directory", None) or getattr(args, "path", None) or ".").resolve()
    config_path = Path(args.config) if args.config else root / ".promptrecon.toml"
    config = load_config(config_path)
    baseline = load_baseline(Path(args.baseline)) if args.baseline else None
    options = ScanOptions(root=root, max_file_size=config.max_file_size, source="worktree")
    rules = _rules(config, args.rules_dir)
    ignore_spec = build_ignore_spec(root, list(config.excludes))
    if args.staged:
        return scan_staged(root, options, rules, ignore_spec, baseline)
    if args.history:
        return scan_history(root, options, rules, ignore_spec, baseline, args.ref)
    return scan_worktree(options, rules, ignore_spec, baseline)


def cmd_scan(args: argparse.Namespace) -> int:
    result = _scan(args)
    fmt = args.format
    output = args.output
    for legacy, legacy_format in ((args.jsonl, "jsonl"), (args.csv, "csv"), (args.md, "markdown")):
        if legacy:
            if args.format != "console" or args.output:
                raise ValueError("legacy output flags cannot be combined with --format/--output")
            fmt, output = legacy_format, legacy
    _render(result, fmt, output)
    return 1 if result.findings else 0


def cmd_baseline(args: argparse.Namespace) -> int:
    if args.action == "audit":
        baseline = load_baseline(Path(args.baseline))
        print(f"Baseline contains {len(baseline.entries)} fingerprint(s).")
        return 0
    result = _scan(args)
    write_baseline(Path(args.baseline), result.findings, force=args.force or args.action == "update")
    print(f"Wrote {len(result.findings)} fingerprint(s) to {args.baseline}.")
    return 0


def cmd_hook(args: argparse.Namespace) -> int:
    root = repo_root(Path.cwd())
    hook = root / ".git" / "hooks" / "pre-commit"
    marker = "# Managed by Prompt-Recon"
    if args.action == "run":
        namespace = argparse.Namespace(directory=str(root), config=None, baseline=None, staged=True, history=False, ref="--all", rules_dir=None, format="console", output=None, jsonl=None, csv=None, md=None)
        result = _scan(namespace)
        for finding in result.findings:
            print(f"[BLOCKED] {finding.path}: {finding.rule_id}:{finding.line} {finding.redacted}")
        if result.findings:
            print(f"\nBlocked {len({item.path for item in result.findings})} file(s). Use --no-verify to bypass.")
            return 1
        return 0
    if args.action == "uninstall":
        if hook.exists() and marker in hook.read_text(encoding="utf-8", errors="replace"):
            hook.unlink()
            print(f"Removed {hook}")
            return 0
        raise ValueError("no Prompt-Recon managed hook is installed")
    if hook.exists() and marker not in hook.read_text(encoding="utf-8", errors="replace") and not args.force:
        raise ValueError("an existing hook was not installed by Prompt-Recon; use --force only after backing it up")
    package_root = Path(__file__).resolve().parent.parent
    content = "\n".join(("#!/bin/sh", marker, f'export PYTHONPATH="{package_root}:$PYTHONPATH"', f'cd "{root}"', f'exec "{sys.executable}" -m promptrecon.hooks.pre_commit')) + "\n"
    hook.parent.mkdir(parents=True, exist_ok=True)
    hook.write_text(content, encoding="utf-8")
    hook.chmod(hook.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    print(f"Installed {hook}")
    return 0


def cmd_patch(args: argparse.Namespace) -> int:
    path = Path(args.file)
    env_var = args.env_var or "SECURE_PROMPT_KEY"
    import re
    if not re.fullmatch(r"[A-Z_][A-Z0-9_]*", env_var):
        raise ValueError("--env-var must be an uppercase environment variable name")
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    line_number = args.line
    if line_number is None and args.snippet:
        matches = [index for index, line in enumerate(lines, 1) if args.snippet in line]
        if len(matches) != 1:
            raise ValueError("legacy snippet must identify exactly one line; use --line instead")
        line_number = matches[0]
    if not line_number or line_number > len(lines):
        raise ValueError("--line must identify an existing Python assignment line")
    old = lines[line_number - 1]
    if not re.match(r"^\s*[A-Za-z_]\w*\s*=\s*(['\"]).*\1\s*(?:#.*)?(?:\n)?$", old):
        raise ValueError("only a single quoted Python assignment can be patched safely")
    replacement = re.sub(r"(=\s*)(['\"]).*\2", rf'\1os.environ["{env_var}"]', old)
    if "import os" not in "".join(lines) and "from os import" not in "".join(lines):
        replacement = "import os\n" + replacement
    print(f"--- {path}\n+++ {path}\n@@ line {line_number} @@\n-<redacted assignment>\n+{replacement.rstrip()}")
    if args.apply:
        target = "".join(lines[: line_number - 1]) + replacement + "".join(lines[line_number:])
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
            handle.write(target)
            temporary = Path(handle.name)
        os.replace(temporary, path)
        print("Applied safe replacement.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prompt-Recon: offline secrets scanner")
    sub = parser.add_subparsers(dest="command", required=True)
    scan = sub.add_parser("scan", help="scan a worktree, staging area, or Git history")
    scan.add_argument("path", nargs="?", default=".")
    scan.add_argument("-d", "--directory", dest="directory")
    mode = scan.add_mutually_exclusive_group()
    mode.add_argument("--staged", action="store_true")
    mode.add_argument("--history", action="store_true")
    scan.add_argument("--ref", default="--all")
    scan.add_argument("--config")
    scan.add_argument("--baseline")
    scan.add_argument("--rules-dir")
    scan.add_argument("--format", choices=("console", "jsonl", "csv", "markdown", "sarif"), default="console")
    scan.add_argument("--output")
    scan.add_argument("--jsonl")
    scan.add_argument("--csv")
    scan.add_argument("--md")
    baseline = sub.add_parser("baseline", help="create, update, or audit a baseline")
    baseline.add_argument("action", choices=("create", "update", "audit"))
    baseline.add_argument("path", nargs="?", default=".")
    baseline.add_argument("--baseline", default=".promptrecon.baseline.json")
    baseline.add_argument("--force", action="store_true")
    baseline.add_argument("--config")
    baseline.add_argument("--rules-dir")
    baseline.add_argument("--staged", action="store_true")
    baseline.add_argument("--history", action="store_true")
    baseline.add_argument("--ref", default="--all")
    hook = sub.add_parser("hook", help="manage a Git pre-commit hook")
    hook.add_argument("action", choices=("run", "install", "uninstall"))
    hook.add_argument("--force", action="store_true")
    patch = sub.add_parser("patch", help="preview or safely apply a Python assignment replacement")
    patch.add_argument("file")
    patch.add_argument("snippet", nargs="?")
    patch.add_argument("--line", type=int)
    patch.add_argument("--env-var")
    patch.add_argument("--apply", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "scan":
            code = cmd_scan(args)
        elif args.command == "baseline":
            code = cmd_baseline(args)
        elif args.command == "hook":
            code = cmd_hook(args)
        else:
            code = cmd_patch(args)
    except (ValueError, OSError, GitError) as exc:
        print(f"Prompt-Recon error: {exc}", file=sys.stderr)
        code = 2
    raise SystemExit(code)
