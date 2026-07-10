<p align="center">
  <img src="assets/logo.png" alt="Prompt-Recon 標誌" width="200">
</p>

<h1 align="center">Prompt-Recon</h1>

<p align="center">
  <strong>適合個人儲存庫與小型團隊的離線 secrets 掃描器</strong><br>
  檢查工作樹、暫存 blob 與本機可達的 Git 歷史，不會將候選內容送到任何地方。
</p>

<p align="center">
  <a href="./README.md">English</a> · <a href="./README.zh-CN.md">简体中文</a> · <a href="./README_ja.md">日本語</a> · <a href="./README_ko.md">한국어</a> · <a href="./README_es.md">Español</a> · <a href="./README_pt-BR.md">Português</a> · <a href="./README_ru.md">Русский</a> · <a href="./README_fr.md">Français</a> · <a href="./README_de.md">Deutsch</a>
</p>

---

## 功能

- 掃描檔案、暫存 blob 與 Git 歷史，不 checkout 舊版本。
- 內建 AWS、GitHub、GitLab、OpenAI、Anthropic、Hugging Face、Slack、Stripe、npm、PyPI、Google API、私鑰、JWT、資料庫 URL 與一般憑證賦值規則。
- 主控台與機器報告一律脫敏；baseline 只保存指紋。
- 支援 `.gitignore`、`.promptignore`、TOML 設定、行內 allow 標記，以及 SARIF、JSONL、CSV、Markdown 報告。

## 需求

- Python 3.10–3.13
- 暫存區與歷史掃描需要 Git

## 安裝

```bash
python -m pip install promptrecon
```

本機開發：

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

支援 `console`、`jsonl`、`csv`、`markdown` 與 `sarif`。退出碼：`0` 表示沒有新的未納入 baseline 的命中，`1` 表示仍有命中，`2` 表示設定、Git 或執行錯誤。

## Baseline 與設定

```bash
promptrecon baseline create .
promptrecon baseline audit
promptrecon baseline update .
```

Baseline 不保存秘密正文；已有檔案必須明確指定 `--force` 才能覆寫。複製 `.promptrecon.toml.example` 為 `.promptrecon.toml` 以設定排除路徑與資料化自訂規則。可使用 `# promptrecon: allow` 或 `# promptrecon: allow-next-line` 標記刻意接受的命中。

## Git Hook

```bash
promptrecon hook install
promptrecon hook run
promptrecon hook uninstall
```

安裝時不會靜默覆蓋既有的第三方 hook，hook 只掃描暫存內容。

## 安全修復預覽

```bash
promptrecon patch settings.py --line 12 --env-var SERVICE_TOKEN
promptrecon patch settings.py --line 12 --env-var SERVICE_TOKEN --apply
```

預設只顯示脫敏預覽，只有明確指定 `--apply` 才會原子寫入，絕不產生含有真實秘密的修復檔案。

## 開發

```bash
python -m pytest
ruff check .
python -m mypy promptrecon
python -m build
```

## 授權

MIT。詳見 [LICENSE](./LICENSE) 與 [CHANGELOG](./CHANGELOG.md)。
