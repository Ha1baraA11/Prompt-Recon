# file: promptrecon/cli.py

"""
Prompt-Recon CLI
只暴露 scan 和 patch 两个子命令。
重型模块（sentinel、AST、向量等）不再默认导入，按需懒加载。
"""

import os
import sys
import argparse

from .core import scan_file, load_rules_from_dir, load_ignore_patterns, should_ignore


# --- patch 命令（轻量，直接调 patcher） ---
def cmd_patch(args):
    try:
        from .auto_remediate.patcher import auto_patch_file
    except ImportError:
        print("Error: auto_remediate.patcher not available", file=sys.stderr)
        sys.exit(1)

    success = auto_patch_file(args.file, args.snippet)
    if success:
        print("[+] Remediated. Check .env.remediated")
    else:
        print("[-] Remediation failed.")
        sys.exit(1)


# --- scan 命令（轻量，正则扫描） ---
def cmd_scan(args):
    from rich.console import Console
    console = Console()

    # 规则：优先 builtin，可选追加 rules-dir
    from .rules.builtin import load_builtin_rules
    rules = load_builtin_rules()

    if args.rules_dir:
        extra = load_rules_from_dir(args.rules_dir)
        rules.update(extra)

    if not rules:
        console.print("[yellow]No rules loaded.[/yellow]")
        sys.exit(0)

    console.print(f"[+] Loaded {len(rules)} rule(s). Scanning...")

    # 无条件加载 ignore patterns（包括内置默认规则，文件不存在也能拿到默认值）
    # .promptignore 路径相对于扫描目标目录（args.directory），不是 cwd
    ignorefile_path = os.path.join(args.directory, args.ignorefile)
    ignore_patterns = load_ignore_patterns(ignorefile_path)

    files_to_scan = []
    for root, dirs, files in os.walk(args.directory, topdown=True):
        # 目录级忽略：把匹配的子目录从遍历队列中移除（递归剪枝）
        dirs[:] = [d for d in dirs
                    if not should_ignore(os.path.join(root, d), ignore_patterns)]
        for fname in files:
            fpath = os.path.join(root, fname)
            if should_ignore(fpath, ignore_patterns):
                continue
            files_to_scan.append(fpath)

    if not files_to_scan:
        console.print("[green]No files to scan.[/green]")
        sys.exit(0)

    all_findings = []
    for fpath in files_to_scan:
        findings = scan_file(fpath, rules, display_root=args.directory)
        all_findings.extend(findings)

    if not all_findings:
        console.print("[green]Scan complete. No secrets found.[/green]")
        sys.exit(0)

    console.print(f"[red]![/red] Found {len(all_findings)} secret(s).")
    _print_findings(all_findings, console)

    if getattr(args, 'jsonl', None):
        _save_jsonl(all_findings, args.jsonl)
    if getattr(args, 'csv', None):
        _save_csv(all_findings, args.csv)
    if getattr(args, 'md', None):
        _save_md(all_findings, args.md)


def _print_findings(findings, console):
    from rich.table import Table
    table = Table(title="Scan Results", show_lines=True)
    table.add_column("File", style="blue")
    table.add_column("Rule", style="cyan")
    table.add_column("Line", justify="right", style="yellow")
    table.add_column("Snippet", style="white")

    for f in findings:
        snippet = f.get('snippet', '')[:60].replace('\n', ' ')
        table.add_row(
            f.get('file', '?'),
            f.get('rule_name', '?'),
            str(f.get('line', '?')),
            snippet
        )
    console.print(table)


def _save_jsonl(findings, filename):
    import json
    with open(filename, 'w', encoding='utf-8') as f:
        for finding in findings:
            out = {k: v for k, v in finding.items() if k != 'rule'}
            f.write(json.dumps(out, ensure_ascii=False) + '\n')


def _save_csv(findings, filename):
    import csv
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["File", "Rule", "Line", "Snippet"])
        for finding in findings:
            writer.writerow([
                finding.get('file', ''),
                finding.get('rule_name', ''),
                finding.get('line', ''),
                finding.get('snippet', ''),
            ])


def _save_md(findings, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("# Prompt-Recon Scan Report\n\n")
        f.write(f"**Total:** {len(findings)}\n\n")
        f.write("| File | Rule | Line | Snippet |\n")
        f.write("| :--- | :--- | ---: | :--- |\n")
        for finding in findings:
            snippet = finding.get('snippet', '').replace('\n', ' ').replace('|', '\\|')
            f.write(f"| {finding.get('file', '')} | {finding.get('rule_name', '')} "
                    f"| {finding.get('line', '')} | {snippet} |\n")


# --- main ---
def main():
    parser = argparse.ArgumentParser(
        description="Prompt-Recon: Local code secrets scanner and Git pre-commit hook."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # scan
    scan_parser = subparsers.add_parser("scan", help="Scan a directory for secrets")
    scan_parser.add_argument('-d', '--directory', required=True,
                              help="Directory to scan")
    scan_parser.add_argument('--rules-dir',
                              help="Extra rules directory (appends to builtin rules)")
    scan_parser.add_argument('--ignorefile', default=".promptignore",
                              help="Ignore patterns file")
    scan_parser.add_argument('--jsonl', help="JSONL output file")
    scan_parser.add_argument('--csv', help="CSV output file")
    scan_parser.add_argument('--md', help="Markdown output file")

    # patch
    patch_parser = subparsers.add_parser("patch", help="Auto-remediate a secret in a file")
    patch_parser.add_argument("file", help="File to patch")
    patch_parser.add_argument("snippet", help="Exact secret string to remediate")

    args = parser.parse_args()

    if args.command == "scan":
        cmd_scan(args)
    elif args.command == "patch":
        cmd_patch(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
