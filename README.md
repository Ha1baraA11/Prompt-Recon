<div align="center">

**[简体中文]** | **[English](./README.en.md)** | **[繁體中文](./README.zh-TW.md)**

</div>

# 🚀 Prompt-Recon (v2.0)

![AI 安全](https://img.shields.io/badge/领域-AI安全-red)
![版本](https://img.shields.io/badge/version-2.0.0-blue)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![许可证](https://img.shields.io/badge/license-MIT-green)

Prompt-Recon v2.0 升级为全生命周期的 AI 资产防御与审计系统。

本工具专为安全研究员、红队成员和 DevSecOps 团队设计，用于拦截、追踪和修复代码库与运行时流量中的“提示词泄露”及机密数据硬编码漏洞。

## 核心功能升级 (v2.0)

- 🛡️ **运行时动态网关 (Sentinel Proxy)**: 在发往大模型（如 OpenAI、Claude）前的 ASGI 网络层截听流量，实现运行时防御阻断。
- 🧠 **端侧多维向量分析**: 集成 `bge-small-zh` 等嵌入模型，通过向量空间相似度检测变异与混淆的提示词，作为正则表达式扫描的补充。
- ⚖️ **LLM 沙盒验证 (LLM Validation)**: 借助 LangChain 框架链式调用验证节点，利用大语言模型评估疑似漏洞，降低误报率。
- 🕸️ **AST/CPG 数据流追踪**: 在 Python 抽象语法树（AST）级别追踪变量定义与函数调用，重构散乱的代码片段。
- 👥 **Git 安全审计**: 结合 `GitPython`，提取引发泄漏问题的代码提交历史特征，协助构建工程风险预警。
- 💧 **零宽防盗水印 (Zero-Width Watermarking)**: 运用不可见零宽字符对核心 Prompt 进行隐写标识，协助内部资产溯源。
- 🤖 **自动代码修复 (Auto-Remediation)**: 检测到硬编码后，系统可自动使用 `os.environ` 抽离明文并重构成安全的 `.env.remediated` 文件。
- ⌨️ **多模式智能入口**: 提供 `scan`、`patch` 和 `sentinel` 三种主要的控制台交互模式。

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
