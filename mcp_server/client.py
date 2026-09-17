"""HTTP client that forwards MCP tool calls to the Datavidence Financials REST API.

Depends only on httpx (no MCP SDK), so it is unit-testable in the core test
suite. Surfaces the API's structured error envelope — including the
``recovery_action`` hint — so an agent can self-correct.
"""

import httpx


class FinancialAPIError(Exception):
    """An API error, carrying the envelope's code / message / recovery hint."""

    def __init__(
        self,
        code: str,
        message: str,
        recovery_action: str | None = None,
        retryable: bool | None = None,
        status: int | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.recovery_action = recovery_action
        self.retryable = retryable
        self.status = status
        super().__init__(self.agent_message())

    def agent_message(self) -> str:
        """A single readable string for the agent, including the recovery hint."""
        text = f"[{self.code}] {self.message}"
        if self.recovery_action:
            text += f" Recovery: {self.recovery_action}"
        return text

    @classmethod
    def from_response(cls, resp: httpx.Response) -> "FinancialAPIError":
        try:
            err = resp.json().get("error", {})
        except ValueError:
            err = {}
        return cls(
            code=err.get("code", "HTTP_ERROR"),
            message=err.get("message", f"HTTP {resp.status_code}"),
            recovery_action=err.get("recovery_action"),
            retryable=err.get("retryable"),
            status=resp.status_code,
        )


class APIClient:
    """Thin async client. Pass ``http_client`` to inject a transport in tests."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        key_header: str = "X-API-Key",
        timeout: float = 30.0,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._base = base_url.rstrip("/")
        self._key = api_key
        self._header = key_header
        self._timeout = timeout
        self._client = http_client

    async def _get(self, path: str, params: dict) -> dict:
        params = {k: v for k, v in params.items() if v is not None}
        headers = {self._header: self._key}
        client = self._client or httpx.AsyncClient(timeout=self._timeout)
        owns = self._client is None
        try:
            resp = await client.get(f"{self._base}{path}", params=params, headers=headers)
            if resp.status_code >= 400:
                raise FinancialAPIError.from_response(resp)
            return resp.json()
        except httpx.HTTPError as exc:
            raise FinancialAPIError(
                "NETWORK_ERROR",
                f"Could not reach the API: {exc}",
                "Transient network error. Retry once after a short backoff.",
                True,
            ) from exc
        finally:
            if owns:
                await client.aclose()

    async def fetch_financials(
        self,
        *,
        year: int,
        ticker: str | None = None,
        cik: str | None = None,
        as_of: str | None = None,
        include_provenance: bool = False,
        include_ratios: bool = False,
    ) -> dict:
        body = await self._get(
            "/v1/extract-ledger",
            {
                "year": year,
                "ticker": ticker,
                "cik": cik,
                "as_of": as_of,
                "include_provenance": include_provenance or None,
                "include_ratios": include_ratios or None,
            },
        )
        return body["data"]

    async def fetch_filings(
        self,
        *,
        ticker: str | None = None,
        cik: str | None = None,
        form: str | None = None,
        limit: int | None = None,
    ) -> dict:
        body = await self._get(
            "/v1/submissions",
            {"ticker": ticker, "cik": cik, "form": form, "limit": limit},
        )
        return body["data"]


    async def fetch_financials_batch(
        self,
        *,
        year: int,
        tickers: str | None = None,
        ciks: str | None = None,
        as_of: str | None = None,
        include_provenance: bool = False,
        include_ratios: bool = False,
    ) -> dict:
        body = await self._get(
            "/v1/extract-ledger/batch",
            {
                "year": year,
                "tickers": tickers,
                "ciks": ciks,
                "as_of": as_of,
                "include_provenance": include_provenance or None,
                "include_ratios": include_ratios or None,
            },
        )
        return body["data"]

    async def fetch_usage(self) -> dict:
        body = await self._get("/v1/usage", {})
        return body["data"]
