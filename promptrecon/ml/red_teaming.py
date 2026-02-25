# file: promptrecon/ml/red_teaming.py
import os
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

# This implements the LLM Sandboxing Validator.
# It acts as a Blue Team Agent reviewing findings.

class RedTeamValidator:
    def __init__(self, model_name="gpt-4o-mini", api_key=None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            self.llm = None
        else:
            self.llm = ChatOpenAI(temperature=0, model=model_name, openai_api_key=self.api_key)

    def validate_snippet(self, filepath: str, snippet: str) -> dict:
        """
        Uses an LLM to logically determine if a specific text snippet from code
        is an actual System Prompt leak or just a false positive.
        """
        if not self.llm:
            return {"is_leak": False, "confidence": 0, "reason": "No API Key provided for LLM"}
            
        prompt = PromptTemplate.from_template(
            """You are a top-tier DevSecOps Agent assessing an alert from Prompt-Recon.
            
            We found the following string in the file `{filepath}`:
            
            ---
            {snippet}
            ---
            
            Is this an actual hardcoded AI System Prompt, persona instruction, or confidential LLM data leak? 
            Or is it a False Positive (e.g., standard code comment, unit test string, logging)?
            
            Respond strictly in the following JSON format:
            {{"is_leak": true/false, "confidence": 0-100, "reason": "short explanation"}}
            """
        )
        
        chain = prompt | self.llm | StrOutputParser()
        try:
            result_str = chain.invoke({"filepath": filepath, "snippet": snippet})
            import json
            # Extremely basic parsing for demo
            clean_str = result_str.strip().strip("```json").strip("```").strip()
            return json.loads(clean_str)
        except Exception as e:
            return {"is_leak": False, "confidence": 0, "reason": f"LLM error: {e}"}
