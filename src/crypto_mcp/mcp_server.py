from __future__ import annotations

from datetime import datetime, timezone
import importlib
from typing import Any

try:
    FastMCP = importlib.import_module("mcp.server.fastmcp").FastMCP
except ImportError:

    class FastMCP:  # type: ignore[override]
        def __init__(self, _name: str) -> None:
            pass

        def tool(self):
            def decorator(func):
                return func

            return decorator

        def run(self) -> None:
            raise RuntimeError("mcp package missing")


from .config import MCPContextMode, load_settings
from .server import (
    confirm_order,
    create_server_context,
    get_market_price,
    list_supported_exchanges,
    list_symbols,
    submit_order,
)

mcp = FastMCP("crypto-mcp")
_SETTINGS = load_settings()
_CTX = create_server_context(_SETTINGS)


def _safe_limit(value: int | None, default: int, maximum: int) -> int:
    if value is None:
        return default
    if value < 0:
        return 0
    return min(value, maximum)


def _request_context():
    settings = load_settings()
    if settings.mcp_context_mode == MCPContextMode.REQUEST.value:
        return create_server_context(settings), True
    return _CTX, False


def _close_if_request_context(ctx: Any, is_request: bool) -> None:
    if is_request:
        ctx.close()


@mcp.tool()
def health() -> dict[str, object]:
    settings = load_settings()
    return {
        "ok": True,
        "tool": "health",
        "service": "crypto-mcp",
        "time_utc": datetime.now(timezone.utc).isoformat(),
        "dry_run": settings.dry_run,
        "mcp_default_limit": settings.mcp_default_limit,
        "mcp_max_limit": settings.mcp_max_limit,
        "mcp_context_mode": settings.mcp_context_mode,
        "exchanges_enabled": settings.exchanges_enabled,
    }


@mcp.tool()
def list_exchanges() -> dict[str, object]:
    ctx, is_request = _request_context()
    try:
        items = list_supported_exchanges(ctx)
        return {
            "ok": True,
            "tool": "list_exchanges",
            "count": len(items),
            "items": items,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "tool": "list_exchanges",
            "error": str(exc),
            "error_category": "internal",
        }
    finally:
        _close_if_request_context(ctx, is_request)


@mcp.tool()
def get_price(exchange: str, symbol: str) -> dict[str, object]:
    ctx, is_request = _request_context()
    try:
        result = get_market_price(ctx, exchange, symbol)
        return {
            "ok": True,
            "tool": "get_price",
            "result": result,
        }
    except ValueError as exc:
        return {
            "ok": False,
            "tool": "get_price",
            "error": str(exc),
            "error_category": "validation",
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "tool": "get_price",
            "error": str(exc),
            "error_category": "provider",
        }
    finally:
        _close_if_request_context(ctx, is_request)


@mcp.tool()
def list_exchange_symbols(exchange: str, limit: int | None = None) -> dict[str, object]:
    settings = load_settings()
    capped_limit = _safe_limit(limit, settings.mcp_default_limit, settings.mcp_max_limit)
    ctx, is_request = _request_context()
    try:
        items = list_symbols(ctx, exchange, capped_limit)
        return {
            "ok": True,
            "tool": "list_exchange_symbols",
            "count": len(items),
            "limit": capped_limit,
            "items": items,
        }
    except ValueError as exc:
        return {
            "ok": False,
            "tool": "list_exchange_symbols",
            "error": str(exc),
            "error_category": "validation",
            "count": 0,
            "items": [],
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "tool": "list_exchange_symbols",
            "error": str(exc),
            "error_category": "provider",
            "count": 0,
            "items": [],
        }
    finally:
        _close_if_request_context(ctx, is_request)


@mcp.tool()
def submit_demo_order(
    exchange: str = "binance", symbol: str = "BTCUSDT", side: str = "BUY", usd_size: float = 25.0
) -> dict[str, object]:
    ctx, is_request = _request_context()
    try:
        result = submit_order(ctx, exchange, symbol, side, usd_size)
        return {
            "ok": True,
            "tool": "submit_demo_order",
            "result": result,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "tool": "submit_demo_order",
            "error": str(exc),
            "error_category": "internal",
        }
    finally:
        _close_if_request_context(ctx, is_request)


@mcp.tool()
def confirm_pending_order(confirmation_id: str) -> dict[str, object]:
    ctx, is_request = _request_context()
    try:
        result = confirm_order(ctx, confirmation_id)
        return {
            "ok": result.get("ok", False),
            "tool": "confirm_pending_order",
            "result": result,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "tool": "confirm_pending_order",
            "error": str(exc),
            "error_category": "internal",
        }
    finally:
        _close_if_request_context(ctx, is_request)


def main() -> None:
    try:
        mcp.run()
    finally:
        _CTX.close()


if __name__ == "__main__":
    main()
