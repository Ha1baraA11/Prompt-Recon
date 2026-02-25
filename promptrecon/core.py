# file: promptrecon/core.py

import os
import re
import importlib.util
import base64
import logging
from pathlib import Path
import fnmatch

def load_ignore_patterns(ignorefile=".promptignore"):
    patterns = []
    if os.path.exists(ignorefile):
        with open(ignorefile, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    patterns.append(line)
    # Default ignores
    patterns.extend(['.git/*', '*/.git/*', 'venv/*', '*/venv/*', '__pycache__/*'])
    return patterns

def should_ignore(filepath, patterns):
    path_str = str(filepath)
    for pattern in patterns:
        if fnmatch.fnmatch(path_str, pattern) or fnmatch.fnmatch(os.path.basename(path_str), pattern):
            return True
    return False


# --- v0.3 Feature #1: 插件式规则加载 ---
def load_rules_from_dir(rules_dir="promptrecon/rules"):
    """
    自动扫描 rules/ 目录, 加载所有 *.py 文件中的 RULE 字典
    """
    loaded_rules = {}
    if not os.path.exists(rules_dir):
        logging.warning(f"Rules directory not found: {rules_dir}")
        return {}

    for filename in os.listdir(rules_dir):
        if filename.endswith('.py') and not filename.startswith('__'):
            filepath = os.path.join(rules_dir, filename)
            module_name = f"promptrecon.rules.{filename[:-3]}"
            
            try:
                spec = importlib.util.spec_from_file_location(module_name, filepath)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                if hasattr(module, 'RULE'):
                    for rule_name, rule_data in module.RULE.items():
                        rule_data["regex"] = re.compile(rule_data["regex"], re.IGNORECASE | re.MULTILINE)
                        loaded_rules[rule_name] = rule_data
            except Exception as e:
                logging.error(f"Failed to load rule from {filename}: {e}")
                
    return loaded_rules

# --- v0.3 Feature #2: 文件过滤 (二进制/大文件) ---
def is_file_scannable(filepath):
    """
    检查文件是否太大, 或者是否为二进制
    """
    try:
        # 1. 检查文件大小
        if os.path.getsize(filepath) > 2 * 1024 * 1024:  # > 2MB
            return False
            
        # 2. 检查二进制 (通过 'null byte' 探测)
        with open(filepath, 'rb') as f:
            # latin-1 可以读取所有字节, 'ignore' 确保无错
            sample = f.read(4096).decode('latin-1', 'ignore')
            if '\x00' in sample:
                return False
                
    except (IOError, OSError):
        return False # 文件不可读
        
    return True

# --- v0.3 Feature #3: L3 语义验证层 ---
def looks_like_prompt(text):
    """
    L3 验证: 检查是否"像"一个 prompt
    """
    text_lower = text.lower()
    keywords = ["you are", "assistant", "instruction", "system", "confidential", "must not", "task is to"]
    hits = sum(1 for k in keywords if k in text_lower)
    return hits >= 2 # 命中 2 个或以上关键词

# --- v0.3 智能 Base64 (来自 v0.2 的改进) ---
def decode_and_verify(encoded_string):
    encoded_string = encoded_string.strip('"\'')
    
    # 简单的 Base64 字符分布检查
    if not re.fullmatch(r'[A-Za-z0-9+/=]+', encoded_string):
        return None
    
    if len(encoded_string) < 100 or len(encoded_string) % 4 != 0:
        return None
        
    try:
        decoded_bytes = base64.b64decode(encoded_string)
        decoded_str = decoded_bytes.decode('utf-8')
        
        # 结合 L3 语义验证
        if looks_like_prompt(decoded_str):
            return decoded_str
    except Exception:
        pass
    return None

# --- v0.3 风险评分 (来自 v0.2 的改进) ---
def calculate_risk_score(match_data):
    base = match_data["rule"]["risk_score"]
    snippet = match_data["snippet"].lower()
    
    # 关键词权重
    if any(k in snippet for k in ["password", "token", "key", "confidential", "admin_"]):
        base += 2.5
    
    # 分支权重
    if "main" in match_data["file"] or "prod" in match_data["file"]:
        base += 1.0
        
    return min(base, 10.0)

# --- v0.3 核心扫描函数 ---
def scan_file(filepath, rules):
    local_findings = []
    if not is_file_scannable(filepath):
        return local_findings

    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
            for rule_name, rule_data in rules.items():
                regex = rule_data["regex"]
                
                for match in regex.finditer(content):
                    snippet = ""
                    risk_adjustment = 0
                    is_l3_verified = False
                    
                    if rule_data.get("needs_decode", False):
                        decoded_prompt = decode_and_verify(match.group(0))
                        if not decoded_prompt:
                            continue
                        snippet = f"Decoded: {decoded_prompt[:100]}..."
                        risk_adjustment = 3.0
                        is_l3_verified = True
                    else:
                        try:
                            snippet = f"{match.group(2)[:100]}..."
                        except IndexError:
                            snippet = f"{match.group(1)[:100]}..."

                    # --- v0.3 Feature #3: L3 验证明文 ---
                    if not is_l3_verified and looks_like_prompt(snippet):
                        risk_adjustment += 1.5 # 看起来像 prompt，增加风险

                    finding = {
                        "file": str(Path(filepath).relative_to(Path.cwd())), # 使用相对路径
                        "rule_name": rule_name,
                        "snippet": snippet.strip(),
                        "rule": rule_data
                    }
                    
                    finding["risk_score"] = calculate_risk_score(finding) + risk_adjustment
                    local_findings.append(finding)
                    
    except Exception:
        pass
    return local_findings
