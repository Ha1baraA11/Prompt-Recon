<p align="center">
  <img src="assets/logo.png" alt="Prompt-Recon logo" width="200">
</p>

<h1 align="center">Prompt-Recon</h1>

<p align="center">
  <strong>Offline secrets scanning for personal repositories and small teams</strong><br>
  Inspect worktrees, staged blobs, and reachable Git history without sending candidates anywhere.
</p>

<p align="center">
  [简体中文](./README.zh-CN.md) · [繁體中文](./README.zh-TW.md) · [日本語](./README_ja.md) · [한국어](./README_ko.md) · [Español](./README_es.md) · [Português](./README_pt-BR.md) · [Русский](./README_ru.md) · [Français](./README_fr.md) · [Deutsch](./README_de.md)
</p>

---

## What it does

- Scans files, staged blobs, and Git history without checking out old revisions.
- Ships rules for AWS, GitHub, GitLab, OpenAI, Anthropic, Hugging Face, Slack, Stripe, npm, PyPI, Google API, private keys, JWTs, database URLs, and generic credential assignments.
- Redacts matched values in console output and machine reports; baselines store fingerprints only.
- Supports `.gitignore`, `.promptignore`, TOML configuration, inline allow markers, SARIF, JSONL, CSV, and Markdown reports.

## Requirements

- Python 3.10–3.13
- Git for staged and history scans

## Installation

```bash
python -m pip install promptrecon
```

For local development:

```bash
python -m pip install -e ".[dev]"
```

## Usage

```bash
# Scan the working tree
promptrecon scan .

# Scan only staged Git blobs before a commit
promptrecon scan --staged

# Scan reachable local Git history
promptrecon scan --history

# Select a report format and output file
promptrecon scan . --format sarif --output results.sarif
promptrecon scan . --format jsonl --output results.jsonl
```

Supported formats are `console`, `jsonl`, `csv`, `markdown`, and `sarif`. Exit codes are `0` when no new un-baselined finding remains, `1` when findings remain, and `2` for configuration, Git, or runtime errors.

## Baseline and configuration

Baselines suppress findings that have been reviewed without storing secret text:

```bash
promptrecon baseline create .
promptrecon baseline audit
promptrecon baseline update .
```

Creation refuses to overwrite an existing baseline unless `--force` is supplied. Copy `.promptrecon.toml.example` to `.promptrecon.toml` to configure exclusions and data-only custom rules. Python rule plugins and `--rules-dir` remain only as deprecated compatibility paths.

Use `# promptrecon: allow` on a finding line or `# promptrecon: allow-next-line` on the preceding line for deliberate exceptions.

## Git hooks

```bash
promptrecon hook install
promptrecon hook run
promptrecon hook uninstall
```

Installation refuses to silently replace an existing third-party hook. The hook scans staged content, not unrelated unstaged edits. A `.pre-commit-hooks.yaml` entry is included for pre-commit users.

## Safe patch preview

Patch is limited to safely located Python string assignments. It shows a redacted preview by default and writes only when `--apply` is explicit:

```bash
promptrecon patch settings.py --line 12 --env-var SERVICE_TOKEN
promptrecon patch settings.py --line 12 --env-var SERVICE_TOKEN --apply
```

Prompt-Recon never creates a remediated file containing the real secret.

## Development

```bash
python -m pytest
ruff check .
python -m mypy promptrecon
python -m build
python -m promptrecon --help
```

## Files

| Path | Purpose |
| --- | --- |
| `promptrecon/core.py` | Worktree scanning and file guards |
| `promptrecon/git.py` | Staged and history blob access |
| `promptrecon/rules/` | Built-in detection rules |
| `promptrecon/baseline.py` | Fingerprint-only baseline handling |
| `promptrecon/cli.py` | CLI and report formats |
| `tests/` | Unit and integration tests |

## License

MIT. See [LICENSE](./LICENSE) and [CHANGELOG](./CHANGELOG.md).
