# file: promptrecon/rules/builtin.py

# 内置规则字典，零外部依赖
# 格式与 load_rules_from_dir() 兼容，会被 pre-compiled

RULE = {
    "openai_api_key": {
        "description": "OpenAI API Key (sk-...)",
        "regex": r"sk-[a-zA-Z0-9]{32,}",
        "risk_score": 9.0,
        "needs_decode": False
    },

    "github_token": {
        "description": "GitHub Personal Access Token (ghp_...)",
        "regex": r"ghp_[a-zA-Z0-9]{36}",
        "risk_score": 9.0,
        "needs_decode": False
    },

    "generic_secret": {
        "description": "Generic secret assignment (password/token/secret/api_key = \"...\")",
        "regex": r"(?i)(password|token|secret|api_key)\s*=\s*['\"][^'\"]{8,}['\"]",
        "risk_score": 7.0,
        "needs_decode": False
    },
}


def load_builtin_rules():
    """
    加载内置规则，返回已编译 regex 的规则字典。
    供 pre-commit hook 直接调用。
    """
    import re
    loaded = {}
    for name, data in RULE.items():
        compiled = re.compile(data["regex"], re.IGNORECASE | re.MULTILINE)
        loaded[name] = {**data, "regex": compiled}
    return loaded
