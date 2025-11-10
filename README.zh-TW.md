<div align="center">

**[简体中文](./README.md)** | **[English](./README.en.md)** | **[繁體中文]**

</div>

# 🚀 Prompt-Recon (v1.0)

![AI 安全](https://img.shields.io/badge/領域-AI安全-red)
![版本](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![授權](https://img.shields.io/badge/license-MIT-green)

一個插件驅動的、多線程的 AI 系統提示詞（System Prompt）及其他機密資訊的硬編碼掃描器。

本工具專為安全研究員、紅隊成員和 DevSecOps 團隊設計，用於審計程式碼庫中的“提示詞洩露”——這是一種新興且關鍵的 AI 安全漏洞。

## 核心功能 (v1.0)

- **多線程掃描**: (功能 #2) 使用 `ThreadPoolExecutor` 高速掃描數千個檔案。
- **插件式規則**: (功能 #1) 自動從 `promptrecon/rules/` 目錄載入所有規則插件。
- **進階風險評分**: (功能 #5) 基於關鍵字和檔案路徑（如 `main` vs `dev` 分支），為每個發現計算風險評分 (0-10)。
- **L3 語義驗證**: (功能 #3, #4) 不止是 Regex。整合了智能 Base64 解碼和語義分析 (`looks_like_prompt`)，大幅減少誤報。
- **CI/CD 与合规**: (功能 #5, #7, #8, #9) 支援 `.promptignore` 忽略列表、`--safe` 安全模式、審计日誌以及 CI/CD 友好的退出碼。
- **豐富格式報告**: (功能 #4, #6) 在控制台輸出精美的 `rich` 表格，并支援生成 `CSV`, `Markdown`, 和 `JSONL` 報告。

## 安裝

1.  克隆本倉庫:

    ```bash
    git clone https://github.com/Ha1baraA11/Prompt-Recon.git
    cd prompt-recon
    ```

2.  (推薦) 建立虛擬環境:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
3.  安裝依賴，并以“可編輯”模式安裝本工具:

    ```bash
    # 安裝核心依賴
    pip install rich gitpython
    
    # 安裝工具
    pip install -e .
    ```

## 使用方法

安裝後，`promptrecon` 命令將全域可用。

```bash
# 掃描一個本地目錄
promptrecon -d /path/to/your/codebase

# 掃描一個公開的 GitHub 倉庫 (將自動克隆)
promptrecon -u [https://github.com/user/vulnerable-repo](https://github.com/user/vulnerable-repo)

# 生成多種報告
promptrecon -d . --md report.md --csv report.csv --jsonl results.jsonl

# 以 --safe 模式運行 (跳過官方倉庫)
promptrecon -u [https://github.com/openai/gpt-3](https://github.com/openai/gpt-3) --safe

# 在 CI/CD 中使用 (如發現嚴重風險，將以退出碼 3 失败)
promptrecon -d .
```
