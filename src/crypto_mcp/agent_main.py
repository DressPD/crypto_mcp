from __future__ import annotations

import importlib


def main() -> None:
    agent_module = importlib.import_module("crypto_mcp.agent")
    agent_module.run_interactive()


if __name__ == "__main__":
    main()
