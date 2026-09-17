"""Standalone MCP server for the Datavidence Financials API.

A separate component (its own dependencies) that exposes the API as MCP tools for
LLM agents and forwards over HTTP to the REST API — so the core service keeps its
pinned deps and the MCP layer stays independently deployable (see docs/13).
"""
