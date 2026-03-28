#!/usr/bin/env python3
# file: promptrecon/hooks/pre_commit.py

"""
Prompt-Recon Git Pre-commit Hook
扫 staged blob（git show :filepath），不是工作区文件

exit 0  — 通过
exit 1  — 发现敏感信息，阻断提交
exit 2  — Hook 自身异常
"""

import subprocess
import sys
import os
import re

# 使用内置规则（零外部依赖）
from promptrecon.rules.builtin import load_builtin_rules


def get_staged_content(filepath):
    """
    用 git show :filepath 读取 staged blob 内容。
    filepath: 工作区相对路径，如 "src/main.py"
    返回: bytes 或 None（文件不存在于 staged）
    """
    # :filepath 格式直接从 staged blob 读取
    result = subprocess.run(
        ['git', 'show', f':{filepath}'],
        capture_output=True,
        cwd=get_repo_root()
    )
    if result.returncode != 0:
        return None
    return result.stdout


def get_repo_root():
    """获取 git 仓库根目录"""
    result = subprocess.run(
        ['git', 'rev-parse', '--show-toplevel'],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return os.getcwd()
    return result.stdout.strip()


def is_binary(content):
    """检查是否二进制（含 null byte）"""
    return b'\x00' in content


ALLOWED_EXTENSIONS = {'.py', '.txt', '.json', '.yaml', '.yml', '.env', '.js', '.ts'}
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB


def get_staged_files():
    """
    用 git diff --cached -z 获取 staged 文件列表。
    返回: 文件路径列表（字符串）
    """
    result = subprocess.run(
        ['git', 'diff', '--cached', '--name-only', '--diff-filter=ACMR', '-z'],
        capture_output=True,
        cwd=get_repo_root()
    )
    if result.returncode != 0:
        print("Error: git diff --cached failed", file=sys.stderr)
        sys.exit(2)

    raw = result.stdout
    if not raw:
        return []

    # -z 零字节分隔，最后一个元素是空字节后跟空字符串，过滤掉
    paths = [p.decode('utf-8', errors='replace') for p in raw.split(b'\x00') if p]
    return paths


def filter_staged_files(paths):
    """
    过滤：扩展名白名单 + 文件大小 + 二进制
    返回: 通过过滤的文件路径列表
    """
    filtered = []
    for path in paths:
        _, ext = os.path.splitext(path)
        if ext.lower() not in ALLOWED_EXTENSIONS:
            continue

        content = get_staged_content(path)
        if content is None:
            continue
        if len(content) > MAX_FILE_SIZE:
            continue
        if is_binary(content):
            continue

        filtered.append(path)
    return filtered


def scan_content(display_path, content, rules):
    """
    扫描给定内容，返回命中列表。
    content: bytes 或 str
    返回: [{'rule': str, 'snippet': str, 'line': int}, ...]
    """
    if isinstance(content, bytes):
        content = content.decode('utf-8', errors='replace')

    hits = []
    for name, rule_data in rules.items():
        regex = rule_data["regex"]
        for m in regex.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            snippet = m.group(0)[:80]
            hits.append({'rule': name, 'snippet': snippet, 'line': line_num})
    return hits


BLOCKED_FILES = {}


def scan_staged(rules):
    """主扫描流程"""
    paths = get_staged_files()
    if not paths:
        return

    scannable = filter_staged_files(paths)

    for path in scannable:
        content = get_staged_content(path)
        if content is None:
            continue
        hits = scan_content(path, content, rules)
        if hits:
            for hit in hits:
                print(f"[BLOCKED] {path}: {hit['rule']}: {hit['snippet']}")
                BLOCKED_FILES[path] = True

    if BLOCKED_FILES:
        print(f"\nBlocked {len(BLOCKED_FILES)} file(s). Use --no-verify to bypass.")
        sys.exit(1)


def main():
    try:
        rules = load_builtin_rules()
        scan_staged(rules)
        sys.exit(0)
    except Exception as e:
        print(f"Hook error: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == '__main__':
    main()
