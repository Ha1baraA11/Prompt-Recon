<div align="center">

**[简体中文](./README.md)** | **[English](./README.en.md)** | **[繁體中文]**

</div>

# 🚀 Prompt-Recon (v2.0)

![AI 安全](https://img.shields.io/badge/領域-AI安全-red)
![版本](https://img.shields.io/badge/version-2.0.0-blue)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![授權](https://img.shields.io/badge/license-MIT-green)

Prompt-Recon v2.0 升級為全生命週期的 AI 資產防禦與稽核系統。

本工具專為安全研究員、紅隊成員和 DevSecOps 團隊設計，用於攔截、追蹤和修復程式碼庫與運行時流量中的“提示詞洩露”及機密資料硬編碼漏洞。

## 核心功能升級 (v2.0)

- 🛡️ **運行時動態網關 (Sentinel Proxy)**: 在發往大模型（如 OpenAI、Claude）前的 ASGI 網路層攔截流量，實現運行時防禦阻斷。
- 🧠 **端側多維向量分析**: 整合 `bge-small-zh` 等嵌入模型，透過向量空間相似度檢測變異與混淆的提示詞，作為正規表示式掃描的補充。
- ⚖️ **LLM 沙盒驗證 (LLM Validation)**: 藉助 LangChain 框架鏈式呼叫驗證節點，利用大型語言模型評估疑似漏洞，降低誤報率。
- 🕸️ **AST/CPG 資料流追蹤**: 在 Python 抽象語法樹（AST）層級追蹤變數定義與函式呼叫，重構散亂的程式碼片段。
- 👥 **Git 安全稽核**: 結合 `GitPython`，提取引發洩漏問題的程式碼提交歷史特徵，協助建構工程風險預警。
- 💧 **零寬防盜浮水印 (Zero-Width Watermarking)**: 運用不可見零寬字元對核心 Prompt 進行隱寫標識，協助內部資產溯源。
- 🤖 **自動程式碼修復 (Auto-Remediation)**: 檢測到硬編碼後，系統可自動使用 `os.environ` 抽離明文並重構為安全的 `.env.remediated` 檔案。
- ⌨️ **多模式智慧入口**: 提供 `scan`、`patch` 和 `sentinel` 三種主要的控制台互動模式。

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
