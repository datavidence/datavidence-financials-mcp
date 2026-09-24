"""Entry point for the MCP Bundle (.mcpb).

The bundle's mcp_config launches this with `uv run`, which installs the
dependencies declared in pyproject.toml, so nothing is vendored. PyPI users
run the `datavidence-financials` console script instead.

Hosts fill FL_* from the bundle's user_config. A host that has no value for an
optional field may pass it through empty or as the literal "${user_config.x}"
placeholder; treat both as unset so the built-in defaults apply, and fall back
to the public sandbox key so the server works out of the box.
"""

import os

for _name in ("FL_API_KEY", "FL_API_BASE_URL", "FL_API_KEY_HEADER", "FL_API_TIMEOUT"):
    _value = os.environ.get(_name, "")
    if not _value.strip() or _value.startswith("${"):
        os.environ.pop(_name, None)
os.environ.setdefault("FL_API_KEY", "sandbox_demo_key")

from mcp_server.server import main  # noqa: E402  (env must be cleaned first)

if __name__ == "__main__":
    main()
