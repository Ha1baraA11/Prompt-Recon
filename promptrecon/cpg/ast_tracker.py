# file: promptrecon/cpg/ast_tracker.py
import ast
import os
from collections import defaultdict

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

def build_project_cpg(directory):
    """
    A simplified version of building a Code Property Graph by extracting
    all string assignments and function calls that might relate to LLM usage.
    """
    graph_data = {}
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                # Extremely simplified CPG tracking: just look for common prompt variables
                found_prompts = trace_variable_in_file(filepath, "system_prompt")
                found_prompts.extend(trace_variable_in_file(filepath, "prompt"))
                
                if found_prompts:
                    graph_data[filepath] = found_prompts
    return graph_data
