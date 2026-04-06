# crypto_mcp

`crypto_mcp` is a refactor of `crypto_bot` into a single MCP-first repository.

Python requirement: `>=3.11`.

For user-facing capability map, see: `docs/CAPABILITIES.MD`.

## What this project does

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
- `tests/`: MCP contract, core server, and agent unit tests.

Detailed architecture: `docs/ARCHITECTURE.MD`.

## Capabilities quick table

| Area | What it does | Main MCP tools |
|---|---|---|
| Runtime health | Reports service state, limits, mode, exchanges | `health` |
| Exchange inventory | Lists adapter-backed exchanges | `list_exchanges` |
| Market data | Fetches ticker prices and symbol lists | `get_price`, `list_exchange_symbols` |
| Guarded execution | Submits demo orders with explicit confirmation gate | `submit_demo_order`, `confirm_pending_order` |
| NL routing | Maps natural language to MCP tool calls | `crypto-mcp-agent` |

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

Setup path-style variant:

```bash
cd /path/to/crypto_mcp
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

Alternative module runner:

```bash
python -m crypto_mcp.main
crypto-mcp
```

## Safety defaults

- `DRY_RUN=true`

Default path is non-live demo execution.

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

Available MCP tools:

- `health`
- `list_exchanges`
- `get_price`
- `list_exchange_symbols`
- `submit_demo_order`
- `confirm_pending_order`

Tool response envelope is consistent:

- `ok`: boolean
- `tool`: tool name
- `error` + `error_category` on failures
- tool-specific payload under `payload`

MCP limits are controlled by:

- `MCP_DEFAULT_LIMIT`
- `MCP_MAX_LIMIT`
- `MCP_CONTEXT_MODE` (`shared` or `request`)

Order safety controls are controlled by:

- `DRY_RUN`
- `REQUIRE_CONFIRMATION_ABOVE_USD`

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
- `list_exchange_symbols`
- `submit_demo_order`
- `confirm_pending_order`

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
- `GEMINI_API_KEY` (optional, used by local NL routing layer)
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

Order confirmation flow:

1. Call `submit_demo_order`.
2. If payload has `status=pending_confirmation`, capture `confirmation_id`.
3. Call `confirm_pending_order(confirmation_id)`.

Contract:
- deterministic response envelope: `{ok, tool, payload}` on success.
- deterministic error envelope: `{ok, tool, error, error_category}` on failure.
- live trading intentionally disabled: returns `live_trading_not_implemented` when `DRY_RUN=false`.

## Safety Notes

- `submit_demo_order` never executes live orders; with `DRY_RUN=false` it returns `live_trading_not_implemented`.
- `submit_demo_order` requires explicit confirmation for large notional.
- response shape never raises raw exceptions to MCP caller; errors are categorized.

## Tests

```bash
python -m pytest
```

## Important notes

- Local MCP stdio transport must keep stdout clean JSON-RPC only.
- This project is starter infrastructure. Not trading advice.
- Add stronger risk modules before real funds.

## Known improvement areas (scan summary)

- Add adapter-level symbol tradability validation before order acceptance.
- Replace broad internal exception mapping with sanitized provider error codes.
- Add confirmation-expiry regression tests at MCP wrapper level.
- Add optional HTTP transport runner for remote clients.
