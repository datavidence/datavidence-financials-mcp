"""MCP server exposing the Datavidence Financials API as agent tools.

Run: `python -m mcp_server.server` (stdio transport, for Claude Desktop et al.).
Requires `mcp_server/requirements.txt` installed and FL_API_KEY set (BYOK;
`sandbox_demo_key` works with no signup). Only this module imports the MCP SDK;
the forwarding logic lives in `client.py` (httpx-only, unit-tested).
"""

from mcp.server.mcpserver import MCPServer

from mcp_server.client import APIClient, FinancialAPIError
from mcp_server.config import load_config

_cfg = load_config()
_client = APIClient(_cfg.base_url, _cfg.api_key, _cfg.key_header, _cfg.timeout)

server = MCPServer(
    "Datavidence Financials",
    instructions=(
        "Tools for normalized US-GAAP financial statements sourced from SEC EDGAR "
        "XBRL filings. Every value can be traced to its source filing, and figures "
        "can be pulled as-originally-reported for a given date (no look-ahead)."
    ),
)


@server.tool()
async def get_financials(
    year: int,
    ticker: str | None = None,
    cik: str | None = None,
    as_of: str | None = None,
    include_provenance: bool = False,
    include_ratios: bool = False,
) -> dict:
    """Retrieve normalized US-GAAP financial statements (income statement, balance
    sheet, cash flow) for one company and fiscal year, from SEC EDGAR XBRL.

    Identify the company by `ticker` OR `cik`. Use `as_of` (ISO YYYY-MM-DD) to get
    the figures as originally reported on that date — no look-ahead bias — for
    backtests. Set `include_provenance=true` to attach, for every value, the SEC
    accession, filed date, and a direct EDGAR source URL for citation. Set
    `include_ratios=true` for margins, ROA/ROE, and leverage derived from the same
    statements. Returns the normalized data object.
    """
    try:
        return await _client.fetch_financials(
            year=year,
            ticker=ticker,
            cik=cik,
            as_of=as_of,
            include_provenance=include_provenance,
            include_ratios=include_ratios,
        )
    except FinancialAPIError as exc:
        raise RuntimeError(exc.agent_message()) from None


@server.tool()
async def list_filings(
    ticker: str | None = None,
    cik: str | None = None,
    form: str | None = None,
    limit: int = 25,
) -> dict:
    """List a company's recent SEC filings (newest first) from the EDGAR
    submissions index — a lean company header plus filing rows.

    Identify the company by `ticker` OR `cik`. Optionally filter by `form` (e.g.
    "10-K", prefix-matched so it includes amendments like "10-K/A") and cap the
    number of rows with `limit` (1-100). Use this to discover which fiscal years
    or filings are available before calling get_financials.
    """
    try:
        return await _client.fetch_filings(ticker=ticker, cik=cik, form=form, limit=limit)
    except FinancialAPIError as exc:
        raise RuntimeError(exc.agent_message()) from None


@server.tool()
async def get_financials_batch(
    year: int,
    tickers: str | None = None,
    ciks: str | None = None,
    as_of: str | None = None,
    include_provenance: bool = False,
    include_ratios: bool = False,
) -> dict:
    """Retrieve normalized US-GAAP financials for MANY companies in one call — use
    this to compare peers or scan a set for a single fiscal year.

    Pass companies as comma-separated `tickers` (e.g. "AAPL,MSFT,GOOGL") and/or
    `ciks`; up to 25 symbols total, all for the same `year`. `as_of`,
    `include_provenance`, and `include_ratios` behave as in get_financials and
    apply to every symbol. Each company returns its own result — either `data` or
    an `error` with a recovery hint — so one bad symbol never fails the batch. The
    whole call counts as a SINGLE request against your monthly quota, so prefer it
    over many get_financials calls when you need several companies.
    """
    try:
        return await _client.fetch_financials_batch(
            year=year,
            tickers=tickers,
            ciks=ciks,
            as_of=as_of,
            include_provenance=include_provenance,
            include_ratios=include_ratios,
        )
    except FinancialAPIError as exc:
        raise RuntimeError(exc.agent_message()) from None


@server.tool()
async def get_usage() -> dict:
    """Report the calling API key's current monthly quota: tier, monthly limit,
    requests used and remaining this billing month, and when it resets.

    Free to call — it does NOT consume quota. Check it before a large batch or a
    long run so you can pace requests and avoid a hard rate-limit (429).
    """
    try:
        return await _client.fetch_usage()
    except FinancialAPIError as exc:
        raise RuntimeError(exc.agent_message()) from None


def main() -> None:
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
