#!/usr/bin/env python3
# file: scripts/install_pre_commit_hook.py

"""
安装 Prompt-Recon pre-commit hook 到当前仓库。
运行方式: python3 scripts/install_pre_commit_hook.py
"""

import os
import stat
import pathlib


def get_repo_root():
    result = pathlib.Path(__file__).resolve().parent.parent
    return result


def get_hook_source():
    return get_repo_root() / 'promptrecon' / 'hooks' / 'pre_commit.py'


def get_hook_target():
    repo_root = get_repo_root()
    return repo_root / '.git' / 'hooks' / 'pre-commit'


def install():
    repo_root = get_repo_root()
    hook_source = get_hook_source()
    hook_target = get_hook_target()

    if not hook_source.exists():
        print(f"Error: hook source not found: {hook_source}", file=sys.stderr)
        return

    git_hooks_dir = hook_target.parent
    if not git_hooks_dir.exists():
        git_hooks_dir.mkdir(parents=True, exist_ok=True)

    # 写包装脚本
    wrapper = f"""#!/bin/sh
# Auto-installed by Prompt-Recon hook installer
# Source: {hook_source.relative_to(repo_root)}
exec python3 "{hook_source}"
"""
    hook_target.write_text(wrapper)

    # 加执行权限
    current = hook_target.stat().st_mode
    hook_target.chmod(current | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    print(f"Installed: {hook_target}")
    print(f"Source:    {hook_source.relative_to(repo_root)}")


if __name__ == '__main__':
    import sys
    install()
