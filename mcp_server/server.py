"""MCP server exposing the Datavidence Financials API as agent tools.

Run: `python -m mcp_server.server` (stdio transport, for Claude Desktop et al.).
Requires `mcp_server/requirements.txt` installed and FL_API_KEY set (BYOK;
`sandbox_demo_key` works with no signup). Only this module imports the MCP SDK;
the forwarding logic lives in `client.py` (httpx-only, unit-tested).
"""

from typing import Annotated

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations
from pydantic import Field
from mcp.server.mcpserver.exceptions import ToolError

from mcp_server import __version__
from mcp_server.client import APIClient, FinancialAPIError
from mcp_server.config import load_config

_cfg = load_config()

# Every tool only reads public SEC data through the API: nothing is created,
# changed or deleted, and repeating a call returns the same answer. Declaring
# that lets clients auto-approve the tools and lets directories score them.
_READ_ONLY = ToolAnnotations(
    readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=True
)

Year = Annotated[int, Field(description="Fiscal year, e.g. 2023.")]
Ticker = Annotated[
    str | None,
    Field(description='Stock ticker, e.g. "AAPL". Give this or `cik`.'),
]
Cik = Annotated[
    str | None,
    Field(description='SEC Central Index Key, e.g. "0000320193". Give this or `ticker`.'),
]
AsOf = Annotated[
    str | None,
    Field(
        description="ISO date YYYY-MM-DD. Return figures as originally reported on "
        "that date (no look-ahead). Omit for the latest reported figures."
    ),
]
IncludeProvenance = Annotated[
    bool,
    Field(description="Attach the SEC accession, filed date and EDGAR URL behind every value."),
]
IncludeRatios = Annotated[
    bool,
    Field(description="Add margins, ROA/ROE and leverage computed from the same statements."),
]
_client = APIClient(_cfg.base_url, _cfg.api_key, _cfg.key_header, _cfg.timeout)

server = MCPServer(
    "Datavidence Financials",
    version=__version__,
    instructions=(
        "Tools for normalized US-GAAP financial statements sourced from SEC EDGAR "
        "XBRL filings. Every value can be traced to its source filing, and figures "
        "can be pulled as-originally-reported for a given date (no look-ahead)."
    ),
)


@server.tool(title="Get financial statements", annotations=_READ_ONLY)
async def get_financials(
    year: Year,
    ticker: Ticker = None,
    cik: Cik = None,
    as_of: AsOf = None,
    include_provenance: IncludeProvenance = False,
    include_ratios: IncludeRatios = False,
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
        # ToolError, not RuntimeError: the SDK treats any other exception as a
        # crash and sends the model only "Error executing tool <name>", which
        # would strip the API's message and its recovery_action hint - the whole
        # point of the error envelope. ToolError's text reaches the caller.
        raise ToolError(exc.agent_message()) from None


@server.tool(title="List SEC filings", annotations=_READ_ONLY)
async def list_filings(
    ticker: Ticker = None,
    cik: Cik = None,
    form: Annotated[
        str | None,
        Field(description='Form type filter, prefix-matched, e.g. "10-K" (includes 10-K/A).'),
    ] = None,
    limit: Annotated[int, Field(description="Maximum rows to return (1-100).")] = 25,
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
        raise ToolError(exc.agent_message()) from None


@server.tool(title="Get financial statements for many companies", annotations=_READ_ONLY)
async def get_financials_batch(
    year: Year,
    tickers: Annotated[
        str | None,
        Field(description='Comma-separated tickers, e.g. "AAPL,MSFT,GOOGL" (25 symbols max, with `ciks`).'),
    ] = None,
    ciks: Annotated[
        str | None,
        Field(description="Comma-separated SEC CIKs (25 symbols max, with `tickers`)."),
    ] = None,
    as_of: AsOf = None,
    include_provenance: IncludeProvenance = False,
    include_ratios: IncludeRatios = False,
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
        raise ToolError(exc.agent_message()) from None


@server.tool(title="Get restatement history", annotations=_READ_ONLY)
async def get_revisions(
    year: Year,
    ticker: Ticker = None,
    cik: Cik = None,
    metrics: Annotated[
        str | None,
        Field(description='Comma-separated metric names, e.g. "total_revenue,net_income". Omit for all.'),
    ] = None,
) -> dict:
    """Show how a company's reported figures for a fiscal year CHANGED across filings
    — as originally reported, then each restatement.

    A company re-reports every fiscal year as a comparative in later filings, and
    when a number changes, that is a restatement. This returns the full series
    for each metric: every reported value with the date it was filed, the form
    (10-K/10-Q), the SEC accession and a direct EDGAR link, plus whether it was
    restated and by how much.

    Use it to answer "has this been restated?", to show a figure's history, or to
    explain why a backtest on today's data would not match what an investor could
    have known at the time. Identify the company by `ticker` OR `cik`; narrow with
    `metrics` (comma-separated, e.g. "total_revenue,net_income") or omit for all.
    get_financials returns the LATEST reported figure; its `as_of` parameter
    returns the value as known on a date; this shows the whole series at once.
    """
    try:
        return await _client.fetch_revisions(
            year=year, ticker=ticker, cik=cik, metrics=metrics
        )
    except FinancialAPIError as exc:
        raise ToolError(exc.agent_message()) from None


@server.tool(title="Search companies", annotations=_READ_ONLY)
async def search_companies(
    query: Annotated[str, Field(description='Company name or ticker, e.g. "berkshire" or "XOM".')],
    limit: Annotated[int, Field(description="Maximum matches to return (1-25).")] = 10,
) -> dict:
    """Find a company's ticker and CIK by ticker or company name.

    Use this FIRST whenever you have a company name but not its ticker or CIK —
    every other tool needs one of those. Searches SEC's master list: "berkshire"
    returns BRK-B with its CIK, "mobil" returns XOM.

    Ranked so the obvious answer wins (an exact ticker beats a company whose name
    merely contains the text). `limit` caps the number of matches (1-25).
    """
    try:
        return await _client.search_companies(query=query, limit=limit)
    except FinancialAPIError as exc:
        raise ToolError(exc.agent_message()) from None


@server.tool(title="Check API usage", annotations=_READ_ONLY)
async def get_usage() -> dict:
    """Report the calling API key's current monthly quota: tier, monthly limit,
    requests used and remaining this billing month, and when it resets.

    Free to call — it does NOT consume quota. Check it before a large batch or a
    long run so you can pace requests and avoid a hard rate-limit (429).
    """
    try:
        return await _client.fetch_usage()
    except FinancialAPIError as exc:
        raise ToolError(exc.agent_message()) from None


def main() -> None:
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
