# Datavidence Financials — MCP Server

<!-- mcp-name: ai.datavidence/datavidence-financials -->

Normalized **US-GAAP financial statements from SEC EDGAR** — income statement,
balance sheet, and cash flow — exposed as **Model Context Protocol (MCP) tools**
for LLM agents (Claude Desktop, LangChain, and custom frameworks). Every value is
traceable to its source SEC filing, and figures can be pulled *as originally
reported* for any date (no look-ahead), for backtests.

This is the open-source, AI-native layer for the
[**Datavidence Financials API**](https://financials.datavidence.ai) — a
standalone stdio server that forwards over HTTPS to the REST API (bring your own
key). The connector is MIT-licensed; the underlying API is a commercial service.

## Quick start (no clone)

Run it with [uv](https://docs.astral.sh/uv/) — it installs into a throwaway
environment:

```bash
FL_API_KEY=sandbox_demo_key uvx datavidence-financials
```

`sandbox_demo_key` returns sample data with **no signup** — good for a first run.
Swap in your real key for live SEC data. Or install it as a persistent tool with
`pipx install datavidence-financials`.

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

Then ask, e.g., *"get AAPL's FY2023 financials with ratios."*

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
- **`get_usage`** — the key's monthly quota (tier, used, remaining, reset). Free
  to call; consumes no quota.

Errors surface the API's `recovery_action` hint, so agents self-correct.

## Configuration (environment variables)

| Variable | Default | Notes |
| --- | --- | --- |
| `FL_API_KEY` | _(none)_ | Your API key. `sandbox_demo_key` = no-signup trial (sample data). |
| `FL_API_BASE_URL` | `https://api.financials.datavidence.ai` | Point at a marketplace gateway for metered BYOK access. |
| `FL_API_KEY_HEADER` | `X-API-Key` | Header to send the key in (e.g. `X-RapidAPI-Key` for the RapidAPI gateway). |
| `FL_API_TIMEOUT` | `30` | Per-request timeout, in seconds. |

## Run from source

```bash
pip install -e .
FL_API_KEY=sandbox_demo_key python -m mcp_server.server   # stdio transport
```

## Links

- **API & docs:** https://financials.datavidence.ai
- **PyPI:** https://pypi.org/project/datavidence-financials/
- **Get a key (RapidAPI):** https://rapidapi.com/datavidence-ykNLbvGmT/api/datavidence-financials-api
- **Security:** see [`SECURITY.md`](SECURITY.md) to report a vulnerability privately.

## License

MIT © 2026 Datavidence LLC. The connector is open-source; the underlying
Datavidence Financials API is a commercial service.
