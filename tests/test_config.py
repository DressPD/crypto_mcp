import importlib


def _config_module():
    return importlib.import_module("crypto_mcp.config")


def test_parse_bool_handles_variants() -> None:
    config = _config_module()
    assert config._parse_bool("true", False) is True
    assert config._parse_bool("1", False) is True
    assert config._parse_bool("off", True) is False
    assert config._parse_bool("no", True) is False
    assert config._parse_bool("maybe", True) is True
    assert config._parse_bool(None, False) is False


def test_parse_int_float_csv_and_clamps() -> None:
    config = _config_module()
    assert config._parse_int("12", 1) == 12
    assert config._parse_int("", 2) == 2
    assert config._parse_int("x", 3) == 3
    assert config._parse_float("1.5", 1.0) == 1.5
    assert config._parse_float("", 2.0) == 2.0
    assert config._parse_float("x", 3.0) == 3.0
    assert config._parse_csv("a, b, , c", ["z"]) == ["a", "b", "c"]
    assert config._parse_csv("", ["z"]) == ["z"]
    assert config._clamp_int(0, 1, 5) == 1
    assert config._clamp_int(9, 1, 5) == 5
    assert config._clamp_float(0.5, 1.0, 2.0) == 1.0
    assert config._clamp_float(5.0, 1.0, 2.0) == 2.0


def test_load_settings_normalizes_and_clamps(monkeypatch) -> None:
    config = _config_module()
    monkeypatch.setattr(config, "_load_dotenv", lambda: True)
    monkeypatch.setenv("MCP_DEFAULT_LIMIT", "999")
    monkeypatch.setenv("MCP_MAX_LIMIT", "5")
    monkeypatch.setenv("MCP_CONTEXT_MODE", "INVALID")
    monkeypatch.setenv("DRY_RUN", "0")
    monkeypatch.setenv("EXCHANGES_ENABLED", "binance, kraken")
    monkeypatch.setenv("BINANCE_API_BASE_URL", "https://x")
    monkeypatch.setenv("BINANCE_API_KEY", "k")
    monkeypatch.setenv("BINANCE_API_SECRET", "s")
    monkeypatch.setenv("REQUIRE_CONFIRMATION_ABOVE_USD", "999999")

    settings = config.load_settings()
    assert settings.mcp_max_limit == 5
    assert settings.mcp_default_limit == 5
    assert settings.mcp_context_mode == config.MCPContextMode.SHARED.value
    assert settings.dry_run is False
    assert settings.exchanges_enabled == ["binance", "kraken"]
    assert settings.binance_api_base_url == "https://x"
    assert settings.binance_api_key == "k"
    assert settings.binance_api_secret == "s"
    assert settings.require_confirmation_above_usd == 100000.0


def test_load_dotenv_false_when_missing(monkeypatch) -> None:
    config = _config_module()

    def raise_import_error(_name: str):
        raise ImportError("missing")

    monkeypatch.setattr(config.importlib, "import_module", raise_import_error)
    assert config._load_dotenv() is False
