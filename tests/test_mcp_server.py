from typing import Any
import importlib


def _mcp_server() -> Any:
    return importlib.import_module("crypto_mcp.mcp_server")


def test_health_shape() -> None:
    result = _mcp_server().health()
    assert result["ok"] is True
    assert result["tool"] == "health"
    assert result["payload"]["service"] == "crypto-mcp"


def test_list_exchanges_shape() -> None:
    result = _mcp_server().list_exchanges()
    assert result["ok"] is True
    assert result["tool"] == "list_exchanges"
    assert isinstance(result["payload"]["items"], list)


def test_confirmation_roundtrip_in_request_mode_works() -> None:
    server = _mcp_server()
    original = server._SETTINGS
    server._SETTINGS = original.__class__(
        mcp_default_limit=original.mcp_default_limit,
        mcp_max_limit=original.mcp_max_limit,
        mcp_context_mode="request",
        dry_run=original.dry_run,
        exchanges_enabled=original.exchanges_enabled,
        binance_api_base_url=original.binance_api_base_url,
        binance_api_key=original.binance_api_key,
        binance_api_secret=original.binance_api_secret,
        require_confirmation_above_usd=original.require_confirmation_above_usd,
    )
    try:
        submitted = server.submit_demo_order(usd_size=1000.0)
        assert submitted["ok"] is True
        confirmation_id = submitted["payload"]["confirmation_id"]
        confirmed = server.confirm_pending_order(confirmation_id)
        assert confirmed["ok"] is True
    finally:
        server._SETTINGS = original


def test_confirm_pending_order_not_found_shape() -> None:
    result = _mcp_server().confirm_pending_order("missing")
    assert result["ok"] is False
    assert result["tool"] == "confirm_pending_order"
    assert result["error"] == "confirmation_not_found"


def test_submit_demo_order_live_mode_returns_top_level_error_envelope() -> None:
    server = _mcp_server()
    original = server._SETTINGS
    original_ctx = server._CTX
    server._SETTINGS = original.__class__(
        mcp_default_limit=original.mcp_default_limit,
        mcp_max_limit=original.mcp_max_limit,
        mcp_context_mode=original.mcp_context_mode,
        dry_run=False,
        exchanges_enabled=original.exchanges_enabled,
        binance_api_base_url=original.binance_api_base_url,
        binance_api_key=original.binance_api_key,
        binance_api_secret=original.binance_api_secret,
        require_confirmation_above_usd=original.require_confirmation_above_usd,
    )
    server._CTX = server.create_server_context(server._SETTINGS)
    try:
        result = server.submit_demo_order(usd_size=25.0)
        assert result["ok"] is False
        assert result["tool"] == "submit_demo_order"
        assert result["error"] == "live_trading_not_implemented"
    finally:
        server._CTX.close()
        server._CTX = original_ctx
        server._SETTINGS = original
