# file: promptrecon/rules/example_rules.py

# v0.3: 插件式规则
# 主程序会自动加载这个 RULE 字典

RULE = {
    "huggingface_api_leak": {
        "description": "Detects HuggingFace API keys (hf_...)",
        "regex": r"hf_[A-Za-z0-9]{30,}",
        "risk_score": 6.5,
        "needs_decode": False
    },
    
    "anthropic_key_leak": {
        "description": "Detects Anthropic API keys (sk-ant-...) (v0.3)",
        "regex": r"sk-ant-api03-[A-Za-z0-9_-]{95}",
        "risk_score": 9.0,
        "needs_decode": False
    },
    
    "long_base64_string": {
        "description": "Matches long Base64 strings that might be encoded prompts.",
        "regex": r'["\'][A-Za-z0-9+/]{200,}={0,2}["\']',
        "risk_score": 4.0,
        "needs_decode": True
    },
    
    "xml_template": {
        "description": "Matches <system> or <instruction> XML tags.",
        "regex": r'(<system>|<instruction>|<system_prompt>)([\s\S]{150,})(</system>|</instruction>|</system_prompt>)',
        "risk_score": 8.0,
        "needs_decode": False
    }
}
