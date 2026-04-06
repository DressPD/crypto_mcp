from __future__ import annotations

from typing import Any

import requests


class BinanceAdapter:
    def __init__(self, base_url: str, api_key: str | None, api_secret: str | None) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.api_secret = api_secret
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({"X-MBX-APIKEY": api_key})

    def close(self) -> None:
        self.session.close()

    def ping(self) -> dict[str, Any]:
        response = self.session.get(f"{self.base_url}/api/v3/ping", timeout=10)
        response.raise_for_status()
        return {"status": "ok"}

    def ticker_price(self, symbol: str) -> dict[str, Any]:
        response = self.session.get(
            f"{self.base_url}/api/v3/ticker/price",
            params={"symbol": symbol.upper()},
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

    def exchange_info(self, symbol: str | None = None) -> dict[str, Any]:
        params = {"symbol": symbol.upper()} if symbol else None
        response = self.session.get(
            f"{self.base_url}/api/v3/exchangeInfo", params=params, timeout=10
        )
        response.raise_for_status()
        return response.json()
