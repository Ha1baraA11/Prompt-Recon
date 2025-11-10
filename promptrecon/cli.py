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
                snippet_md = f["snippet"].replace('\n', ' ').replace('|', '\|')
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
# v0.3: 主函数 (Orchestrator)
# ----------------------------------------------------------------------
def main():
    global temp_dir_to_clean
    
    # --- v0.3 Feature #6: 注册 SIGINT 处理器 ---
    signal.signal(signal.SIGINT, handle_sigint)

    parser = argparse.ArgumentParser(
        description="Prompt-Recon (v0.3) - A plugin-driven, multithreaded scanner for hardcoded AI System Prompts.",
        epilog="Use with caution. For educational and authorized red-team use only."
    )
    
    # 扫描目标
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-u', '--url', help="GitHub repo URL to clone and scan.")
    group.add_argument('-d', '--directory', help="Local directory to scan.")
    
    # 报告输出 (v0.3 Feature #4)
    parser.add_argument('--jsonl', help="File to save findings in JSONL format.")
    parser.add_argument('--csv', help="File to save findings in CSV format.")
    parser.add_argument('--md', help="File to save findings in Markdown format.")
    
    # 配置
    parser.add_argument('-r', '--rules-dir', default="promptrecon/rules", 
                        help="Path to custom rules directory (default: promptrecon/rules).")
    parser.add_argument('-i', '--ignorefile', default=".promptignore",
                        help="Path to custom ignore file (default: .promptignore).")
    
    # --- v0.3 Feature #5: Safe Mode ---
    parser.add_argument('--safe', action='store_true', 
                        help="[Compliance] Skip scanning known official repositories (e.g., github.com/openai).")
    
    args = parser.parse_args()
    
    start_time = float(os.times()[4])
    
    # --- v0.3 Feature #1: 加载规则 ---
    rules = load_rules_from_dir(args.rules_dir)
    if not rules:
        console.print("[ERROR] No rules loaded. Exiting.", style="red")
        sys.exit(1)
    console.print(f"[+] Loaded {len(rules)} rules from [cyan]{args.rules_dir}[/cyan]")
        
    ignore_patterns = load_ignore_patterns(args.ignorefile)
    
    target_dir = args.directory
    is_temp_dir = False
    
    console.print("="*60)
    console.print("  Prompt-Recon (v0.3) - AI System Prompt Scanner")
    console.print("="*60)
    
    try:
        # --- 场景1：扫描 URL ---
        if args.url:
            # --- v0.3 Feature #5: Safe Mode 检查 ---
            if args.safe and ("github.com/openai" in args.url or "github.com/huggingface" in args.url):
                console.print("[SAFE MODE] Skipped official repository scanning for compliance reasons.", style="yellow")
                sys.exit(0)
                
            repo_name = urlparse(args.url).path.split('/')[-1].replace('.git', '')
            temp_dir = os.path.join(os.getcwd(), f"temp_{repo_name}")
            temp_dir_to_clean = temp_dir # 注册清理
            is_temp_dir = True
            
            if os.path.exists(temp_dir):
                import shutil
                shutil.rmtree(temp_dir)
            
            console.print(f"[*] Cloning {args.url} into {temp_dir} (depth=1)...")
            Repo.clone_from(args.url, temp_dir, depth=1)
            target_dir = temp_dir
        
        # --- 场景2：扫描目录 ---
        console.print(f"[*] Starting scan on [cyan]{target_dir}[/cyan]...")
        
        files_to_scan = []
        for root, _, files in os.walk(target_dir):
            for file in files:
                filepath = os.path.join(root, file)
                if not should_ignore(filepath, ignore_patterns):
                    files_to_scan.append(filepath)

        if not files_to_scan:
            console.print("[+] No files to scan (or all ignored).", style="green")
            sys.exit(0)

        # --- v0.3 Feature #2 & #4: 动态线程 + Rich Progress ---
        max_workers = min(32, os.cpu_count() * 4)
        console.print(f"[*] Found {len(files_to_scan)} files. Starting [green]ThreadPoolExecutor[/green] (max_workers={max_workers})...")
        
        global findings
        findings = []

        with Progress() as progress:
            task = progress.add_task("[cyan]Scanning...", total=len(files_to_scan))
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_file = {executor.submit(scan_file, fp, rules): fp for fp in files_to_scan}
                
                for future in as_completed(future_to_file):
                    try:
                        result = future.result()
                        if result:
                            # v0.3 Feature #3: 线程安全添加
                            with findings_lock:
                                findings.extend(result)
                    except Exception as e:
                        console.print(f"[ERROR] Thread failed for {future_to_file[future]}: {e}", style="red")
                    progress.advance(task)

        # --- 结果呈现 ---
        if not findings:
            console.print("\n[+] Scan complete. No findings. (Looks clean!)", style="green")
            sys.exit(0)

        console.print(f"\n[!] Scan Complete. Found [bold red]{len(findings)}[/bold red] potential leaks!")
        
        findings.sort(key=lambda x: x['risk_score'], reverse=True)
        
        # 默认 Rich 表格输出
        output_rich_table(findings)
        
        # v0.3 Feature #4: 额外报告
        if args.jsonl:
            save_jsonl_report(findings, args.jsonl)
        if args.csv:
            save_csv_report(findings, args.csv)
        if args.md:
            save_md_report(findings, args.md)

    except Exception as e:
        console.print(f"\n[FATAL ERROR] An unexpected error occurred: {e}", style="red")
        logging.error(f"FATAL ERROR: {e}")
        
    finally:
        if is_temp_dir and os.path.exists(target_dir):
            import shutil
            console.print(f"\n[*] Cleaning up temporary directory: [cyan]{temp_dir}[/cyan]")
            shutil.rmtree(temp_dir)
            
        end_time = float(os.times()[4])
        duration = end_time - start_time
        console.print(f"[+] Scan finished in {duration:.2f} seconds.")
        logging.info(f"Scan target: {args.url or args.directory}. Findings: {len(findings)}. Duration: {duration:.2f}s")
        
        # --- v0.3 Feature #7: CI/CD 退出码 ---
        max_risk = max((f['risk_score'] for f in findings), default=0)
        if max_risk >= 8:
            console.print(f"[!] Exiting with code 3 (Critical risk found: {max_risk:.1f})", style="red")
            sys.exit(3)
        elif max_risk >= 5:
            console.print(f"[!] Exiting with code 2 (High risk found: {max_risk:.1f})", style="yellow")
            sys.exit(2)
        elif max_risk > 0:
            sys.exit(1)
        else:
            sys.exit(0)

if __name__ == "__main__":
    main()
