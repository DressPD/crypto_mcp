import runpy
import sys
import importlib


def test_main_module_executes_main_guard(monkeypatch) -> None:
    called = {"ok": False}
    mcp_server_module = importlib.import_module("crypto_mcp.mcp_server")
    monkeypatch.setattr(mcp_server_module, "main", lambda: called.__setitem__("ok", True))
    sys.modules.pop("crypto_mcp.main", None)
    runpy.run_module("crypto_mcp.main", run_name="__main__")
    assert called["ok"] is True


def test_agent_main_module_executes_main_guard(monkeypatch) -> None:
    called = {"ok": False}

    original_import_module = importlib.import_module

    class _FakeAgentModule:
        @staticmethod
        def run_interactive() -> None:
            called["ok"] = True

    def _fake_import_module(name: str, package: str | None = None):
        if name == "crypto_mcp.agent":
            return _FakeAgentModule
        return original_import_module(name, package)

    monkeypatch.setattr(importlib, "import_module", _fake_import_module)
    sys.modules.pop("crypto_mcp.agent_main", None)
    runpy.run_module("crypto_mcp.agent_main", run_name="__main__")
    assert called["ok"] is True
