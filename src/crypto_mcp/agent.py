from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any

from . import mcp_server


@dataclass(frozen=True)
class ToolDecision:
    tool: str
    args: dict[str, Any]


class CryptoAgent:
    def __init__(self, gemini_api_key: str | None = None):
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")

    def decide(self, prompt: str) -> ToolDecision:
        text = prompt.strip()
        lower = text.lower()

        match = re.search(r"confirm\s+([a-f0-9]{8,64})", lower)
        if match:
            return ToolDecision(
                tool="confirm_pending_order", args={"confirmation_id": match.group(1)}
            )

        if any(keyword in lower for keyword in ["buy", "sell", "order", "trade"]):
            symbol = _extract_symbol(text)
            side = "SELL" if "sell" in lower else "BUY"
            usd_size = _extract_float(lower, default=25.0)
            exchange = _extract_exchange(lower)
            return ToolDecision(
                tool="submit_demo_order",
                args={
                    "exchange": exchange,
                    "symbol": symbol,
                    "side": side,
                    "usd_size": usd_size,
                },
            )

        if any(keyword in lower for keyword in ["price", "quote", "ticker"]):
            symbol = _extract_symbol(text)
            exchange = _extract_exchange(lower)
            return ToolDecision(tool="get_price", args={"exchange": exchange, "symbol": symbol})

        if any(keyword in lower for keyword in ["symbol", "symbols", "pairs"]):
            limit = _extract_int(lower, default=10)
            exchange = _extract_exchange(lower)
            return ToolDecision(
                tool="list_exchange_symbols",
                args={"exchange": exchange, "limit": limit},
            )

        if any(
            phrase in lower
            for phrase in ["list exchanges", "which exchanges", "supported exchanges"]
        ):
            return ToolDecision(tool="list_exchanges", args={})

        return ToolDecision(tool="health", args={})

    def process(self, prompt: str) -> dict[str, Any]:
        decision = self.decide(prompt)
        if decision.tool == "list_exchanges":
            result = mcp_server.list_exchanges()
        elif decision.tool == "list_exchange_symbols":
            result = mcp_server.list_exchange_symbols(**decision.args)
        elif decision.tool == "get_price":
            result = mcp_server.get_price(**decision.args)
        elif decision.tool == "submit_demo_order":
            result = mcp_server.submit_demo_order(**decision.args)
        elif decision.tool == "confirm_pending_order":
            result = mcp_server.confirm_pending_order(**decision.args)
        else:
            result = mcp_server.health()

        return {
            "ok": bool(result.get("ok", False)),
            "tool": decision.tool,
            "args": decision.args,
            "response": result,
        }


def run_interactive() -> None:
    agent = CryptoAgent()
    print("crypto_mcp agent ready. Type 'exit' to quit.")
    while True:
        prompt = input("You: ").strip()
        if prompt.lower() in {"exit", "quit"}:
            print("Bye")
            return
        response = agent.process(prompt)
        print(json.dumps(response, indent=2))


def _extract_exchange(lower_text: str) -> str:
    if "binance" in lower_text:
        return "binance"
    return "binance"


def _extract_symbol(text: str) -> str:
    upper = text.upper()
    known = re.findall(r"\b[A-Z]{3,10}USDT\b", upper)
    if known:
        return known[0]
    return "BTCUSDT"


def _extract_int(text: str, default: int) -> int:
    match = re.search(r"\b(\d{1,4})\b", text)
    if not match:
        return default
    return int(match.group(1))


def _extract_float(text: str, default: float) -> float:
    match = re.search(r"\b(\d+(?:\.\d+)?)\b", text)
    if not match:
        return default
    return float(match.group(1))
