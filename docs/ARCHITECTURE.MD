# crypto_mcp Architecture

## Overview

`crypto_mcp` exposes local MCP tools for market reads and guarded demo order flow.

- Read-only tools: `health`, `list_exchanges`, `get_price`, `list_exchange_symbols`
- Trade-gated tools: `submit_demo_order`, `confirm_pending_order`

For user-facing tool behavior, see `docs/CAPABILITIES.MD`.

## Core Components

- `src/crypto_mcp/mcp_server.py`
  - FastMCP server registration
  - deterministic response envelopes
  - wrapper-level error categorization
- `src/crypto_mcp/server.py`
  - runtime context container
  - exchange adapter routing
  - order validation and confirmation lifecycle
- `src/crypto_mcp/config.py`
  - environment loading
  - typed parsing and clamps for safety limits
- `src/crypto_mcp/adapters/binance.py`
  - Binance REST calls (`ping`, `ticker_price`, `exchange_info`)
- `src/crypto_mcp/agent.py`
  - natural-language intent routing into MCP tool calls

## Runtime Context Model

`ServerContext` holds:

- `settings`
- `adapters`
- `pending_confirmations`

`mcp_server.py` creates global `_SETTINGS` and global `_CTX` at startup.

### Context mode behavior

- `MCP_CONTEXT_MODE=shared`
  - read tools use global context.
- `MCP_CONTEXT_MODE=request`
  - `list_exchanges`, `get_price`, `list_exchange_symbols` create request-scoped context and close it.

Current behavior note:

- `submit_demo_order` and `confirm_pending_order` use shared `_CTX` for confirmation continuity.

## Request Flow

```text
MCP Client
  -> mcp_server tool wrapper
    -> core server function
      -> Binance adapter / confirmation state
    -> envelope normalization
  -> MCP response
```

## Order Lifecycle

1. `submit_demo_order` validates `exchange`, `symbol`, `side`, `usd_size`.
2. If `usd_size >= REQUIRE_CONFIRMATION_ABOVE_USD`:
   - response returns `pending_confirmation` with `confirmation_id`.
3. `confirm_pending_order(confirmation_id)` executes pending payload if valid and unexpired.
4. If `DRY_RUN=false`, execution returns `live_trading_not_implemented`.

Confirmation expiry window: 15 minutes.

## Response Envelope Contract

Success envelope:

```json
{"ok": true, "tool": "<tool>", "payload": {...}}
```

Error envelope:

```json
{"ok": false, "tool": "<tool>", "error": "<message>", "error_category": "validation|provider|internal"}
```

## Safety and Limits

Configured in `Settings`:

- `MCP_DEFAULT_LIMIT`, `MCP_MAX_LIMIT`
- `MCP_CONTEXT_MODE`
- `DRY_RUN`
- `REQUIRE_CONFIRMATION_ABOVE_USD`
- `EXCHANGES_ENABLED`
- Binance endpoint and credentials

Numeric values are clamped in config parsing.
