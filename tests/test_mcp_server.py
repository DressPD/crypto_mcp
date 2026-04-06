from typing import Any
import importlib


def _mcp_server() -> Any:
    return importlib.import_module("crypto_mcp.mcp_server")


def test_health_shape() -> None:
    result = _mcp_server().health()
    assert result["ok"] is True
    assert result["tool"] == "health"
    assert result["service"] == "crypto-mcp"


def test_list_exchanges_shape() -> None:
    result = _mcp_server().list_exchanges()
    assert result["ok"] is True
    assert result["tool"] == "list_exchanges"
    assert isinstance(result["items"], list)
