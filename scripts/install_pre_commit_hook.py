#!/usr/bin/env python3
# file: scripts/install_pre_commit_hook.py

"""
安装 Prompt-Recon pre-commit hook 到当前仓库。
运行方式: python3 scripts/install_pre_commit_hook.py

幂等：重复执行只覆盖同一份 Hook。
"""

import os
import stat
import pathlib
import subprocess
import sys


def get_repo_root():
    # 使用运行时的当前目录（支持从任意仓库目录安装）
    result = subprocess.run(
        ['git', 'rev-parse', '--show-toplevel'],
        capture_output=True, text=True,
        cwd=os.getcwd()
    )
    if result.returncode != 0:
        raise RuntimeError("Not inside a Git repository")
    return pathlib.Path(result.stdout.strip())


def install():
    repo_root = get_repo_root()
    hook_target = repo_root / '.git' / 'hooks' / 'pre-commit'

    # 写 wrapper：cd 到仓库根，加入 PYTHONPATH 再用 python3 -m 启动
    # PYTHONPATH 需要指向 Prompt-Recon 的 parent 目录，让 python 能找到 promptrecon 包
    promptrecon_root = str(repo_root)
    wrapper_lines = [
        '#!/bin/sh',
        f'# Auto-installed by Prompt-Recon',
        f'export PYTHONPATH="{promptrecon_root}:$PYTHONPATH" && \\',
        f'cd "{repo_root}" && \\',
        f'  python3 -m promptrecon.hooks.pre_commit',
    ]
    wrapper_content = '\n'.join(wrapper_lines) + '\n'

    git_hooks_dir = hook_target.parent
    if not git_hooks_dir.exists():
        git_hooks_dir.mkdir(parents=True, exist_ok=True)

    hook_target.write_text(wrapper_content)
    hook_target.chmod(hook_target.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    print(f"Installed: {hook_target}")
    print(f"Runner:    {sys.executable} -m promptrecon.hooks.pre_commit")


if __name__ == '__main__':
    install()
