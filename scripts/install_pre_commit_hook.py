#!/usr/bin/env python3
# file: scripts/install_pre_commit_hook.py

"""
安装 Prompt-Recon pre-commit hook 到当前仓库。
运行方式: python3 scripts/install_pre_commit_hook.py

幂等：重复执行只覆盖同一份 Hook。

安装契约：
  1. 先执行 pip install -e . 安装 Prompt-Recon
  2. 再运行本脚本，将 Hook 安装到目标 Git 仓库
Hook 依赖 PYTHONPATH 指向 Prompt-Recon 源码根目录，
由安装脚本写入目标仓库的 .git/hooks/pre-commit 包装脚本。
"""

import os
import stat
import pathlib
import subprocess
import sys


def get_promptrecon_root():
    """Prompt-Recon 源码根目录（脚本所在项目的根目录）"""
    return pathlib.Path(__file__).resolve().parent.parent


def get_target_repo_root():
    """目标 Git 仓库根目录（运行 install 的那个仓库）"""
    result = subprocess.run(
        ['git', 'rev-parse', '--show-toplevel'],
        capture_output=True, text=True,
        cwd=os.getcwd()
    )
    if result.returncode != 0:
        raise RuntimeError("Not inside a Git repository")
    return pathlib.Path(result.stdout.strip())


def install():
    promptrecon_root = str(get_promptrecon_root())
    target_repo_root = str(get_target_repo_root())
    python_bin = sys.executable  # 绝对路径

    hook_target = pathlib.Path(target_repo_root) / '.git' / 'hooks' / 'pre-commit'

    # Wrapper 顺序：shebang → 注释 → PYTHONPATH → cd → exec
    wrapper_lines = [
        '#!/bin/sh',
        '# Auto-installed by Prompt-Recon',
        f'export PYTHONPATH="{promptrecon_root}:$PYTHONPATH" && \\',
        f'cd "{target_repo_root}" && \\',
        f'  exec "{python_bin}" -m promptrecon.hooks.pre_commit',
    ]
    wrapper_content = '\n'.join(wrapper_lines) + '\n'

    git_hooks_dir = hook_target.parent
    if not git_hooks_dir.exists():
        git_hooks_dir.mkdir(parents=True, exist_ok=True)

    hook_target.write_text(wrapper_content)
    hook_target.chmod(hook_target.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    print(f"Installed:  {hook_target}")
    print(f"PYTHONPATH: {promptrecon_root}")
    print(f"Runner:     {python_bin} -m promptrecon.hooks.pre_commit")


if __name__ == '__main__':
    install()
