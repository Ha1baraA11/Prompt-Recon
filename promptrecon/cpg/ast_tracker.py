# file: promptrecon/cpg/ast_tracker.py
import ast
import os
from collections import defaultdict

# Common prompt variable names to look for
PROMPT_VARIABLE_NAMES = [
    "system_prompt", "prompt", "system_instruction", "assistant_prompt",
    "meta_prompt", "api_system_prompt", "chat_system", "system_msg",
    "instruction", "system_message", "assistant_instruction"
]

# API call patterns to track
API_CALL_PATTERNS = [
    "openai.ChatCompletion.create",
    "openai.chat.completions.create",
    "client.chat.completions.create",
    "client.files.create",
    "anthropic.messages.create",
    "langchain.chat_models.ChatOpenAI",
    "ChatOpenAI",
]


class VariableTracker(ast.NodeVisitor):
    def __init__(self, target_variable="prompt"):
        self.target_variable = target_variable
        self.assignments = defaultdict(list)
        self.found = False
        self.sources = []

    def visit_Assign(self, node):
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == self.target_variable:
                self.found = True
                if isinstance(node.value, ast.Constant):
                    self.sources.append(node.value.value)
                elif isinstance(node.value, ast.JoinedStr):
                    parts = []
                    for val in node.value.values:
                        if isinstance(val, ast.Constant):
                            parts.append(val.value)
                        elif isinstance(val, ast.FormattedValue):
                            parts.append(f"{{{ast.unparse(val.value)}}}")
                    self.sources.append("".join(parts))
        self.generic_visit(node)


class APICallTracker(ast.NodeVisitor):
    """Track LLM API call sites in the code."""

    def __init__(self):
        self.calls = []

    def visit_Call(self, node):
        # Check for attribute calls like openai.ChatCompletion.create
        if isinstance(node.func, ast.Attribute):
            full_name = self._get_attr_name(node.func)
            if any(pattern in full_name for pattern in API_CALL_PATTERNS):
                self.calls.append({
                    "type": "api_call",
                    "name": full_name,
                    "line": node.lineno
                })
        # Check for direct names like ChatOpenAI(...)
        elif isinstance(node.func, ast.Name):
            if node.func.id in [p.split(".")[-1] for p in API_CALL_PATTERNS]:
                self.calls.append({
                    "type": "api_call",
                    "name": node.func.id,
                    "line": node.lineno
                })
        self.generic_visit(node)

    def _get_attr_name(self, node):
        parts = []
        while isinstance(node, ast.Attribute):
            parts.append(node.attr)
            node = node.value
        if isinstance(node, ast.Name):
            parts.append(node.id)
        return ".".join(reversed(parts))


def trace_variable_in_file(filepath, variable_name="system_prompt"):
    """
    Attempt to trace the value of a specific variable across the AST of a file.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=filepath)

        tracker = VariableTracker(target_variable=variable_name)
        tracker.visit(tree)

        return tracker.sources
    except Exception as e:
        return []


def trace_api_calls_in_file(filepath):
    """Find all LLM API call sites in a file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=filepath)

        tracker = APICallTracker()
        tracker.visit(tree)

        return tracker.calls
    except Exception:
        return []


def build_project_cpg(directory):
    """
    Build a Code Property Graph by extracting prompt variables and API call sites.
    """
    graph_data = {}
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                prompts = []
                calls = []

                # Track all common prompt variable names
                for var_name in PROMPT_VARIABLE_NAMES:
                    found = trace_variable_in_file(filepath, var_name)
                    prompts.extend(found)

                # Track API call sites
                calls = trace_api_calls_in_file(filepath)

                if prompts or calls:
                    graph_data[filepath] = {
                        "prompts": prompts,
                        "api_calls": calls
                    }
    return graph_data
