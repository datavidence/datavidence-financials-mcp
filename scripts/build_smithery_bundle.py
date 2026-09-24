#!/usr/bin/env python3
"""Build the Smithery flavour of the MCP Bundle.

Smithery's registry requires every tool in the bundle's server card to carry an
``inputSchema`` (it returns 400 "expected object, received undefined" per tool
otherwise), but the MCPB manifest spec only allows ``name`` and ``description``
on a tool, and strict validators (``mcpb validate``, Claude Desktop) reject
anything more. So the committed manifest.json stays spec-clean, and this script
produces a Smithery-only bundle whose manifest has the live input schemas:

    python3 scripts/build_smithery_bundle.py
    # -> dist/datavidence-financials-<version>-smithery.mcpb

It starts the server under ``uv`` (sandbox key, no network needed), reads
``tools/list``, packs the spec-clean bundle with ``mcpb pack`` (so it is validated and
.mcpbignore applies), then swaps the enriched manifest into the archive. Requires ``uv`` and
``mcpb`` (npm install -g @anthropic-ai/mcpb).
"""

import json
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def live_tools() -> list[dict]:
    env = dict(os.environ, FL_API_KEY="sandbox_demo_key")
    proc = subprocess.Popen(
        ["uv", "run", "--directory", str(ROOT), "run_server.py"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        text=True, env=env,
    )

    def send(msg: dict) -> None:
        proc.stdin.write(json.dumps(msg) + "\n")
        proc.stdin.flush()

    try:
        send({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
            "protocolVersion": "2025-06-18", "capabilities": {},
            "clientInfo": {"name": "build_smithery_bundle", "version": "1"}}})
        proc.stdout.readline()
        send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        send({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        return json.loads(proc.stdout.readline())["result"]["tools"]
    finally:
        proc.terminate()


def main() -> None:
    manifest = json.loads((ROOT / "manifest.json").read_text())
    schemas = {t["name"]: t["inputSchema"] for t in live_tools()}
    declared = {t["name"] for t in manifest["tools"]}
    if declared != set(schemas):
        sys.exit(f"manifest tools {sorted(declared)} != server tools {sorted(schemas)}")
    for tool in manifest["tools"]:
        tool["inputSchema"] = schemas[tool["name"]]

    out = ROOT / "dist" / f"{manifest['name']}-{manifest['version']}-smithery.mcpb"
    out.parent.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        # Pack the spec-clean bundle first (validates it, applies .mcpbignore),
        # then swap in the enriched manifest: `mcpb pack` itself would reject it.
        clean = Path(tmp) / "clean.mcpb"
        subprocess.run(["mcpb", "pack", str(ROOT), str(clean)], check=True,
                       stdout=subprocess.DEVNULL)
        with zipfile.ZipFile(clean) as src, zipfile.ZipFile(
            out, "w", zipfile.ZIP_DEFLATED
        ) as dst:
            for item in src.infolist():
                data = src.read(item.filename)
                if item.filename == "manifest.json":
                    data = (json.dumps(manifest, indent=2) + "\n").encode()
                dst.writestr(item, data)
    print(f"wrote {out} ({out.stat().st_size} bytes, {len(schemas)} tools with inputSchema)")


if __name__ == "__main__":
    main()
