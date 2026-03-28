<div align="center">

**[简体中文]** | **[English](./README.en.md)** | **[繁體中文]**

</div>

# Prompt-Recon

本地程式碼敏感資訊掃描與 Git 提交前攔截工具。

用於在程式碼提交前偵測硬編碼的 API Key、Token、密碼等敏感憑證，從源頭防止外洩。

## 核心功能

- **規則驅動掃描**：使用 Python 標準庫正則，掃描程式碼目錄中的硬編碼憑證（OpenAI API Key、GitHub Token、`.env` 檔案等）。
- **Git Pre-commit Hook**：將掃描封裝為 Git 鉤子，commit 時自動觸發，偵測到敏感詞則阻斷提交。
- **僅掃描暫存檔案**：Hook 只掃描 `git diff --cached` 回傳的已暫存檔案（staged blob），不掃描整個倉庫，速度快。
- **輔助脫敏**：自動將明文憑證替換為 `os.environ.get()` 格式。

## 安裝

```bash
git clone https://github.com/Ha1baraA11/Prompt-Recon.git
cd Prompt-Recon
pip install -e .
```

安裝後 `promptrecon` 命令全局可用，也可使用：

```bash
python3 -m promptrecon scan -d .
```

## 目錄掃描

```bash
# 掃描目前目錄
promptrecon scan -d .

# 產生報告
promptrecon scan -d . --jsonl results.jsonl
```

## Hook 安裝

```bash
# 安裝 pre-commit hook（自動攔截含敏感資訊的提交）
python3 scripts/install_pre_commit_hook.py
```

安裝後，每次 `git commit` 自動掃描已暫存檔案（staged blob），發現敏感詞則阻斷提交。支援掃描 `.env`、`.py`、`.json`、`.yaml` 等檔案類型。

## 提交攔截範例

```bash
$ echo 'api_key = "sk-mock-1234567890abcdefghijklmnop"' > test.py
$ git add test.py
$ git commit -m "add key"
[BLOCKED] test.py: generic_secret:1 api_key = "sk-mock-123...

Blocked 1 file(s). Use --no-verify to bypass.
```

## 已知限制

- 正則掃描存在誤報和漏報可能，適合作為開發流程第一道卡點。
- 目前規則以內建 Python 字典形式提供，後續可擴展為規則檔案。
- 輔助脫敏為字串替換，無法保證語意完全等價。

## 架構說明

```
promptrecon/
  hooks/
    pre_commit.py       — Hook 主邏輯
  rules/
    builtin.py          — 內建規則字典
  core.py               — 統一掃描核心
  cli.py                — CLI 入口（scan / patch）
  __main__.py           — python3 -m 入口
scripts/
  install_pre_commit_hook.py  — Hook 安裝腳本
```

---

[![Stargazers over time](https://starchart.cc/Ha1baraA11/Prompt-Recon.svg?variant=dark)](https://starchart.cc/Ha1baraA11/Prompt-Recon)
