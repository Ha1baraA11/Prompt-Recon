<p align="center">
  <img src="assets/logo.png" alt="Prompt-Recon 标志" width="200">
</p>

<h1 align="center">Prompt-Recon</h1>

<p align="center">
  <strong>面向个人仓库和小团队的离线 secrets 扫描器</strong><br>
  检查工作树、暂存 blob 和本地可达的 Git 历史，不向任何地方发送候选内容。
</p>

<p align="center">
  [English](./README.md) · [繁體中文](./README.zh-TW.md) · [日本語](./README_ja.md) · [한국어](./README_ko.md) · [Español](./README_es.md) · [Português](./README_pt-BR.md) · [Русский](./README_ru.md) · [Français](./README_fr.md) · [Deutsch](./README_de.md)
</p>

---

## 功能

- 扫描文件、暂存 blob 和 Git 历史，不 checkout 旧版本。
- 内置 AWS、GitHub、GitLab、OpenAI、Anthropic、Hugging Face、Slack、Stripe、npm、PyPI、Google API、私钥、JWT、数据库 URL 和通用凭证赋值规则。
- 控制台和机器报告始终脱敏；baseline 只保存指纹。
- 支持 `.gitignore`、`.promptignore`、TOML 配置、行内 allow 标记，以及 SARIF、JSONL、CSV、Markdown 报告。

## 要求

- Python 3.10–3.13
- 暂存区和历史扫描需要 Git

## 安装

```bash
python -m pip install promptrecon
```

本地开发：

```bash
python -m pip install -e ".[dev]"
```

## 使用

```bash
promptrecon scan .
promptrecon scan --staged
promptrecon scan --history
promptrecon scan . --format sarif --output results.sarif
```

支持 `console`、`jsonl`、`csv`、`markdown` 和 `sarif`。退出码：`0` 表示没有新的未纳入 baseline 的命中，`1` 表示仍有命中，`2` 表示配置、Git 或运行错误。

## Baseline 与配置

```bash
promptrecon baseline create .
promptrecon baseline audit
promptrecon baseline update .
```

Baseline 不保存秘密正文；已有文件必须显式指定 `--force` 才能覆盖。复制 `.promptrecon.toml.example` 为 `.promptrecon.toml`，即可配置排除路径和数据化自定义规则。可使用 `# promptrecon: allow` 或 `# promptrecon: allow-next-line` 标记有意接受的命中。

## Git Hook

```bash
promptrecon hook install
promptrecon hook run
promptrecon hook uninstall
```

安装时不会静默覆盖已有的第三方 hook，hook 只扫描暂存内容。

## 安全修复预览

```bash
promptrecon patch settings.py --line 12 --env-var SERVICE_TOKEN
promptrecon patch settings.py --line 12 --env-var SERVICE_TOKEN --apply
```

默认只显示脱敏预览，只有明确指定 `--apply` 才会原子写入，绝不生成包含真实秘密的修复文件。

## 开发

```bash
python -m pytest
ruff check .
python -m mypy promptrecon
python -m build
```

## 许可证

MIT。详见 [LICENSE](./LICENSE) 和 [CHANGELOG](./CHANGELOG.md)。
