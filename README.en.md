<div align="center">

**[简体中文](./README.md)** | **[English]** | **[繁體中文](./README.zh-TW.md)**

</div>

# 🚀 Prompt-Recon (v2.0)

![AI Security](https://img.shields.io/badge/focus-AI%20Security-red)
![Version](https://img.shields.io/badge/version-2.0.0-blue)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

Prompt-Recon v2.0 is a comprehensive lifecycle AI asset defense and auditing system.

This tool is designed for security researchers, red-teamers, and DevSecOps teams to audit, intercept, and fix hardcoded "system prompt leaks" and other confidential data vulnerabilities within codebases and runtime traffic.

## Core Features (v2.0)

- 🛡️ **Runtime Dynamic Gateway (Sentinel Proxy)**: An ASGI network proxy that intercepts LLM-bound traffic (e.g., OpenAI, Claude) to detect and block prompt leaks at runtime.
- 🧠 **Embedding Vector Analysis**: Integrates embedding models like `bge-small-zh` to detect obfuscated prompts via vector space similarity, complementing pure regex scanning.
- ⚖️ **LLM Sandbox Validation**: Implements LangChain-based validation loops, using LLMs to evaluate suspected leaked prompts and lower false-positive rates.
- 🕸️ **AST/CPG Data Flow Tracking**: Tracks variables and function calls at the Python Abstract Syntax Tree (AST) level to reconstruct fragmented prompt strings.
- 👥 **Git Security Auditing**: Uses `GitPython` to extract commit history features associated with leaked code, assisting in engineering risk alerts.
- 💧 **Zero-Width Watermarking**: Uses invisible zero-width characters to watermark core prompts to help track insider threats.
- 🤖 **Auto-Remediation**: Can automatically refactor detected hard-coded prompts using `os.environ` lookups and safely extract the secrets to an `.env.remediated` file.
- ⌨️ **Multi-Mode CLI**: Provides `scan`, `patch`, and `sentinel` as the three core operational modes.

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
