from typing import Any
import importlib


def _agent_cls() -> Any:
    return importlib.import_module("crypto_mcp.agent").CryptoAgent


def test_decide_price_maps_to_get_price() -> None:
    agent = _agent_cls()()
    decision = agent.decide("price for ethusdt on binance")
    assert decision.tool == "get_price"
    assert decision.args["symbol"] == "ETHUSDT"


def test_decide_symbols_maps_to_list_symbols() -> None:
    agent = _agent_cls()()
    decision = agent.decide("list 15 symbols")
    assert decision.tool == "list_exchange_symbols"
    assert decision.args["limit"] == 15


def test_decide_order_maps_to_submit_demo_order() -> None:
    agent = _agent_cls()()
    decision = agent.decide("buy 125 btcusdt")
    assert decision.tool == "submit_demo_order"
    assert decision.args["side"] == "BUY"
    assert decision.args["usd_size"] == 125.0


def test_process_fallback_health() -> None:
    agent = _agent_cls()()
    result = agent.process("hello there")
    assert result["tool"] == "health"
    assert result["response"]["ok"] is True


def test_exchange_word_does_not_override_price_intent() -> None:
    agent = _agent_cls()()
    decision = agent.decide("price btcusdt on binance exchange")
    assert decision.tool == "get_price"


def test_exchange_word_does_not_override_order_intent() -> None:
    agent = _agent_cls()()
    decision = agent.decide("buy 50 btcusdt on binance exchange")
    assert decision.tool == "submit_demo_order"
    assert decision.args["usd_size"] == 50.0
