<div align="center">

**[简体中文]** | **[English](./README.en.md)** | **[繁體中文](./README.zh-TW.md)**

</div>

# Prompt-Recon

本地代码敏感信息扫描与 Git 提交前拦截工具。

本工具用于在代码提交前检测硬编码的 API Key、Token、密码等敏感凭证，从源头防止泄露。

## 核心功能

- **规则驱动扫描**：使用 Python 标准库正则，扫描代码目录中的硬编码凭证（OpenAI API Key、GitHub Token、通用密钥赋值）。
- **Git Pre-commit Hook**：将扫描封装为 Git 钩子，commit 时自动触发，检测到敏感词则阻断提交。
- **仅扫描暂存文件**：Hook 只扫描 `git diff --cached` 返回的已暂存文件，不扫描整个仓库，速度快。
- **辅助脱敏**：自动将明文凭证替换为 `os.environ.get()` 格式。

## 安装

```bash
git clone https://github.com/Ha1baraA11/Prompt-Recon.git
cd Prompt-Recon
pip install rich
```

## 目录扫描

```bash
# 扫描当前目录
promptrecon -d .

# 生成报告
promptrecon -d . --jsonl results.jsonl
```

## Hook 安装

```bash
# 安装 pre-commit hook（自动拦截含敏感信息的提交）
python3 scripts/install_pre_commit_hook.py
```

安装后，每次 `git commit` 自动扫描暂存文件，发现敏感词则阻断提交。

## 提交拦截示例

```bash
$ echo 'api_key = "sk-mock-1234567890abcdefghijklmnop"' > test.py
$ git add test.py
$ git commit -m "add key"
[BLOCKED] test.py: generic_secret: api_key = "sk-mock-1234567890abcdefghijklmnop"

Blocked 1 file(s). Use --no-verify to bypass.
```

## 已知限制

- 正则扫描存在误报和漏报可能，适合作为开发流程第一道卡点。
- 当前规则以内置 Python 字典形式提供，后续可扩展为规则文件。
- 辅助脱敏为字符串替换，不能保证语义完全等价。

## 架构说明

```
promptrecon/
  hooks/pre_commit.py    — Hook 主逻辑
  rules/builtin.py       — 内置规则字典
  core.py                — 扫描核心（scan_content）
  scripts/
    install_pre_commit_hook.py  — Hook 安装脚本
```

---

[![Stargazers over time](https://starchart.cc/Ha1baraA11/Prompt-Recon.svg?variant=dark)](https://starchart.cc/Ha1baraA11/Prompt-Recon)
