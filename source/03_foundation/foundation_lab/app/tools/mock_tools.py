"""
Mock tools used to keep the Tool boundary explicit in phase 1.
"""

from __future__ import annotations

import ast
from datetime import datetime

from app.schemas import ToolResult


RULE_BOOK = {
    "quality": "Prefer clear module boundaries, simple tests, and explicit completion standards.",
    "retriever": "Retriever returns documents, not action side effects.",
    "tool": "Tool returns action results and can reach outside the model context.",
}


def _safe_eval(node: ast.AST) -> int | float:
    if isinstance(node, ast.Expression):
        return _safe_eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
        left = _safe_eval(node.left)
        right = _safe_eval(node.right)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        return left / right
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        value = _safe_eval(node.operand)
        return value if isinstance(node.op, ast.UAdd) else -value
    raise ValueError("Only simple arithmetic expressions are allowed.")


def run_calculator(expression: str) -> ToolResult:
    tree = ast.parse(expression, mode="eval")
    value = _safe_eval(tree)
    return ToolResult(tool_name="calculator", tool_input=expression, output=str(value))


def get_current_time() -> ToolResult:
    now = datetime.now().isoformat(timespec="seconds")
    return ToolResult(tool_name="current_time", tool_input="", output=now)


def lookup_rule(topic: str) -> ToolResult:
    matched = RULE_BOOK.get(topic.lower(), "No matching rule was found.")
    return ToolResult(tool_name="rule_lookup", tool_input=topic, output=matched)


def run_tool(tool_name: str, tool_input: str) -> ToolResult:
    if tool_name == "calculator":
        return run_calculator(tool_input)
    if tool_name == "current_time":
        return get_current_time()
    if tool_name == "rule_lookup":
        return lookup_rule(tool_input)
    raise ValueError(f"Unsupported tool: {tool_name}")
