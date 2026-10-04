"""Tool failures must reach the model, not be masked as a crash.

The MCP SDK (mcp==2.1.1) surfaces the message of a `ToolError` to the caller and
treats ANY other exception as a crash, replacing it with a bare
"Error executing tool <name>". Raising RuntimeError therefore silently discarded
the API's error envelope - code, message, and the `recovery_action` hint the
README and docs/13 promise agents can self-correct from.

These checks read the source (they need no network and no API key); the behaviour
itself is exercised through the SDK in tests/test_tools.py.
"""

import ast
from pathlib import Path

SERVER = Path(__file__).resolve().parent.parent / "mcp_server" / "server.py"


def _tree() -> ast.Module:
    return ast.parse(SERVER.read_text())


def _raises_in_handlers() -> list[str]:
    """Every exception type name raised from an `except` block in server.py."""
    names: list[str] = []
    for node in ast.walk(_tree()):
        if not isinstance(node, ast.ExceptHandler):
            continue
        for inner in ast.walk(node):
            if isinstance(inner, ast.Raise) and isinstance(inner.exc, ast.Call):
                func = inner.exc.func
                if isinstance(func, ast.Name):
                    names.append(func.id)
    return names


def test_tool_handlers_raise_tool_error():
    raised = _raises_in_handlers()
    assert raised, "no raises found in server.py except-handlers — test is stale"
    assert set(raised) == {"ToolError"}, (
        f"tool handlers must raise ToolError so the message reaches the model; "
        f"found {sorted(set(raised))}"
    )


def test_tool_error_is_imported_from_the_sdk():
    imports = {
        f"{node.module}.{alias.name}"
        for node in ast.walk(_tree())
        if isinstance(node, ast.ImportFrom) and node.module
        for alias in node.names
    }
    assert "mcp.server.mcpserver.exceptions.ToolError" in imports


def test_nothing_raises_runtimeerror():
    """A RuntimeError raised anywhere here would be masked as a crash.

    AST-based on purpose: the word appears in an explanatory comment, and a
    substring check would fail on the comment that documents the rule.
    """
    raised = {
        node.exc.func.id
        for node in ast.walk(_tree())
        if isinstance(node, ast.Raise)
        and isinstance(node.exc, ast.Call)
        and isinstance(node.exc.func, ast.Name)
    }
    assert "RuntimeError" not in raised
