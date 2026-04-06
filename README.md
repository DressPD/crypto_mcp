# crypto_mcp

`crypto_mcp` is a refactor of `crypto_bot` into a single MCP-first repository.

Python requirement: `>=3.11`.

## Goals

- Expose deterministic MCP tools over stdio.
- Keep transport contract stable for LLM clients.
- Separate market data (safe/read-only) from trading (gated).
- Keep exchange adapters replaceable.

## Architecture

- `src/crypto_mcp/mcp_server.py`: FastMCP server and tool definitions.
- `src/crypto_mcp/agent.py`: NL command router mapping prompts to MCP tools.
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
pip install -e ".[dev]"
cp .env.example .env
python -m pytest
crypto-mcp-server
# separate terminal
crypto-mcp-agent
```

Alternative module runner:

```bash
python -m crypto_mcp.main
```

## Run MCP server locally

Stdio server (local MCP clients):

```bash
crypto-mcp-server
```

For MCP Inspector debugging:

```bash
npx @modelcontextprotocol/inspector python -m crypto_mcp.main
```

Do not write `print()` logs inside stdio server paths. Use logging to stderr.

## Connect this MCP to clients

Use path placeholders:

- `path/to/crypto_mcp` = repository root.
- `path/to/crypto_mcp/.venv/bin/python` = project interpreter.

### GitHub Copilot (VS Code Agent Mode)

Add MCP server config in your VS Code MCP settings JSON:

```json
{
  "mcpServers": {
    "crypto-mcp": {
      "command": "python",
      "args": ["-m", "crypto_mcp.main"],
      "cwd": "path/to/crypto_mcp",
      "env": {
        "PYTHONPATH": "src"
      }
    }
  }
}
```

If your environment requires venv binary, use:

```json
{
  "command": "path/to/crypto_mcp/.venv/bin/python",
  "args": ["-m", "crypto_mcp.main"]
}
```

### Claude Desktop

Edit Claude Desktop MCP config and add:

```json
{
  "mcpServers": {
    "crypto-mcp": {
      "command": "path/to/crypto_mcp/.venv/bin/python",
      "args": ["-m", "crypto_mcp.main"],
      "cwd": "path/to/crypto_mcp",
      "env": {
        "PYTHONPATH": "src"
      }
    }
  }
}
```

Restart Claude Desktop after changes.

### OpenCode

OpenCode can run MCP from command config. Add server entry in your OpenCode MCP configuration:

```json
{
  "mcpServers": {
    "crypto-mcp": {
      "command": "path/to/crypto_mcp/.venv/bin/python",
      "args": ["-m", "crypto_mcp.main"],
      "cwd": "path/to/crypto_mcp",
      "env": {
        "PYTHONPATH": "src"
      }
    }
  }
}
```

Then restart OpenCode session and verify tools:
- `health`
- `list_exchanges`
- `get_price`

OpenCode install and usage:

```bash
# install OpenCode (example)
npm install -g opencode-ai

# verify installation
opencode --version

# start session in this repository
cd path/to/crypto_mcp
opencode
```

Inside OpenCode:
- ensure MCP server `crypto-mcp` is connected.
- run a quick tool check with `health`.
- ask natural language command examples:
  - "get btcusdt price"
  - "list 20 symbols"
  - "buy 50 btcusdt"

## Environment

Copy `.env.example` to `.env` and update values.

- `MCP_DEFAULT_LIMIT`, `MCP_MAX_LIMIT`
- `MCP_CONTEXT_MODE` (`shared` or `request`)
- `DRY_RUN` (`true`/`false`)
- `EXCHANGES_ENABLED` (`binance` default)
- `BINANCE_API_BASE_URL`
- `BINANCE_API_KEY`, `BINANCE_API_SECRET`
- `REQUIRE_CONFIRMATION_ABOVE_USD`

For this task, an empty `.env` file exists and is safe because defaults are clamped.

## What this MCP can do

Read-only tools:
- `health`: service status, context mode, limits, enabled exchanges.
- `list_exchanges`: list adapter-backed exchanges.
- `get_price`: fetch ticker price for symbol/exchange.
- `list_exchange_symbols`: bounded symbol list with clamp.

Trading flow tools (safety-gated):
- `submit_demo_order`: validates side/symbol/size and creates pending confirmation above threshold.
- `confirm_pending_order`: executes pending order if valid and not expired.

Contract:
- deterministic response envelope: `{ok, tool, payload}` on success.
- deterministic error envelope: `{ok, tool, error, error_category}` on failure.
- live trading intentionally disabled: returns `live_trading_not_implemented` when `DRY_RUN=false`.

## Safety Notes

- `submit_demo_order` never executes live orders; with `DRY_RUN=false` it returns `live_trading_not_implemented`.
- `submit_order` requires explicit confirmation for large notional.
- response shape never raises raw exceptions to MCP caller; errors are categorized.

## Known improvement areas (scan summary)

- Add adapter-level symbol tradability validation before order acceptance.
- Replace broad internal exception mapping with sanitized provider error codes.
- Add confirmation-expiry regression tests at MCP wrapper level.
- Add optional HTTP transport runner for remote clients.
