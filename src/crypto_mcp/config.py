from __future__ import annotations

import os
import importlib
from dataclasses import dataclass
from enum import Enum


def _load_dotenv() -> bool:
    try:
        dotenv = importlib.import_module("dotenv")
    except ImportError:
        return False
    return bool(dotenv.load_dotenv())


class MCPContextMode(str, Enum):
    SHARED = "shared"
    REQUEST = "request"


def _parse_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    return default


def _parse_int(value: str | None, default: int) -> int:
    if value is None or value.strip() == "":
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _parse_float(value: str | None, default: float) -> float:
    if value is None or value.strip() == "":
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _parse_csv(value: str | None, default: list[str]) -> list[str]:
    if value is None or value.strip() == "":
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


def _clamp_int(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, value))


def _clamp_float(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


@dataclass(frozen=True)
class Settings:
    mcp_default_limit: int
    mcp_max_limit: int
    mcp_context_mode: str
    dry_run: bool
    exchanges_enabled: list[str]
    binance_api_base_url: str
    binance_api_key: str | None
    binance_api_secret: str | None
    require_confirmation_above_usd: float


def load_settings() -> Settings:
    _ = _load_dotenv()

    mcp_default_limit = _clamp_int(_parse_int(os.getenv("MCP_DEFAULT_LIMIT"), 10), 1, 100)
    mcp_max_limit = _clamp_int(_parse_int(os.getenv("MCP_MAX_LIMIT"), 50), 1, 500)
    if mcp_default_limit > mcp_max_limit:
        mcp_default_limit = mcp_max_limit

    mcp_context_mode = (
        (os.getenv("MCP_CONTEXT_MODE") or MCPContextMode.SHARED.value).strip().lower()
    )
    if mcp_context_mode not in {MCPContextMode.SHARED.value, MCPContextMode.REQUEST.value}:
        mcp_context_mode = MCPContextMode.SHARED.value

    return Settings(
        mcp_default_limit=mcp_default_limit,
        mcp_max_limit=mcp_max_limit,
        mcp_context_mode=mcp_context_mode,
        dry_run=_parse_bool(os.getenv("DRY_RUN"), True),
        exchanges_enabled=_parse_csv(os.getenv("EXCHANGES_ENABLED"), ["binance"]),
        binance_api_base_url=os.getenv("BINANCE_API_BASE_URL", "https://api.binance.com"),
        binance_api_key=os.getenv("BINANCE_API_KEY") or None,
        binance_api_secret=os.getenv("BINANCE_API_SECRET") or None,
        require_confirmation_above_usd=_clamp_float(
            _parse_float(os.getenv("REQUIRE_CONFIRMATION_ABOVE_USD"), 500.0),
            1.0,
            100000.0,
        ),
    )
