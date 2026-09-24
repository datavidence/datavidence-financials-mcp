"""Standalone MCP server for the Datavidence Financials API.

A separate component (its own dependencies) that exposes the API as MCP tools for
LLM agents and forwards over HTTP to the REST API — so the core service keeps its
pinned deps and the MCP layer stays independently deployable (see docs/13).
"""

# Single source of truth for the running server's reported version: the package
# metadata in pyproject.toml and the registry entry in server.json are bumped to
# match on release. Surfaced to clients as serverInfo.version.
__version__ = "0.1.5"
