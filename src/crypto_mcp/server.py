from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from .adapters import BinanceAdapter
from .config import Settings


@dataclass
class PendingConfirmation:
    confirmation_id: str
    action: str
    payload: dict[str, object]
    created_at: datetime
    expires_at: datetime


@dataclass
class ServerContext:
    settings: Settings
    adapters: dict[str, BinanceAdapter] = field(default_factory=dict)
    pending_confirmations: dict[str, PendingConfirmation] = field(default_factory=dict)

    def close(self) -> None:
        for adapter in self.adapters.values():
            close = getattr(adapter, "close", None)
            if callable(close):
                close()


def create_server_context(settings: Settings) -> ServerContext:
    adapters: dict[str, BinanceAdapter] = {}
    if "binance" in [name.lower() for name in settings.exchanges_enabled]:
        adapters["binance"] = BinanceAdapter(
            base_url=settings.binance_api_base_url,
            api_key=settings.binance_api_key,
            api_secret=settings.binance_api_secret,
        )
    return ServerContext(settings=settings, adapters=adapters)


def list_supported_exchanges(ctx: ServerContext) -> list[str]:
    return sorted(ctx.adapters.keys())


def get_market_price(ctx: ServerContext, exchange: str, symbol: str) -> dict[str, object]:
    adapter = _get_exchange_adapter(ctx, exchange)
    payload = adapter.ticker_price(symbol)
    return {
        "exchange": exchange,
        "symbol": payload.get("symbol", symbol.upper()),
        "price": payload.get("price"),
    }


def list_symbols(ctx: ServerContext, exchange: str, limit: int) -> list[dict[str, object]]:
    adapter = _get_exchange_adapter(ctx, exchange)
    info = adapter.exchange_info()
    symbols = info.get("symbols", [])
    items: list[dict[str, object]] = []
    for row in symbols[:limit]:
        items.append(
            {
                "symbol": row.get("symbol"),
                "status": row.get("status"),
                "base_asset": row.get("baseAsset"),
                "quote_asset": row.get("quoteAsset"),
            }
        )
    return items


def submit_order(
    ctx: ServerContext, exchange: str, symbol: str, side: str, usd_size: float
) -> dict[str, object]:
    payload = {
        "exchange": exchange,
        "symbol": symbol.upper(),
        "side": side.upper(),
        "usd_size": usd_size,
        "dry_run": ctx.settings.dry_run,
    }

    if usd_size >= ctx.settings.require_confirmation_above_usd:
        confirmation_id = uuid4().hex
        now = datetime.now(timezone.utc)
        entry = PendingConfirmation(
            confirmation_id=confirmation_id,
            action="submit_order",
            payload=payload,
            created_at=now,
            expires_at=now + timedelta(minutes=15),
        )
        ctx.pending_confirmations[confirmation_id] = entry
        return {
            "status": "pending_confirmation",
            "confirmation_id": confirmation_id,
            "expires_at": entry.expires_at.isoformat(),
            "payload": payload,
        }

    return _execute_order(payload)


def confirm_order(ctx: ServerContext, confirmation_id: str) -> dict[str, object]:
    entry = ctx.pending_confirmations.get(confirmation_id)
    if entry is None:
        return {"ok": False, "error": "confirmation_not_found", "error_category": "validation"}
    if entry.expires_at < datetime.now(timezone.utc):
        ctx.pending_confirmations.pop(confirmation_id, None)
        return {"ok": False, "error": "confirmation_expired", "error_category": "validation"}

    ctx.pending_confirmations.pop(confirmation_id, None)
    return _execute_order(entry.payload)


def _execute_order(payload: dict[str, object]) -> dict[str, object]:
    return {
        "ok": True,
        "status": "accepted",
        "execution_mode": "dry_run" if payload.get("dry_run") else "live_disabled_placeholder",
        "order": payload,
    }


def _get_exchange_adapter(ctx: ServerContext, exchange: str):
    key = exchange.lower()
    if key not in ctx.adapters:
        raise ValueError(f"unsupported_exchange:{exchange}")
    return ctx.adapters[key]
