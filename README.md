# Datavidence Financials — MCP Server

<!-- mcp-name: ai.datavidence/datavidence-financials -->

**Normalized US-GAAP financial statements for every SEC XBRL filer — point-in-time, as originally reported — as MCP tools for your AI agent (or a plain REST API).**

[![PyPI](https://img.shields.io/pypi/v/datavidence-financials.svg)](https://pypi.org/project/datavidence-financials/)
[![Python versions](https://img.shields.io/pypi/pyversions/datavidence-financials.svg)](https://pypi.org/project/datavidence-financials/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![MCP registry](https://img.shields.io/badge/MCP%20registry-ai.datavidence%2Fdatavidence--financials-6f42c1.svg)](https://registry.modelcontextprotocol.io)
[![smithery badge](https://smithery.ai/badge/datavidence/datavidence-financials)](https://smithery.ai/servers/datavidence/datavidence-financials)

Language models are good at reasoning about financial statements and bad at *getting* them. SEC EDGAR has the data, but its XBRL is a thicket of inconsistent tags, renamed concepts, and per-filer quirks — so agents either hallucinate the numbers or you spend weeks building a normalization layer. This is that layer: your agent asks for a company's financials and gets a clean, consistent answer — over the **Model Context Protocol**, or as a plain **REST API**.

> ⭐ **If this is useful, please star the repo.** It's a solo, early project, and stars are how other developers find it.

![Claude calls the Datavidence Financials get_revisions tool: Pfizer's FY2019 revenue as filed ($51.75B) and as it reads today ($40.9B), with links to the SEC filings](https://raw.githubusercontent.com/datavidence/datavidence-financials-mcp/main/docs/demo.gif)

This is the open-source, AI-native layer for the [**Datavidence Financials API**](https://financials.datavidence.ai) — a standalone stdio server that forwards over HTTPS to the REST API (bring your own key). The connector is MIT-licensed; the underlying API is a commercial service.

## Try it in 30 seconds (no signup)

Run it with no clone using [uv](https://docs.astral.sh/uv/) — it installs into a throwaway environment:

```bash
FL_API_KEY=sandbox_demo_key uvx datavidence-financials
```

`sandbox_demo_key` returns sample data with **no signup** — good for a first run. Set `FL_API_KEY` to your real key for live SEC data. The server speaks MCP over stdio, so an MCP client (e.g. Claude Desktop, below) launches it.

Or install it as a persistent tool with pipx:

```bash
pipx install datavidence-financials
FL_API_KEY=sandbox_demo_key datavidence-financials
```

## Why it's different

- **Point-in-time, as originally reported.** Pass an `as_of` date and you get the figures as they stood then — no look-ahead bias from later restatements. The thing backtests quietly get burned without.
- **Normalized to one schema.** EDGAR's XBRL tags drift between filers and change over the years. We map them to a single US-GAAP income statement, balance sheet, and cash flow — including the awkward cases (noncontrolling interest, mezzanine/temporary equity, non-calendar fiscal years) — so you never parse a filing.
- **Every SEC XBRL filer.** Coverage is the whole SEC XBRL universe (~2009 to present), fetched and normalized on demand — any CIK with XBRL facts, not a curated subset.
- **Source-linked, too.** Turn on provenance and every value carries its SEC accession, filed date, and a direct EDGAR URL — so the model cites the filing instead of inventing a number.

Honest scope: US-GAAP only (IFRS filers return a clear "unsupported" signal rather than wrong numbers); XBRL-era history (~2009 onward). And when a company reorganizes under a new holding entity, SEC's ticker map points only at the successor CIK — the earlier years stay under the predecessor, so the error tells you and you pass `cik=` directly.

## Tools

- **`get_financials`** — normalized income statement + balance sheet + cash flow
  for one company and fiscal year, from SEC EDGAR XBRL. Supports `as_of`
  (point-in-time, as originally reported), `include_provenance` (per-value SEC
  accession, filed date, and direct EDGAR source URL), and `include_ratios`
  (margins, ROA/ROE, leverage).
- **`get_financials_batch`** — the same, for up to 25 companies in one call
  (comma-separated tickers/CIKs). Per-symbol results; counts as a single quota
  unit, so one bad symbol never fails the batch.
- **`list_filings`** — a company's recent SEC filings (newest first) from the
  EDGAR submissions index; filter by form (e.g. `10-K`). Use it to discover which
  fiscal years are available before calling `get_financials`.
- **`get_revisions`** — how a fiscal year's figures CHANGED across filings: every
  reported value with its filing date, form, SEC accession and EDGAR link, plus
  whether it was restated and by how much. Pfizer's FY2019 revenue was filed at
  $51.75B in 2020 and restated to $40.9B by 2022 — this is how you see that.
- **`search_companies`** — find a ticker and CIK by ticker or company name, for
  when you have "Berkshire" and need `BRK-B`. Use it before the tools above,
  which all require an identifier.
- **`get_usage`** — the key's monthly quota (tier, used, remaining, reset). Free
  to call; consumes no quota.

Errors surface the API's `recovery_action` hint, so agents self-correct.

## Claude Desktop

Add to `claude_desktop_config.json`, then fully quit (Cmd+Q) and reopen Claude
Desktop — the tools appear:

```json
{
  "mcpServers": {
    "datavidence-financials": {
      "command": "uvx",
      "args": ["datavidence-financials"],
      "env": { "FL_API_KEY": "sandbox_demo_key" }
    }
  }
}
```

Then ask, e.g., *"Get AAPL's FY2023 income statement, balance sheet, and cash flow with ratios."* Swap in your real key for live data.

## Configuration (environment variables)

| Variable | Default | Notes |
| --- | --- | --- |
| `FL_API_KEY` | _(none)_ | Your API key. `sandbox_demo_key` = no-signup trial (sample data). |
| `FL_API_BASE_URL` | `https://api.financials.datavidence.ai` | Point at a marketplace gateway for metered BYOK access. |
| `FL_API_KEY_HEADER` | `X-API-Key` | Header to send the key in (e.g. `X-RapidAPI-Key` for the RapidAPI gateway). |
| `FL_API_TIMEOUT` | `30` | Per-request timeout, in seconds. |

## Getting live data

The demo key returns sample data. For live figures, grab a key on [RapidAPI](https://rapidapi.com/datavidence-ykNLbvGmT/api/datavidence-financials-api): **Free** (1,500 calls/mo), **Pro** ($29 / 50k), **Business** ($99 / 300k). Full feature parity across tiers — they differ only by monthly call volume.

For a metered marketplace channel, point `FL_API_BASE_URL` at the gateway endpoint and set `FL_API_KEY` / `FL_API_KEY_HEADER` to the gateway's key/header (BYOK), so calls are metered by the marketplace rather than hitting the origin directly.

## Run from source

```bash
pip install -e .
FL_API_KEY=sandbox_demo_key python -m mcp_server.server   # stdio transport
```

## Feedback

Found a company where the numbers come back wrong, or a field/tool you need? **[Open an issue](https://github.com/datavidence/datavidence-financials-mcp/issues)** — the normalization edge cases are exactly the feedback that makes this better, and I read every one.

## Links

- **Site & docs:** https://financials.datavidence.ai
- **MCP quickstart:** https://financials.datavidence.ai/mcp
- **MCP registry:** `ai.datavidence/datavidence-financials`
- **PyPI:** https://pypi.org/project/datavidence-financials/
- **Get a key (RapidAPI):** https://rapidapi.com/datavidence-ykNLbvGmT/api/datavidence-financials-api
- **Security:** see [`SECURITY.md`](SECURITY.md) to report a vulnerability privately.

## License

MIT © 2026 Datavidence LLC — see [LICENSE](LICENSE). The connector is
open-source; the underlying Datavidence Financials API is a commercial service.
