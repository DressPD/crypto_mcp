from typing import Any
import importlib
import sys
import pytest


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


def test_list_exchange_symbols_uses_default_limit_when_none() -> None:
    result = _mcp_server().list_exchange_symbols("binance", None)
    assert result["ok"] is True
    assert result["tool"] == "list_exchange_symbols"
    assert "limit" in result["payload"]


def test_request_context_mode_for_read_tools() -> None:
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
        result = server.list_exchanges()
        assert result["ok"] is True
        assert result["tool"] == "list_exchanges"
    finally:
        server._SETTINGS = original


def test_list_exchange_symbols_limit_clamps() -> None:
    server = _mcp_server()
    result = server.list_exchange_symbols("binance", -5)
    assert result["ok"] is True
    assert result["payload"]["limit"] == 0


def test_get_price_validation_error_envelope(monkeypatch) -> None:
    server = _mcp_server()
    monkeypatch.setattr(
        server, "get_market_price", lambda *_args: (_ for _ in ()).throw(ValueError("bad"))
    )
    result = server.get_price("binance", "BTCUSDT")
    assert result["ok"] is False
    assert result["tool"] == "get_price"
    assert result["error_category"] == "validation"


def test_get_price_provider_error_envelope(monkeypatch) -> None:
    server = _mcp_server()
    monkeypatch.setattr(
        server, "get_market_price", lambda *_args: (_ for _ in ()).throw(RuntimeError("boom"))
    )
    result = server.get_price("binance", "BTCUSDT")
    assert result["ok"] is False
    assert result["error_category"] == "provider"


def test_list_exchanges_internal_error_envelope(monkeypatch) -> None:
    server = _mcp_server()
    monkeypatch.setattr(
        server,
        "list_supported_exchanges",
        lambda _ctx: (_ for _ in ()).throw(RuntimeError("x")),
    )
    result = server.list_exchanges()
    assert result["ok"] is False
    assert result["tool"] == "list_exchanges"
    assert result["error_category"] == "internal"


def test_list_exchange_symbols_provider_error(monkeypatch) -> None:
    server = _mcp_server()
    monkeypatch.setattr(
        server, "list_symbols", lambda *_args: (_ for _ in ()).throw(RuntimeError("x"))
    )
    result = server.list_exchange_symbols("binance", 1)
    assert result["ok"] is False
    assert result["tool"] == "list_exchange_symbols"
    assert result["error_category"] == "provider"


def test_submit_demo_order_validation_error(monkeypatch) -> None:
    server = _mcp_server()
    monkeypatch.setattr(
        server, "submit_order", lambda *_args: (_ for _ in ()).throw(ValueError("invalid"))
    )
    result = server.submit_demo_order(usd_size=-1.0)
    assert result["ok"] is False
    assert result["error_category"] == "validation"


def test_confirm_pending_order_internal_error(monkeypatch) -> None:
    server = _mcp_server()
    monkeypatch.setattr(
        server, "confirm_order", lambda *_args: (_ for _ in ()).throw(RuntimeError("oops"))
    )
    result = server.confirm_pending_order("abc")
    assert result["ok"] is False
    assert result["error_category"] == "internal"


def test_close_if_request_context_calls_close() -> None:
    server = _mcp_server()

    class _Ctx:
        def __init__(self) -> None:
            self.closed = False

        def close(self) -> None:
            self.closed = True

    ctx = _Ctx()
    server._close_if_request_context(ctx, True)
    assert ctx.closed is True


def test_get_price_success_envelope(monkeypatch) -> None:
    server = _mcp_server()
    monkeypatch.setattr(
        server,
        "get_market_price",
        lambda _ctx, exchange, symbol: {"exchange": exchange, "symbol": symbol, "price": "1"},
    )
    result = server.get_price("binance", "BTCUSDT")
    assert result["ok"] is True
    assert result["tool"] == "get_price"
    assert result["payload"]["symbol"] == "BTCUSDT"


def test_list_exchange_symbols_validation_error(monkeypatch) -> None:
    server = _mcp_server()
    monkeypatch.setattr(
        server, "list_symbols", lambda *_args: (_ for _ in ()).throw(ValueError("invalid"))
    )
    result = server.list_exchange_symbols("binance", 1)
    assert result["ok"] is False
    assert result["tool"] == "list_exchange_symbols"
    assert result["error"] == "invalid"
    assert result["error_category"] == "validation"


def test_submit_demo_order_internal_error(monkeypatch) -> None:
    server = _mcp_server()
    monkeypatch.setattr(
        server, "submit_order", lambda *_args: (_ for _ in ()).throw(RuntimeError("crash"))
    )
    result = server.submit_demo_order(usd_size=25.0)
    assert result["ok"] is False
    assert result["tool"] == "submit_demo_order"
    assert result["error"] == "crash"
    assert result["error_category"] == "internal"


def test_error_envelope_fields_present_consistently() -> None:
    result = _mcp_server().confirm_pending_order("missing")
    assert set(result.keys()) == {"ok", "tool", "error", "error_category"}
    assert result["ok"] is False


def test_main_closes_context(monkeypatch) -> None:
    server = _mcp_server()
    events: list[str] = []

    class _MCP:
        def run(self) -> None:
            events.append("run")

    class _CTX:
        def close(self) -> None:
            events.append("close")

    monkeypatch.setattr(server, "mcp", _MCP())
    monkeypatch.setattr(server, "_CTX", _CTX())
    server.main()
    assert events == ["run", "close"]


def test_main_closes_context_on_run_error(monkeypatch) -> None:
    server = _mcp_server()
    events: list[str] = []

    class _MCP:
        def run(self) -> None:
            events.append("run")
            raise RuntimeError("boom")

    class _CTX:
        def close(self) -> None:
            events.append("close")

    monkeypatch.setattr(server, "mcp", _MCP())
    monkeypatch.setattr(server, "_CTX", _CTX())
    try:
        server.main()
        raise AssertionError("expected RuntimeError")
    except RuntimeError:
        pass
    assert events == ["run", "close"]


def test_fallback_fastmcp_class_when_package_missing(monkeypatch) -> None:
    original_import_module = importlib.import_module

    def _fake_import_module(name: str, package: str | None = None):
        if name == "mcp.server.fastmcp":
            raise ImportError("missing")
        return original_import_module(name, package)

    monkeypatch.setattr(importlib, "import_module", _fake_import_module)
    sys.modules.pop("crypto_mcp.mcp_server", None)
    fallback_module = importlib.import_module("crypto_mcp.mcp_server")
    fake = fallback_module.FastMCP("x")
    with pytest.raises(RuntimeError):
        fake.run()
    sys.modules.pop("crypto_mcp.mcp_server", None)
    importlib.import_module("crypto_mcp.mcp_server")
