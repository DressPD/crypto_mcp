# crypto_mcp

`crypto_mcp` is a refactor of `crypto_bot` into a single MCP-first repository.

## Goals

- Expose deterministic MCP tools over stdio.
- Keep transport contract stable for LLM clients.
- Separate market data (safe/read-only) from trading (gated).
- Keep exchange adapters replaceable.

## Architecture

- `src/crypto_mcp/mcp_server.py`: FastMCP server and tool definitions.
- `src/crypto_mcp/config.py`: Typed settings loader with sane defaults and clamps.
- `src/crypto_mcp/adapters/binance.py`: Binance HTTP adapter abstraction.
- `src/crypto_mcp/main.py`: Runnable MCP entrypoint.
- `tests/`: MCP contract and adapter unit tests.

Design pattern references taken from `polymarket_mcp`:

- deterministic tool envelope: `{ok, tool, ...}`
- bounded limits for list/read tools
- safety confirmation flow for trade tools
- split entrypoint (`main.py`) from MCP server implementation

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
pytest
python -m crypto_mcp.main
```

## Environment

Copy `.env.example` to `.env` and update values.

- `MCP_DEFAULT_LIMIT`, `MCP_MAX_LIMIT`
- `MCP_CONTEXT_MODE` (`shared` or `request`)
- `DRY_RUN` (`true`/`false`)
- `EXCHANGES_ENABLED` (`binance` default)
- `BINANCE_API_BASE_URL`
- `BINANCE_API_KEY`, `BINANCE_API_SECRET`
- `REQUIRE_CONFIRMATION_ABOVE_USD`

## Safety Notes

- `submit_demo_order` always dry-run payload now.
- `submit_order` requires explicit confirmation for large notional.
- response shape never raises raw exceptions to MCP caller; errors are categorized.
