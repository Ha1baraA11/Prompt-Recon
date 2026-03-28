<div align="center">

**[简体中文](./README.md)** | **[English]** | **[繁體中文](./README.zh-TW.md)**

</div>

# Prompt-Recon

A local code secrets scanner and Git pre-commit hook interceptor.

Detects hardcoded API keys, tokens, passwords and other secrets before they are committed — blocking leaks at the source.

## Core Features

- **Rule-based Scanning**: Uses Python standard library regex to detect hardcoded credentials (OpenAI API Key, GitHub Token, `.env` files, etc.).
- **Git Pre-commit Hook**: Scans staged blobs on every `git commit` and blocks if secrets are found.
- **Staged Files Only**: Hook only scans files returned by `git diff --cached`, not the entire repository — fast.
- **Basic Auto-Remediation**: Replaces plaintext secrets with `os.environ.get()` format.

## Installation

```bash
git clone https://github.com/Ha1baraA11/Prompt-Recon.git
cd Prompt-Recon
pip install -e .
```

After installation, `promptrecon` is available globally, or use:

```bash
python3 -m promptrecon scan -d .
```

## Directory Scanning

```bash
# Scan current directory
promptrecon scan -d .

# Generate report
promptrecon scan -d . --jsonl results.jsonl
```

## Hook Installation

```bash
# Install pre-commit hook (auto-blocks commits with secrets)
python3 scripts/install_pre_commit_hook.py
```

After installation, every `git commit` automatically scans staged blobs. Supports `.env`, `.py`, `.json`, `.yaml` and more.

## Commit Blocking Example

```bash
$ echo 'api_key = "sk-mock-1234567890abcdefghijklmnop"' > test.py
$ git add test.py
$ git commit -m "add key"
[BLOCKED] test.py: generic_secret:1 api_key = "sk-mock-123...

Blocked 1 file(s). Use --no-verify to bypass.
```

## Known Limitations

- Regex scanning can produce false positives and false negatives; best used as a first line of defense.
- Current rules are hardcoded Python dictionaries; can be extended to rule files in future.
- Auto-remediation is string-based replacement and may not preserve exact semantics.

## Architecture

```
promptrecon/
  hooks/
    pre_commit.py       — Hook main logic
  rules/
    builtin.py          — Built-in rules
  core.py               — Unified scan core
  cli.py                — CLI entry (scan / patch)
  __main__.py           — python3 -m entry
scripts/
  install_pre_commit_hook.py  — Hook installer
```

---

[![Stargazers over time](https://starchart.cc/Ha1baraA11/Prompt-Recon.svg?variant=dark)](https://starchart.cc/Ha1baraA11/Prompt-Recon)
