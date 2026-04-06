import importlib


def test_main_entrypoint_importable() -> None:
    module = importlib.import_module("crypto_mcp.main")
    assert hasattr(module, "main")


def test_main_calls_run_server(monkeypatch) -> None:
    module = importlib.import_module("crypto_mcp.main")
    called = {"ok": False}

    def _run() -> None:
        called["ok"] = True

    monkeypatch.setattr(module, "run_server", _run)
    module.main()
    assert called["ok"] is True


def test_agent_main_calls_run_interactive(monkeypatch) -> None:
    module = importlib.import_module("crypto_mcp.agent_main")
    called = {"ok": False}

    class _AgentModule:
        @staticmethod
        def run_interactive() -> None:
            called["ok"] = True

    monkeypatch.setattr(module.importlib, "import_module", lambda _name: _AgentModule)
    module.main()
    assert called["ok"] is True
