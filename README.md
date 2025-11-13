<div align="center">

**[简体中文]** | **[English](./README.en.md)** | **[繁體中文](./README.zh-TW.md)**

</div>

# 🚀 Prompt-Recon (v1.0)

![AI 安全](https://img.shields.io/badge/领域-AI安全-red)
![版本](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![许可证](https://img.shields.io/badge/license-MIT-green)

一个插件驱动的、多线程的 AI 系统提示词（System Prompt）及其他秘密信息的硬编码扫描器。

本工具专为安全研究员、红队成员和 DevSecOps 团队设计，用于审计代码库中的“提示词泄露”——这是一种新兴且关键的 AI 安全漏洞。

## 核心功能 (v1.0)

- **多线程扫描**: (功能 #2) 使用 `ThreadPoolExecutor` 高速扫描数千个文件。
- **插件式规则**: (功能 #1) 自动从 `promptrecon/rules/` 目录加载所有规则插件。
- **高级风险评分**: (功能 #5) 基于关键词和文件路径（如 `main` vs `dev` 分支），为每个发现计算风险评分 (0-10)。
- **L3 语义验证**: (功能 #3, #4) 不止是 Regex。集成了智能 Base64 解码和语义分析 (`looks_like_prompt`)，大幅减少误报。
- **CI/CD 与合规**: (功能 #5, #7, #8, #9) 支持 `.promptignore` 忽略列表、`--safe` 安全模式、审计日志以及 CI/CD 友好的退出码。
- **富格式报告**: (功能 #4, #6) 在控制台输出精美的 `rich` 表格，并支持生成 `CSV`, `Markdown`, 和 `JSONL` 报告。

## 安装

1.  克隆本仓库:

    ```bash
    git clone https://github.com/Ha1baraA11/Prompt-Recon.git
    cd prompt-recon
    ```

2.  (推荐) 创建虚拟环境:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
3.  安装依赖，并以“可编辑”模式安装本工具:

    ```bash
    # 安装核心依赖
    pip install rich gitpython
    
    # 安装工具
    pip install -e .
    ```

## 使用方法

安装后，`promptrecon` 命令将全局可用。

```bash
# 扫描一个本地目录
promptrecon -d /path/to/your/codebase

# 扫描一个公开的 GitHub 仓库 (将自动克隆)
promptrecon -u [https://github.com/user/vulnerable-repo](https://github.com/user/vulnerable-repo)

# 生成多种报告
promptrecon -d . --md report.md --csv report.csv --jsonl results.jsonl

# 以 --safe 模式运行 (跳过官方仓库)
promptrecon -u [https://github.com/openai/gpt-3](https://github.com/openai/gpt-3) --safe

# 在 CI/CD 中使用 (如发现严重风险，将以退出码 3 失败)
promptrecon -d .
```
## Stargazers over time
[![Stargazers over time](https://starchart.cc/Ha1baraA11/Prompt-Recon.svg?variant=dark)](https://starchart.cc/Ha1baraA11/Prompt-Recon)
