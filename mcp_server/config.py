"""Runtime config for the MCP server, from environment variables."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    base_url: str
    api_key: str
    key_header: str
    timeout: float


def load_config() -> Config:
    """Load config from env.

    - FL_API_BASE_URL: API base (default the production origin). For a marketplace
      channel, point this at the gateway endpoint (see docs/13 §2.1 / docs/12).
    - FL_API_KEY: the caller's key (BYOK). `sandbox_demo_key` works with no signup.
    - FL_API_KEY_HEADER: header to send the key in (default X-API-Key; a gateway
      may need e.g. X-RapidAPI-Key).
    - FL_API_TIMEOUT: per-request timeout seconds (default 30).
    """
    return Config(
        base_url=os.getenv(
            "FL_API_BASE_URL", "https://api.financials.datavidence.ai"
        ).rstrip("/"),
        api_key=os.getenv("FL_API_KEY", ""),
        key_header=os.getenv("FL_API_KEY_HEADER", "X-API-Key"),
        timeout=float(os.getenv("FL_API_TIMEOUT", "30")),
    )
