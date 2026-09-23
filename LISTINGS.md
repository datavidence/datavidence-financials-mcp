# Canonical listing copy

Reusable across every directory (mcp.so submit form, and the Glama / PulseMCP /
Smithery listings after you claim them). Keyword-led for discovery.

## Name / display title
**Datavidence Financials**

(package & command: `datavidence-financials` · registry name:
`io.github.datavidence/datavidence-financials`)

## One-line tagline
SEC EDGAR financial statements & fundamentals — normalized US-GAAP income
statement, balance sheet, and cash flow, as MCP tools for LLM agents.

## Short description (1–2 sentences)
Normalized US-GAAP financial statements from SEC EDGAR — income statement, balance
sheet, and cash flow — as Model Context Protocol tools for LLM agents. Point-in-time
(as-originally-reported) figures and per-value SEC source provenance for citation.

## Long description
Datavidence Financials gives AI agents clean, normalized US-GAAP financial
statements sourced directly from SEC EDGAR XBRL filings. Instead of parsing raw
filings, an agent calls six tools: `get_financials` (income statement, balance
sheet, and cash flow for a company and fiscal year, with optional financial ratios),
`get_financials_batch` (up to 25 companies in one call, for peer comparison),
`get_revisions` (how a year's figures changed across filings — as reported, then
each restatement), `search_companies` (find a ticker and CIK by company name),
`list_filings` (discover a company's available filings and years), and `get_usage`
(check quota). Every value can be pulled *as originally reported* on a given date
(no look-ahead bias, for backtests) and traced to its source filing via a direct
EDGAR URL. Errors return a machine-readable recovery hint so agents self-correct.
Runs over stdio; bring your own key — `sandbox_demo_key` gives a no-signup trial.

## Install (one line, no clone)
```
FL_API_KEY=sandbox_demo_key uvx datavidence-financials
```

## Category
Finance / Financial Data

## Tags / keywords
sec, edgar, financial-statements, fundamentals, us-gaap, xbrl, finance,
income-statement, balance-sheet, cash-flow, financial-data, financial-ratios,
equities, stocks, investing, fintech, mcp, llm, agents

## Links
- Website / docs: https://financials.datavidence.ai
- Repository: https://github.com/datavidence/datavidence-financials-mcp
- PyPI: https://pypi.org/project/datavidence-financials/
- Get a key (RapidAPI): https://rapidapi.com/datavidence-ykNLbvGmT/api/datavidence-financials-api

## Example prompts (for listings that show usage)
- "Get AAPL's FY2023 income statement, balance sheet, and cash flow with ratios."
- "Compare FY2023 revenue and net margin for AAPL, MSFT, and GOOGL."
- "What 10-K filings does NVDA have on EDGAR, and pull FY2022 as originally reported."
