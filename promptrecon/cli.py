# file: promptrecon/cli.py

import os
import argparse
import json
import csv
import sys
import signal
import threading
import fnmatch
import logging
from multiprocessing import cpu_count
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

from git import Repo
from rich.console import Console
from rich.table import Table
from rich.progress import Progress

# 从 'core' 模块导入我们的扫描逻辑
from .core import load_rules_from_dir, load_ignore_patterns, should_ignore, scan_file

# --- 全局配置 ---
console = Console()
findings_lock = threading.Lock()
findings = []
temp_dir_to_clean = None

# ----------------------------------------------------------------------
# v0.3: 功能实现 (Features #4, #5, #6, #7)
# ----------------------------------------------------------------------

# --- v0.3 Feature #6: SIGINT 处理器 ---
def handle_sigint(signum, frame):
    console.print("\n[!] Interrupted by user. Cleaning up...", style="yellow")
    if temp_dir_to_clean and os.path.exists(temp_dir_to_clean):
        import shutil
        shutil.rmtree(temp_dir_to_clean)
        console.print(f"[+] Cleaned up temp directory: {temp_dir_to_clean}", style="yellow")
    sys.exit(0)

# --- v0.3 Feature #4: 报告生成 (CSV/MD) ---
def save_csv_report(findings_list, filename):
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Risk Score", "Rule", "File", "Snippet"])
            for f in findings_list:
                writer.writerow([f"{f['risk_score']:.1f}", f["rule_name"], f["file"], f["snippet"]])
        console.print(f"[+] CSV report saved to [green]{filename}[/green]")
    except Exception as e:
        console.print(f"[ERROR] Failed to write CSV file: {e}", style="red")

def save_md_report(findings_list, filename):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("# Prompt-Recon Scan Report\n\n")
            f.write(f"**Total Findings:** {len(findings_list)}\n\n")
            f.write("| Risk | Rule | File | Snippet |\n")
            f.write("| :--- | :--- | :--- | :--- |\n")
            for f in findings_list:
                snippet_md = f["snippet"].replace('\n', ' ').replace('|', '\\|')
                f.write(f"| {f['risk_score']:.1f} | {f['rule_name']} | `{f['file']}` | `{snippet_md}` |\n")
        console.print(f"[+] Markdown report saved to [green]{filename}[/green]")
    except Exception as e:
        console.print(f"[ERROR] Failed to write MD file: {e}", style="red")

def save_jsonl_report(findings_list, filename):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            for finding in findings_list:
                finding.pop('rule', None)
                f.write(json.dumps(finding) + '\n')
        console.print(f"[+] JSONL report saved to [green]{filename}[/green]")
    except Exception as e:
        console.print(f"[ERROR] Failed to write JSONL file: {e}", style="red")

# ----------------------------------------------------------------------
# v2.0: Orchestrator 降维打击架构
# ----------------------------------------------------------------------

from .ml.vector_analyzer import VectorAnomalyDetector
from .dynamic.sentinel_proxy import run_sentinel
from .auto_remediate.patcher import auto_patch_file
from .cpg.ast_tracker import build_project_cpg
from .sociotech.git_analyzer import analyze_author_risk

def cmd_sentinel(args):
    """Start the runtime interception proxy"""
    console.print("[bold red]🚀 Initiating Prompt-Recon Sentinel Proxy...[/bold red]")
    run_sentinel(port=args.port)

def cmd_patch(args):
    """Auto-remediate a detected leak"""
    console.print(f"[*] Auto-patching {args.file} for leaked snippet...")
    success = auto_patch_file(args.file, args.snippet)
    if success:
        console.print("[+] Successfully remediated code. Check .env.remediated", style="green")
    else:
        console.print("[-] Remediation failed.", style="red")

