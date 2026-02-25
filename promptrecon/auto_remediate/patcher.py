# file: promptrecon/auto_remediate/patcher.py
import re
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def auto_patch_file(filepath: str, snippet: str, var_name: str = "SECURE_PROMPT_KEY") -> bool:
    """
    Attempts to 'surgically' remove a leaked prompt from a source code file.
    It replaces the hardcoded string with an environment variable lookup
    and saves the extracted string to a local `.env.remediated` file.
    
    WARNING: Semiautomatic refactoring.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Build a safe Regex to find the snippet (handling possible quotes)
        safe_snippet = re.escape(snippet)
        
        # We look for the snippet inside quotes (single, double, or triple)
        # This is a basic AST-less naive replacement for demonstration.
        # A true implementation would use `libcst` or `ast` tools to rewrite the tree.
        pattern = re.compile(rf'([\"\'`]{{1,3}}){safe_snippet}([\"\'`]{{1,3}})')
        
        if not pattern.search(content):
            logger.warning(f"Could not reliably locate exact string bounds for patching in {filepath}")
            return False

        # Replace with os.environ
        # Add import os if not present
        if "import os" not in content and "from os import" not in content:
            content = "import os\n" + content

        # Replace the hardcoded string with an env lookup
        replacement = f'os.environ.get("{var_name}", "MISSING_PROMPT")'
        new_content = pattern.sub(replacement, content, count=1)
        
        # Save patched file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
            
        # Log the extracted secret mapping
        env_dump_file = ".env.remediated"
        with open(env_dump_file, 'a', encoding='utf-8') as env_f:
            env_f.write(f"{var_name}=\"{snippet}\"\n")
            
        logger.info(f"[Auto-Remediation] Mapped extracted string to {var_name} in {env_dump_file}")
        return True
        
    except Exception as e:
        logger.error(f"[Auto-Remediation] Patch failed for {filepath}: {e}")
        return False
