import importlib


class _Response:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self):
        return self._payload


class _Session:
    def __init__(self):
        self.headers = {}
        self.calls = []
        self.closed = False

    def get(self, url, params=None, timeout=None):
        self.calls.append({"url": url, "params": params, "timeout": timeout})
        if url.endswith("/api/v3/ticker/price"):
            symbol = (params or {}).get("symbol", "BTCUSDT")
            return _Response({"symbol": symbol, "price": "1.23"})
        if url.endswith("/api/v3/exchangeInfo"):
            return _Response({"symbols": [{"symbol": "BTCUSDT"}]})
        return _Response({})

    def close(self) -> None:
        self.closed = True


def test_adapter_sets_header_and_calls_endpoints(monkeypatch) -> None:
    module = importlib.import_module("crypto_mcp.adapters.binance")
    fake = _Session()
    monkeypatch.setattr(module.requests, "Session", lambda: fake)

    adapter = module.BinanceAdapter("https://api.binance.com/", "key", "secret")
    assert fake.headers["X-MBX-APIKEY"] == "key"

    assert adapter.ping() == {"status": "ok"}
    price = adapter.ticker_price("btcusdt")
    assert price["symbol"] == "BTCUSDT"
    info = adapter.exchange_info("ethusdt")
    assert isinstance(info["symbols"], list)
    adapter.exchange_info()
    adapter.close()
    assert fake.closed is True

    urls = [entry["url"] for entry in fake.calls]
    assert any(url.endswith("/api/v3/ping") for url in urls)
    assert any(url.endswith("/api/v3/ticker/price") for url in urls)
    assert any(url.endswith("/api/v3/exchangeInfo") for url in urls)
