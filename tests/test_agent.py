from typing import Any
import importlib
import builtins


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


def test_extract_defaults_when_prompt_has_no_numbers_or_symbol() -> None:
    mod = importlib.import_module("crypto_mcp.agent")
    assert mod._extract_symbol("hello") == "BTCUSDT"
    assert mod._extract_int("no number", 10) == 10
    assert mod._extract_float("no float", 2.5) == 2.5


def test_run_interactive_one_round_then_exit(monkeypatch: Any) -> None:
    mod = importlib.import_module("crypto_mcp.agent")

    prompts = iter(["price btcusdt", "exit"])

    def fake_input(_: str) -> str:
        return next(prompts)

    def fake_process(_: Any, __: str) -> dict[str, object]:
        return {"ok": True, "tool": "get_price", "response": {"ok": True}}

    monkeypatch.setattr(builtins, "input", fake_input)
    monkeypatch.setattr(mod.CryptoAgent, "process", fake_process)
    monkeypatch.setattr(builtins, "print", lambda *args, **kwargs: None)

    mod.run_interactive()


def test_decide_confirm_route() -> None:
    agent = _agent_cls()()
    decision = agent.decide("confirm abcdef1234")
    assert decision.tool == "confirm_pending_order"
    assert decision.args["confirmation_id"] == "abcdef1234"


def test_decide_list_exchanges_phrase() -> None:
    agent = _agent_cls()()
    decision = agent.decide("which exchanges are supported")
    assert decision.tool == "list_exchanges"


def test_process_dispatches_all_tools(monkeypatch) -> None:
    agent_mod = importlib.import_module("crypto_mcp.agent")
    agent = agent_mod.CryptoAgent()

    monkeypatch.setattr(agent_mod.mcp_server, "list_exchanges", lambda: {"ok": True})
    monkeypatch.setattr(
        agent_mod.mcp_server,
        "list_exchange_symbols",
        lambda **_kwargs: {"ok": True},
    )
    monkeypatch.setattr(agent_mod.mcp_server, "get_price", lambda **_kwargs: {"ok": True})
    monkeypatch.setattr(
        agent_mod.mcp_server,
        "submit_demo_order",
        lambda **_kwargs: {"ok": False},
    )
    monkeypatch.setattr(
        agent_mod.mcp_server,
        "confirm_pending_order",
        lambda **_kwargs: {"ok": True},
    )

    result = agent.process("which exchanges")
    assert result["ok"] is True
    assert result["tool"] == "list_exchanges"

    result = agent.process("symbols 9")
    assert result["tool"] == "list_exchange_symbols"

    result = agent.process("price btcusdt")
    assert result["tool"] == "get_price"

    result = agent.process("buy 10 btcusdt")
    assert result["ok"] is False
    assert result["tool"] == "submit_demo_order"

    result = agent.process("confirm abcdef1234")
    assert result["tool"] == "confirm_pending_order"
