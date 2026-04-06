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


def _ok(tool: str, payload: object) -> dict[str, object]:
    return {"ok": True, "tool": tool, "payload": payload}


def _err(tool: str, error: str, category: str) -> dict[str, object]:
    return {
        "ok": False,
        "tool": tool,
        "error": error,
        "error_category": category,
    }


def _safe_limit(value: int | None, default: int, maximum: int) -> int:
    if value is None:
        return default
    if value < 0:
        return 0
    return min(value, maximum)


def _request_context():
    settings = _SETTINGS
    if settings.mcp_context_mode == MCPContextMode.REQUEST.value:
        return create_server_context(settings), True
    return _CTX, False


def _close_if_request_context(ctx: Any, is_request: bool) -> None:
    if is_request:
        ctx.close()


@mcp.tool()
def health() -> dict[str, object]:
    settings = _SETTINGS
    return _ok(
        "health",
        {
            "service": "crypto-mcp",
            "time_utc": datetime.now(timezone.utc).isoformat(),
            "dry_run": settings.dry_run,
            "mcp_default_limit": settings.mcp_default_limit,
            "mcp_max_limit": settings.mcp_max_limit,
            "mcp_context_mode": settings.mcp_context_mode,
            "exchanges_enabled": settings.exchanges_enabled,
        },
    )


@mcp.tool()
def list_exchanges() -> dict[str, object]:
    ctx, is_request = _request_context()
    try:
        items = list_supported_exchanges(ctx)
        return _ok("list_exchanges", {"count": len(items), "items": items})
    except Exception as exc:  # noqa: BLE001
        return _err("list_exchanges", str(exc), "internal")
    finally:
        _close_if_request_context(ctx, is_request)


@mcp.tool()
def get_price(exchange: str, symbol: str) -> dict[str, object]:
    ctx, is_request = _request_context()
    try:
        result = get_market_price(ctx, exchange, symbol)
        return _ok("get_price", result)
    except ValueError as exc:
        return _err("get_price", str(exc), "validation")
    except Exception as exc:  # noqa: BLE001
        return _err("get_price", str(exc), "provider")
    finally:
        _close_if_request_context(ctx, is_request)


@mcp.tool()
def list_exchange_symbols(exchange: str, limit: int | None = None) -> dict[str, object]:
    settings = load_settings()
    capped_limit = _safe_limit(limit, settings.mcp_default_limit, settings.mcp_max_limit)
    ctx, is_request = _request_context()
    try:
        items = list_symbols(ctx, exchange, capped_limit)
        return _ok(
            "list_exchange_symbols",
            {"count": len(items), "limit": capped_limit, "items": items},
        )
    except ValueError as exc:
        return _err("list_exchange_symbols", str(exc), "validation")
    except Exception as exc:  # noqa: BLE001
        return _err("list_exchange_symbols", str(exc), "provider")
    finally:
        _close_if_request_context(ctx, is_request)


@mcp.tool()
def submit_demo_order(
    exchange: str = "binance", symbol: str = "BTCUSDT", side: str = "BUY", usd_size: float = 25.0
) -> dict[str, object]:
    ctx, is_request = _CTX, False
    try:
        result = submit_order(ctx, exchange, symbol, side, usd_size)
        if bool(result.get("ok", True)):
            return _ok("submit_demo_order", result)
        return _err(
            "submit_demo_order",
            str(result.get("error", "submit_failed")),
            str(result.get("error_category", "internal")),
        )
    except ValueError as exc:
        return _err("submit_demo_order", str(exc), "validation")
    except Exception as exc:  # noqa: BLE001
        return _err("submit_demo_order", str(exc), "internal")
    finally:
        _close_if_request_context(ctx, is_request)


@mcp.tool()
def confirm_pending_order(confirmation_id: str) -> dict[str, object]:
    ctx, is_request = _CTX, False
    try:
        result = confirm_order(ctx, confirmation_id)
        if result.get("ok", False):
            return _ok("confirm_pending_order", result)
        return _err(
            "confirm_pending_order",
            str(result.get("error", "confirmation_failed")),
            str(result.get("error_category", "validation")),
        )
    except Exception as exc:  # noqa: BLE001
        return _err("confirm_pending_order", str(exc), "internal")
    finally:
        _close_if_request_context(ctx, is_request)


def main() -> None:
    try:
        mcp.run()
    finally:
        _CTX.close()


if __name__ == "__main__":
    main()
