"""Example function-calling tools for the Anthropic provider.

Two small, safe, side-effect-free tools to demonstrate the tool-use loop end
to end. Add more tools here (and wire them into the tool-use loop in
app/providers/anthropic_provider.py) as the platform grows.
"""

import ast
import operator
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "name": "get_current_time",
        "description": (
            "Get the current date and time. Call this when the user asks "
            "what time or date it is right now."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "timezone": {
                    "type": "string",
                    "description": (
                        "IANA timezone name, e.g. 'America/New_York'. "
                        "Defaults to UTC if omitted."
                    ),
                }
            },
            "required": [],
        },
    },
    {
        "name": "calculate",
        "description": "Evaluate a basic arithmetic expression, e.g. '2 * (3 + 4)'.",
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Arithmetic expression to evaluate.",
                }
            },
            "required": ["expression"],
        },
    },
]

_BIN_OPS: dict[type, Any] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
}
_UNARY_OPS: dict[type, Any] = {ast.USub: operator.neg, ast.UAdd: operator.pos}


def _eval_node(node: ast.AST) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _BIN_OPS:
        return _BIN_OPS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPS:
        return _UNARY_OPS[type(node.op)](_eval_node(node.operand))
    raise ValueError("Unsupported expression")


def run_tool(name: str, tool_input: dict[str, Any]) -> str:
    """Execute a tool by name and return its result as a string.

    Called from the tool-use loop after Claude emits a `tool_use` block; the
    return value is sent back as the `tool_result` content.
    """
    if name == "get_current_time":
        tz_name = tool_input.get("timezone") or "UTC"
        try:
            now = datetime.now(ZoneInfo(tz_name))
        except Exception:
            return f"Unknown timezone: {tz_name}"
        return now.strftime("%Y-%m-%d %H:%M:%S %Z")

    if name == "calculate":
        expression = tool_input["expression"]
        try:
            tree = ast.parse(expression, mode="eval")
            return str(_eval_node(tree.body))
        except Exception as exc:
            return f"Error evaluating expression: {exc}"

    return f"Unknown tool: {name}"
