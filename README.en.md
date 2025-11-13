<div align="center">

**[简体中文](./README.md)** | **[English]** | **[繁體中文](./README.zh-TW.md)**

</div>

# 🚀 Prompt-Recon (v1.0)

![AI Security](https://img.shields.io/badge/focus-AI%20Security-red)
![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

A plugin-driven, multithreaded scanner for hardcoded AI System Prompts and other secrets.

This tool is designed for security researchers, red-teamers, and DevSecOps teams to audit codebases for "leaked prompts" – a new and critical class of AI security vulnerabilities.

## Core Features (v1.0)

- **Multithreaded**: (Feature #2) Uses `ThreadPoolExecutor` to scan thousands of files at high speed.
- **Plugin-Driven Rules**: (Feature #1) Automatically loads all rule plugins from the `promptrecon/rules/` directory.
- **Advanced Risk Scoring**: (Feature #5) Calculates a risk score (0-10) for each finding, based on keywords and file paths (`main` vs. `dev`).
- **L3 Semantic Verification**: (Features #3, #4) Goes beyond simple regex. Uses smart Base64 decoding and semantic analysis (`looks_like_prompt`) to reduce false positives.
- **CI/CD & Compliance**: (Features #5, #7, #8, #9) Supports `.promptignore`, audit logs, and provides CI/CD-friendly exit codes.
- **Rich Reports**: (Features #4, #6) Generates beautiful `rich` tables in the console, plus `CSV`, `Markdown`, and `JSONL` reports.

## Installation

1.  Clone this repository:

    ```bash
    git clone https://github.com/Ha1baraA11/Prompt-Recon.git
    cd prompt-recon
    ```

2.  (Recommended) Create a virtual environment:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
3.  Install dependencies and the tool in "editable" mode:

    ```bash
    # Install the core dependencies
    pip install rich gitpython
    
    # Install the tool
    pip install -e .
    ```

## Usage

Once installed, the `promptrecon` command will be available.

```bash
# Scan a local directory
promptrecon -d /path/to/your/codebase

# Scan a public GitHub repository (will be cloned automatically)
promptrecon -u [https://github.com/user/vulnerable-repo](https://github.com/user/vulnerable-repo)

# Generate multiple reports
promptrecon -d . --md report.md --csv report.csv --jsonl results.jsonl

# Run in --safe mode (skips official repos)
promptrecon -u [https://github.com/openai/gpt-3](https://github.com/openai/gpt-3) --safe

# Use in CI/CD (will exit with code 3 if critical risk found)
promptrecon -d .
```
## Stargazers over time
[![Stargazers over time](https://starchart.cc/Ha1baraA11/Prompt-Recon.svg?variant=dark)](https://starchart.cc/Ha1baraA11/Prompt-Recon)
