# crypto_mcp Capabilities

## What this service is

`crypto_mcp` is a local MCP server for crypto market reads plus guarded demo order workflow.

Default runtime is safety-first (`DRY_RUN=true`).

---

## Core capabilities

### 1) Runtime health and limits

- `health`
  - returns service status, UTC time, context mode, limits, enabled exchanges.

### 2) Exchange discovery

- `list_exchanges`
  - returns adapter-backed exchange list.

### 3) Market reads

- `get_price(exchange, symbol)`
  - ticker price lookup from adapter.
- `list_exchange_symbols(exchange, limit?)`
  - bounded symbol listing with limit clamp.

### 4) Guarded demo order flow

- `submit_demo_order(exchange="binance", symbol="BTCUSDT", side="BUY", usd_size=25.0)`
  - validates order inputs.
  - returns immediate dry-run acceptance for small notional.
  - returns pending confirmation for large notional.
- `confirm_pending_order(confirmation_id)`
  - confirms and executes pending order if valid and unexpired.

### 5) Natural-language routing layer

- `CryptoAgent` maps text intents to MCP tools.
- script entrypoint: `crypto-mcp-agent`.

---

## MCP tool catalog

| Tool | Purpose | Key args |
|---|---|---|
| `health` | Runtime status and limits | none |
| `list_exchanges` | Enabled exchange list | none |
| `get_price` | Symbol price lookup | `exchange`, `symbol` |
| `list_exchange_symbols` | Bounded symbol listing | `exchange`, `limit?` |
| `submit_demo_order` | Guarded demo order submit | `exchange?`, `symbol?`, `side?`, `usd_size?` |
| `confirm_pending_order` | Confirm pending order | `confirmation_id` |

---

## Envelope contract

Success:

```json
{"ok": true, "tool": "<tool>", "payload": {...}}
```

Failure:

```json
{"ok": false, "tool": "<tool>", "error": "<message>", "error_category": "validation|provider|internal"}
```

Common validation errors:

- `invalid_side`
- `invalid_symbol`
- `invalid_usd_size`
- `unsupported_exchange:<name>`
- `confirmation_not_found`
- `confirmation_expired`

Live-disabled execution error:

- `live_trading_not_implemented`

---

## Runtime and environment controls

Primary variables:

- `MCP_DEFAULT_LIMIT`
- `MCP_MAX_LIMIT`
- `MCP_CONTEXT_MODE` (`shared` or `request`)
- `DRY_RUN`
- `EXCHANGES_ENABLED`
- `BINANCE_API_BASE_URL`
- `BINANCE_API_KEY`
- `BINANCE_API_SECRET`
- `REQUIRE_CONFIRMATION_ABOVE_USD`
- `GEMINI_API_KEY` (agent layer)

Safety defaults from `.env.example` keep local usage in non-live mode.
