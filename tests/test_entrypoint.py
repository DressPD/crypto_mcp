import importlib


def test_main_entrypoint_importable() -> None:
    module = importlib.import_module("crypto_mcp.main")
    assert hasattr(module, "main")
