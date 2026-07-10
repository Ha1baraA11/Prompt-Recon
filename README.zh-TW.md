# Prompt-Recon

Prompt-Recon 是離線 secrets 掃描器，可檢查工作樹、Git 暫存區與本地可達的 Git 歷史，偵測 API key、token、私鑰、資料庫憑證及高熵字串。候選憑證不會送出網路，報告只顯示脫敏值與指紋。

```bash
python -m pip install promptrecon
promptrecon scan .
promptrecon scan --staged
promptrecon scan --history
promptrecon scan . --format sarif --output results.sarif
```

退出碼為 `0`（沒有新增命中）、`1`（發現命中）或 `2`（工具/設定錯誤）。Baseline 只保存指紋：

```bash
promptrecon baseline create .
promptrecon baseline audit
promptrecon hook install
```

複製 `.promptrecon.toml.example` 為 `.promptrecon.toml` 可設定排除路徑與資料化自訂規則。修復預設只預覽，只有明確指定 `--apply` 才會寫入。

詳見 [CHANGELOG](./CHANGELOG.md)。採用 MIT License。
