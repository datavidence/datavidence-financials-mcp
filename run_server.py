"""Entry point for the MCP Bundle (.mcpb). The bundle host runs this with
`uv run`, which installs the dependencies declared in pyproject.toml.
PyPI users run the `datavidence-financials` console script instead."""

from mcp_server.server import main

if __name__ == "__main__":
    main()
