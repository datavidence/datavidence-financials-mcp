"""The HTTP forwarding client (httpx only, no MCP SDK). No network: every request
is answered by an httpx MockTransport."""

import httpx
import pytest

from mcp_server.client import APIClient, FinancialAPIError


def _client(handler) -> APIClient:
    transport = httpx.MockTransport(handler)
    http = httpx.AsyncClient(transport=transport)
    return APIClient("http://api.test", "k-123", http_client=http)


async def test_fetch_financials_success_and_headers():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["key"] = request.headers.get("X-API-Key")
        seen["query"] = dict(request.url.params)
        return httpx.Response(200, json={"status": "success", "data": {
            "cik": "0000320193", "income_statement": {"total_revenue": 100},
        }})

    c = _client(handler)
    data = await c.fetch_financials(year=2023, ticker="AAPL", include_ratios=True)
    assert data["income_statement"]["total_revenue"] == 100
    assert seen["path"] == "/v1/extract-ledger"
    assert seen["key"] == "k-123"                       # BYOK header forwarded
    assert seen["query"]["include_ratios"] == "true"    # flag passed through (httpx lowercases bools)
    assert "cik" not in seen["query"]                   # None params dropped


async def test_fetch_revisions_forwards_the_metric_filter():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["query"] = dict(request.url.params)
        return httpx.Response(200, json={"status": "success", "data": {
            "cik": "0000078003", "fiscal_year": 2019, "any_restated": True,
            "metrics": {"total_revenue": {"section": "income_statement",
                                          "status": "ok", "restated": True}},
        }})

    data = await _client(handler).fetch_revisions(
        year=2019, ticker="PFE", metrics="total_revenue"
    )
    assert seen["path"] == "/v1/revisions"
    assert seen["query"]["metrics"] == "total_revenue"
    assert "cik" not in seen["query"]                   # None params dropped
    assert data["any_restated"] is True


async def test_search_companies_maps_query_to_q():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["query"] = dict(request.url.params)
        return httpx.Response(200, json={"status": "success", "data": {
            "query": "berkshire", "count": 1,
            "results": [{"ticker": "BRK-B", "cik": "0001067983",
                         "title": "BERKSHIRE HATHAWAY INC"}],
        }})

    data = await _client(handler).search_companies(query="berkshire", limit=5)
    assert seen["path"] == "/v1/companies"
    assert seen["query"]["q"] == "berkshire"            # the API param is `q`
    assert seen["query"]["limit"] == "5"
    assert data["results"][0]["ticker"] == "BRK-B"


async def test_fetch_filings_success():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/submissions"
        return httpx.Response(200, json={"status": "success", "data": {
            "cik": "0000320193", "filings_returned": 1, "filings": [{"form": "10-K"}],
        }})

    data = await _client(handler).fetch_filings(ticker="AAPL", form="10-K", limit=5)
    assert data["filings_returned"] == 1


async def test_error_envelope_surfaces_recovery_action():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"status": "error", "error": {
            "code": "TICKER_NOT_FOUND",
            "message": "no such ticker",
            "recovery_action": "Verify the ticker, or supply the CIK.",
            "retryable": False,
        }})

    with pytest.raises(FinancialAPIError) as ei:
        await _client(handler).fetch_financials(year=2023, ticker="NOPE")
    err = ei.value
    assert err.code == "TICKER_NOT_FOUND"
    assert err.retryable is False
    assert "Recovery: Verify the ticker" in err.agent_message()


async def test_network_error_is_retryable():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom")

    with pytest.raises(FinancialAPIError) as ei:
        await _client(handler).fetch_financials(year=2023, cik="0000320193")
    assert ei.value.code == "NETWORK_ERROR"
    assert ei.value.retryable is True


async def test_fetch_financials_batch_success_and_params():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["query"] = dict(request.url.params)
        return httpx.Response(200, json={"status": "success", "data": {
            "requested": 2, "succeeded": 2, "failed": 0,
            "results": [{"ticker": "AAPL", "status": "success"},
                        {"ticker": "MSFT", "status": "success"}],
        }})

    c = _client(handler)
    data = await c.fetch_financials_batch(year=2023, tickers="AAPL,MSFT", include_ratios=True)
    assert data["succeeded"] == 2
    assert seen["path"] == "/v1/extract-ledger/batch"
    assert seen["query"]["tickers"] == "AAPL,MSFT"
    assert seen["query"]["include_ratios"] == "true"   # flag passed through
    assert "ciks" not in seen["query"]                 # None params dropped


async def test_fetch_usage_success_no_params():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/usage"
        assert dict(request.url.params) == {}          # usage takes no params
        return httpx.Response(200, json={"status": "success", "data": {
            "tier": "developer", "monthly_limit": 50000,
            "requests_this_month": 10, "requests_remaining": 49990,
            "resets_at": "2026-10-01T00:00:00+00:00",
        }})

    data = await _client(handler).fetch_usage()
    assert data["tier"] == "developer"
    assert data["requests_remaining"] == 49990
