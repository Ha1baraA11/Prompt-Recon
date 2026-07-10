<div align="center">

**[简体中文](./README.md)** | **[English](./README.en.md)** | **[繁體中文](./README.zh-TW.md)**

</div>

# Prompt-Recon

Prompt-Recon 是一个离线 secrets 扫描器：在工作树、暂存区和 Git 历史中发现 API key、token、私钥、数据库凭证和高熵字符串，并在提交前安全拦截。

它不会向任何服务发送候选凭证。报告只输出脱敏值和指纹。

## 安装

```bash
python -m pip install promptrecon
```

源码开发：

```bash
python -m pip install -e ".[dev]"
```

## 使用

```bash
# 扫描工作树；发现未纳入 baseline 的命中时返回 1
promptrecon scan .

# 只扫描 Git 暂存 blob，适合提交前检查
promptrecon scan --staged

# 扫描本地可达 refs 的历史 blob
promptrecon scan --history

# 输出 SARIF/JSONL
promptrecon scan . --format sarif --output results.sarif
promptrecon scan . --format jsonl --output results.jsonl
```

退出码为 `0`（无新增命中）、`1`（发现命中）或 `2`（工具/配置错误）。

## Baseline 与配置

首次接入已有仓库时，可以建立不包含秘密正文的指纹基线：

```bash
promptrecon baseline create .
promptrecon baseline audit
promptrecon baseline update .
```

可复制 `.promptrecon.toml.example` 为 `.promptrecon.toml`，配置排除路径、停用规则和自定义 TOML 规则。代码插件已弃用，避免扫描时执行任意 Python。

支持在行尾使用 `# promptrecon: allow`，或在上一行使用 `# promptrecon: allow-next-line`。

## Git hook

```bash
promptrecon hook install
```

已有第三方 hook 时不会静默覆盖。也可以使用仓库自带的 `.pre-commit-hooks.yaml`。

## 安全修复预览

修复默认只生成脱敏 diff；确认后才应用：

```bash
promptrecon patch settings.py --line 12 --env-var SERVICE_TOKEN
promptrecon patch settings.py --line 12 --env-var SERVICE_TOKEN --apply
```

不会生成包含真实秘密的 `.env.remediated` 文件。

## 开发

```bash
python -m pytest
ruff check .
python -m mypy promptrecon
python -m build
```

MIT License。详见 [CHANGELOG](./CHANGELOG.md)。
