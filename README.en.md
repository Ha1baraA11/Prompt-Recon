# Prompt-Recon

Prompt-Recon is an offline secrets scanner for worktrees, staged Git blobs, and reachable Git history. It detects provider tokens, private keys, database credentials, and high-entropy values without sending candidates over the network.

```bash
python -m pip install promptrecon
promptrecon scan .
promptrecon scan --staged
promptrecon scan --history
promptrecon scan . --format sarif --output results.sarif
```

Exit codes are `0` for no new findings, `1` for findings, and `2` for tool or configuration errors. Baselines contain fingerprints only:

```bash
promptrecon baseline create .
promptrecon baseline audit
promptrecon hook install
```

Copy `.promptrecon.toml.example` to `.promptrecon.toml` for exclusions and data-only custom rules. Use `# promptrecon: allow` for a deliberate inline exception. Remediation is preview-only unless `--apply` is explicitly passed.

See [CHANGELOG](./CHANGELOG.md). Licensed under MIT.
