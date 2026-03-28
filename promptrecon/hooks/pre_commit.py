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

# 复用 core.py 的统一扫描函数
from promptrecon.core import scan_content
from promptrecon.rules.builtin import load_builtin_rules

# 模块加载时缓存一次 repo root，避免每个文件都起 git rev-parse
_REPO_ROOT = None


def _get_repo_root():
    global _REPO_ROOT
    if _REPO_ROOT is None:
        result = subprocess.run(
            ['git', 'rev-parse', '--show-toplevel'],
            capture_output=True, text=True
        )
        _REPO_ROOT = result.stdout.strip() if result.returncode == 0 else os.getcwd()
    return _REPO_ROOT


ALLOWED_EXTENSIONS = {'.py', '.txt', '.json', '.yaml', '.yml', '.js', '.ts'}
ALLOWED_BASENAMES = {'.env'}
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB


def _get_staged_files():
    """用 git diff --cached -z 获取 staged 文件列表（bytes 路径）。"""
    result = subprocess.run(
        ['git', 'diff', '--cached', '--name-only', '--diff-filter=ACMR', '-z'],
        capture_output=True,
        cwd=_get_repo_root()
    )
    if result.returncode != 0:
        print("Error: git diff --cached failed", file=sys.stderr)
        sys.exit(2)

    raw = result.stdout
    if not raw:
        return []
    return [p for p in raw.split(b'\x00') if p]


BLOCKED_FILES = {}


def _scan_staged_file(path_bytes, rules):
    """
    对单个 staged 文件执行：路径过滤 → 读取 blob → 扫描。
    每个文件只读一次（合并了过滤 + 扫描）。
    """
    # 解码路径
    path = path_bytes.decode('utf-8', errors='replace')
    basename = os.path.basename(path)
    _, ext = os.path.splitext(basename)

    # 扩展名过滤（.env 文件名不走 splitext）
    is_env_file = basename == '.env'
    if ext.lower() not in ALLOWED_EXTENSIONS and not is_env_file:
        return

    # 只读一次 staged blob
    result = subprocess.run(
        ['git', 'show', f':{path}'],
        capture_output=True,
        cwd=_get_repo_root()
    )
    if result.returncode != 0:
        return
    content_bytes = result.stdout

    # 大小过滤
    if len(content_bytes) > MAX_FILE_SIZE:
        return

    # 二进制过滤
    if b'\x00' in content_bytes[:4096]:
        return

    # 扫描
    hits = scan_content(content_bytes, rules)
    if not hits:
        return

    for hit in hits:
        print(f"[BLOCKED] {path}: {hit['rule_name']}:{hit['line']} {hit['snippet']}")
        BLOCKED_FILES[path] = True


def scan_staged(rules):
    """主扫描流程"""
    staged = _get_staged_files()
    for path_bytes in staged:
        _scan_staged_file(path_bytes, rules)

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
