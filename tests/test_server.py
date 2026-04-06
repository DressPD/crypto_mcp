from typing import Any
import importlib


def _server_module() -> Any:
    return importlib.import_module("crypto_mcp.server")


def _config_module() -> Any:
    return importlib.import_module("crypto_mcp.config")


def _settings() -> Any:
    settings_cls = _config_module().Settings
    return settings_cls(
        mcp_default_limit=10,
        mcp_max_limit=50,
        mcp_context_mode="shared",
        dry_run=True,
        exchanges_enabled=["binance"],
        binance_api_base_url="https://api.binance.com",
        binance_api_key=None,
        binance_api_secret=None,
        require_confirmation_above_usd=100.0,
    )


def test_supported_exchanges_contains_binance() -> None:
    server = _server_module()
    ctx = server.create_server_context(_settings())
    try:
        assert server.list_supported_exchanges(ctx) == ["binance"]
    finally:
        ctx.close()


def test_submit_order_under_threshold_executes() -> None:
    server = _server_module()
    ctx = server.create_server_context(_settings())
    try:
        result = server.submit_order(ctx, "binance", "BTCUSDT", "BUY", 25.0)
        assert result["ok"] is True
        assert result["status"] == "accepted"
    finally:
        ctx.close()


def test_submit_order_over_threshold_requires_confirmation() -> None:
    server = _server_module()
    ctx = server.create_server_context(_settings())
    try:
        result = server.submit_order(ctx, "binance", "BTCUSDT", "BUY", 150.0)
        assert result["status"] == "pending_confirmation"
        confirmation_id = result["confirmation_id"]
        confirmed = server.confirm_order(ctx, confirmation_id)
        assert confirmed["ok"] is True
    finally:
        ctx.close()


def test_submit_order_rejects_invalid_side() -> None:
    server = _server_module()
    ctx = server.create_server_context(_settings())
    try:
        try:
            server.submit_order(ctx, "binance", "BTCUSDT", "HOLD", 25.0)
            raise AssertionError("expected ValueError")
        except ValueError as exc:
            assert str(exc) == "invalid_side"
    finally:
        ctx.close()


def test_submit_order_rejects_non_positive_usd_size() -> None:
    server = _server_module()
    ctx = server.create_server_context(_settings())
    try:
        try:
            server.submit_order(ctx, "binance", "BTCUSDT", "BUY", 0.0)
            raise AssertionError("expected ValueError")
        except ValueError as exc:
            assert str(exc) == "invalid_usd_size"
    finally:
        ctx.close()


def test_submit_order_rejects_empty_symbol() -> None:
    server = _server_module()
    ctx = server.create_server_context(_settings())
    try:
        try:
            server.submit_order(ctx, "binance", "", "BUY", 25.0)
            raise AssertionError("expected ValueError")
        except ValueError as exc:
            assert str(exc) == "invalid_symbol"
    finally:
        ctx.close()