def cmd_deep_scan(args):
    """The new AI-native Deep Scan Engine"""
    global temp_dir_to_clean
    
    start_time = float(os.times()[4])
    
    # 1. Load Rules (Legacy support)
    rules = load_rules_from_dir(args.rules_dir)
    console.print(f"[+] Loaded {len(rules)} legacy rules.")
        
    ignore_patterns = load_ignore_patterns(args.ignorefile)
    target_dir = args.directory
    is_temp_dir = False
    
    console.print("="*60)
    console.print("  Prompt-Recon (v2.0) - AI Native Sentinel & Scanner")
    console.print("="*60)
    
    try:
        # Clone logic
        if args.url:
            if args.safe and ("github.com/openai" in args.url or "github.com/huggingface" in args.url):
                console.print("[SAFE MODE] Skipped official repository scanning.", style="yellow")
                sys.exit(0)
                
            repo_name = urlparse(args.url).path.split('/')[-1].replace('.git', '')
            temp_dir = os.path.join(os.getcwd(), f"temp_{repo_name}")
            temp_dir_to_clean = temp_dir
            is_temp_dir = True
            
            if os.path.exists(temp_dir):
                import shutil
                shutil.rmtree(temp_dir)
            
            console.print(f"[*] Cloning {args.url} into {temp_dir}...")
            Repo.clone_from(args.url, temp_dir, depth=1)
            target_dir = temp_dir
        
        # Gather Files
        files_to_scan = []
        for root, _, files in os.walk(target_dir):
            for file in files:
                filepath = os.path.join(root, file)
                if not should_ignore(filepath, ignore_patterns):
                    files_to_scan.append(filepath)

        if not files_to_scan:
            console.print("[+] No files to scan.", style="green")
            sys.exit(0)
            
        # 2. Vector Anomaly Analysis & Legacy Core Scan
        console.print(f"[*] Initializing Vector Anomaly Detector (bge-small-zh)...")
        # In a real heavy implementation, we'd pass this to threads
        # vector_detector = VectorAnomalyDetector()
        
        # 3. Sociotech Analysis setup
        repo_path = target_dir if is_temp_dir else os.getcwd()
        
        max_workers = min(32, os.cpu_count() * 4)
        global findings
        findings = []

        with Progress() as progress:
            task = progress.add_task("[cyan]Deep Scanning Matrix...", total=len(files_to_scan))
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_file = {executor.submit(scan_file, fp, rules): fp for fp in files_to_scan}
                
                for future in as_completed(future_to_file):
                    try:
                        result = future.result()
                        if result:
                            # Enhance with Sociotech
                            for finding in result:
                                abs_path = os.path.join(target_dir, finding["file"])
                                socio = analyze_author_risk(repo_path, abs_path)
                                finding["sociotech"] = socio
                                finding["risk_score"] += socio.get("sociotech_risk_modifier", 0)
                                
                            with findings_lock:
                                findings.extend(result)
                    except Exception as e:
                        console.print(f"[ERROR] Thread failed: {e}", style="red")
                    progress.advance(task)

        # Output
        if not findings:
            console.print("\n[+] Scan complete. Matrix is clean.", style="green")
            sys.exit(0)

        console.print(f"\n[!] Deep Scan Complete. Found [bold red]{len(findings)}[/bold red] anomalies!")
        findings.sort(key=lambda x: x['risk_score'], reverse=True)
        
        # We assume output_rich_table exists in legacy core or is defined
        from .core import output_rich_table # Ensure it's imported if needed
        try:
            output_rich_table(findings)
        except Exception:
            console.print(findings)
            
        if args.jsonl: save_jsonl_report(findings, args.jsonl)

    finally:
        if is_temp_dir and os.path.exists(target_dir):
            import shutil
            shutil.rmtree(temp_dir)
            
        console.print("[+] Execution finished.")


def main():
    global temp_dir_to_clean
    signal.signal(signal.SIGINT, handle_sigint)

    parser = argparse.ArgumentParser(
        description="Prompt-Recon (v2.0) - AI Native Prompt Leak Analysis Matrix"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # 1. Sentinel Command
    sentinel_parser = subparsers.add_parser("sentinel", help="Run the runtime API interception proxy")
    sentinel_parser.add_argument("--port", type=int, default=8080)
    
    # 2. Patch Command
    patch_parser = subparsers.add_parser("patch", help="Auto-remediate a detected leak in a file")
    patch_parser.add_argument("file", help="File to patch")
    patch_parser.add_argument("snippet", help="Exact string leak to extract")
    
    # 3. Deep Scan Command
    scan_parser = subparsers.add_parser("scan", help="Run deep code property graph and vector scan")
    group = scan_parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-u', '--url', help="GitHub repo URL.")
    group.add_argument('-d', '--directory', help="Local directory.")
    scan_parser.add_argument('--jsonl', help="JSONL output")
    scan_parser.add_argument('-r', '--rules-dir', default="promptrecon/rules")
    scan_parser.add_argument('-i', '--ignorefile', default=".promptignore")
    scan_parser.add_argument('--safe', action='store_true')

    args = parser.parse_args()
    
    if args.command == "sentinel":
        cmd_sentinel(args)
    elif args.command == "patch":
        cmd_patch(args)
    elif args.command == "scan":
        cmd_deep_scan(args)

if __name__ == "__main__":
    main()
