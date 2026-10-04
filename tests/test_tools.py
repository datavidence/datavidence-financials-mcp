"""Every declared tool, exercised through the MCP SDK the way a client calls it.

No network and no API key: the forwarding client is replaced by a stub that records
what each tool asked for.
"""

import json

import pytest
from mcp.server.mcpserver.exceptions import ToolError

from mcp_server import server as srv
from mcp_server.client import FinancialAPIError

TOOLS = {
    "get_financials", "get_financials_batch", "get_revisions",
    "list_filings", "search_companies", "get_usage",
}
HINTS = ("read_only_hint", "destructive_hint", "idempotent_hint", "open_world_hint")


class StubClient:
    """Stands in for APIClient: records the call, returns a marker payload."""

    def __init__(self, error: FinancialAPIError | None = None):
        self.calls: list[tuple[str, dict]] = []
        self.error = error

    def __getattr__(self, name):
        async def method(**kwargs):
            self.calls.append((name, kwargs))
            if self.error:
                raise self.error
            return {"called": name}
        return method


@pytest.fixture
def stub(monkeypatch):
    client = StubClient()
    monkeypatch.setattr(srv, "_client", client)
    return client


async def _tools() -> dict:
    return {t.name: t for t in await srv.server.list_tools()}


def _payload(result) -> dict:
    assert result.is_error is False
    return json.loads(result.content[0].text)


async def test_the_declared_tools_are_the_documented_six():
    assert set(await _tools()) == TOOLS


async def test_every_tool_declares_all_four_hints_as_booleans():
    # Directories (M8ven, the ChatGPT app directory) reject or mark down a tool
    # with any hint missing; clients use them to decide what needs approval.
    for name, tool in (await _tools()).items():
        assert tool.annotations is not None, name
        for hint in HINTS:
            assert isinstance(getattr(tool.annotations, hint), bool), f"{name}.{hint}"


async def test_every_tool_is_read_only_and_says_so():
    # Each tool only reads public SEC data through the API.
    for name, tool in (await _tools()).items():
        a = tool.annotations
        assert (a.read_only_hint, a.destructive_hint, a.idempotent_hint, a.open_world_hint) == (
            True, False, True, True), name


async def test_every_tool_has_a_title_a_description_and_described_parameters():
    for name, tool in (await _tools()).items():
        assert tool.title and tool.title[0].isupper(), name
        assert tool.description and len(tool.description) > 40, name
        for param, schema in tool.input_schema.get("properties", {}).items():
            assert schema.get("description"), f"{name}.{param} has no description"


@pytest.mark.parametrize(
    "tool, arguments, method, expected",
    [
        ("get_financials", {"year": 2023, "ticker": "AAPL", "include_ratios": True},
         "fetch_financials", {"year": 2023, "ticker": "AAPL", "include_ratios": True}),
        ("get_financials_batch", {"year": 2023, "tickers": "AAPL,MSFT"},
         "fetch_financials_batch", {"year": 2023, "tickers": "AAPL,MSFT"}),
        ("get_revisions", {"year": 2019, "ticker": "PFE", "metrics": "total_revenue"},
         "fetch_revisions", {"year": 2019, "ticker": "PFE", "metrics": "total_revenue"}),
        ("list_filings", {"ticker": "AAPL", "form": "10-K", "limit": 5},
         "fetch_filings", {"ticker": "AAPL", "form": "10-K", "limit": 5}),
        ("search_companies", {"query": "berkshire", "limit": 5},
         "search_companies", {"query": "berkshire", "limit": 5}),
        ("get_usage", {}, "fetch_usage", {}),
    ],
)
async def test_each_tool_forwards_its_arguments_and_returns_the_api_data(
    stub, tool, arguments, method, expected
):
    result = await srv.server.call_tool(tool, arguments)
    assert _payload(result) == {"called": method}
    assert len(stub.calls) == 1
    called, kwargs = stub.calls[0]
    assert called == method
    for key, value in expected.items():
        assert kwargs[key] == value, key


async def test_the_parametrized_cases_cover_every_tool():
    cases = test_each_tool_forwards_its_arguments_and_returns_the_api_data.pytestmark[0].args[1]
    assert {case[0] for case in cases} == set(await _tools())


@pytest.mark.parametrize("tool, arguments", [
    ("get_financials", {"year": 2023, "ticker": "NOPE"}),
    ("get_financials_batch", {"year": 2023, "tickers": "NOPE"}),
    ("get_revisions", {"year": 2023, "ticker": "NOPE"}),
    ("list_filings", {"ticker": "NOPE"}),
    ("search_companies", {"query": "nope"}),
    ("get_usage", {}),
])
async def test_an_api_error_reaches_the_model_with_its_recovery_hint(monkeypatch, tool, arguments):
    error = FinancialAPIError(
        "TICKER_NOT_FOUND", "no such ticker",
        recovery_action="Verify the ticker, or supply the CIK.", retryable=False, status=404,
    )
    monkeypatch.setattr(srv, "_client", StubClient(error))
    with pytest.raises(ToolError) as caught:
        await srv.server.call_tool(tool, arguments)
    message = str(caught.value)
    assert "TICKER_NOT_FOUND" in message
    assert "Verify the ticker, or supply the CIK." in message


async def test_a_missing_required_argument_is_rejected_before_any_call(stub):
    with pytest.raises(ToolError):
        await srv.server.call_tool("get_financials", {"ticker": "AAPL"})   # no year
    assert stub.calls == []
