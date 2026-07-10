# Changelog

## 1.0.0 - 2026-07-10

- Rebuilt the scanner around typed findings, offline provider rules, entropy-aware filtering, and safe redaction.
- Added worktree, staged-blob, Git history, baseline, SARIF, and managed hook workflows.
- Migrated packaging to `pyproject.toml` and removed unshipped experimental runtime modules.
- Made automatic remediation preview-only unless `--apply` is explicitly requested.
