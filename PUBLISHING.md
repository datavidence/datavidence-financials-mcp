# Releasing & directory listings

The runbook for shipping a new version of `datavidence-financials`. Written after
the 0.1.3 release (2026-09-22); the earlier version of this file described the
first publish and had gone stale in ways that would break a release — see
"Namespace: what does not work" below.

Everything here runs on your Mac, from this repo. Nothing touches the API box:
this is a package release, not a deploy.

---

## Part A — Bump the version in four places

They must agree, or the registry will publish metadata that points at a PyPI
version that does not exist.

| File | Field |
| :--- | :--- |
| `mcp_server/__init__.py` | `__version__` — what the running server reports as `serverInfo.version` |
| `pyproject.toml` | `version` — the PyPI package |
| `server.json` | `version` **and** `packages[0].version` (two places in one file) |
| `manifest.json` | `version` — the MCP Bundle (.mcpb) published to Smithery |

---

## Part B — Build and publish to PyPI

Release tooling does not live in either project venv (`.venv` is the core API,
`mcp_server/.venv` runs the server). Use a throwaway one — Homebrew Python
refuses a bare `pip install` outside a venv anyway:

```bash
cd datavidence-financials-mcp
python3 -m venv /tmp/relenv && source /tmp/relenv/bin/activate
pip install -q --upgrade build twine

rm -rf dist build *.egg-info
python -m build
twine check dist/*
```

Before uploading — PyPI will not let you replace a version once it is up, so
confirm the artifact carries what you think it does:

```bash
unzip -p dist/datavidence_financials-<version>-py3-none-any.whl mcp_server/__init__.py | grep __version__
```

Then:

```bash
twine upload dist/*     # ~/.pypirc, __token__ + a project-scoped PyPI token in Keychain
```

**Verify:** `curl -s https://pypi.org/pypi/datavidence-financials/json | grep -o '"version":"[^"]*"' | head -1`
shows the new version. PyPI's JSON API caches for a minute or two after upload;
publishing to the registry before it propagates fails validation, so wait for
this to flip before Part C.

---

## Part C — Publish to the official MCP registry

Registry name: **`ai.datavidence/datavidence-financials`**, authorized by **DNS**
on `datavidence.ai` (a `v=MCPv1; k=ed25519; p=…` TXT record on the apex, in
Cloudflare). The Ed25519 key lives outside this repo at
`api-framework/datavidence-mcp-dns/key.pem`.

`mcp-publisher` wants the 32-byte seed as hex, not the PEM. Derive it into a
variable so the key stays out of your shell history:

```bash
KEY_HEX=$(openssl pkey -in ../datavidence-mcp-dns/key.pem -outform DER | tail -c 32 | xxd -p -c 32)
# sanity: echo ${#KEY_HEX} -> 64
mcp-publisher login dns --domain datavidence.ai --private-key "$KEY_HEX"
unset KEY_HEX

mcp-publisher publish          # reads ./server.json
```

**Verify:**

```bash
curl -s "https://registry.modelcontextprotocol.io/v0/servers?search=datavidence"
```

The newest entry should show the new version with `status: active`. Older
versions stay listed as history — that is normal.

### Namespace: what does not work

`io.github.datavidence/*` was tried first and **failed**. The `datavidence` org
restricts third-party OAuth apps, so `mcp-publisher login github` only ever
granted the personal namespace (`io.github.vijaykas/*`), even with public org
membership and the restriction temporarily lifted. DNS verification is the
working path. It is also **not** `com.datavidence` — the namespace is the
reverse-DNS of the `.ai` domain we actually control.

---

## Part D — Tag the GitHub release

Glama scores listings partly on having stable releases, and docked this one for
"no stable release" until a tag existed:

```bash
gh release create v<version> --title "v<version>" --notes "<what changed>"
```

---

## Part E — Directories (status as of 2026-09-22)

None of these take a per-release action; they ingest the registry and crawl this
repo on their own cadence.

- **Glama** — listed and **claimed**. Ownership is recognized via `glama.json`
  (`maintainers`) at the repo root, because a personal GitHub login alone does not
  grant maintainer status on an org-owned repo. The listing avatar is derived from
  the GitHub **org** avatar; there is no upload field.
- **PulseMCP** — **not listed, and not pending.** Their submit page (last updated
  2026-09-03) states that new submissions *and changes to existing listings* are
  paused indefinitely while they rework their ingestion pipeline, with no reopen
  date. Their own guidance is to publish to the official registry, which we do in
  Part C. Nothing to chase; re-check occasionally.
- **Smithery** — does **not** ingest the registry (still absent 6 days after
  publishing there). It takes either a remote Streamable-HTTP URL or an **MCP
  Bundle**. We publish the bundle, so this one IS a per-release step:

  ```bash
  npm install -g @anthropic-ai/mcpb        # once
  mcpb validate manifest.json
  mcpb pack . dist/datavidence-financials-<version>.mcpb
  npx -y @smithery/cli@latest auth login   # once, opens a browser
  npx -y @smithery/cli@latest mcp publish dist/datavidence-financials-<version>.mcpb -n datavidence/datavidence-financials
  ```

  Use the scoped package `@smithery/cli` — the unscoped `smithery` on npm is an
  unrelated old package. The bundle is `server.type: "uv"`: the host installs the
  dependencies from `pyproject.toml` and runs `run_server.py`, so nothing is
  vendored. `.mcpbignore` keeps docs (the 5.9 MB demo GIF) out of it. Attach the
  same `.mcpb` to the GitHub release (Part D) — Claude Desktop installs it with a
  double-click.
- **mcp.so** — **skipped** (decision 2026-09-17): the submit form is paid-only
  ($39, no free tier). Revisit only on a concrete demand signal.

Use `LISTINGS.md` for the title, descriptions, category and keywords wherever a
directory lets you edit them.

---

## Part F — Smoke-test what users will actually get

Install the published artifact in a clean environment and drive a real session,
rather than trusting the local checkout:

```bash
python3 -m venv /tmp/verifyenv && /tmp/verifyenv/bin/pip install "datavidence-financials==<version>"
```

Then speak JSON-RPC to it over stdio, keeping stdin **open** between messages —
the process exits on EOF, and a tool call that is still waiting on the network
dies with "Connection closed" if you pipe everything at once and close:

1. `initialize` → check `serverInfo.version` matches the release.
2. `tools/list` → four tools; no `ctx` parameter leaking into any input schema.
3. `tools/call get_financials` with `FL_API_KEY=sandbox_demo_key` → sample data.
4. `tools/call get_financials` with `year: 3` → the response must carry the full
   envelope, e.g. `[INVALID_YEAR_FORMAT] … Recovery: …`. A bare
   "Error executing tool get_financials" means a handler raised something other
   than `ToolError` and the SDK masked it as a crash — that regression shipped in
   0.1.2 and is guarded by `tests/test_mcp_tool_errors.py` in the core repo.
