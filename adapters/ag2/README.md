# Antimatter: Antigravity 2.0 Adapter (AG2)

This directory contains the Antimatter IPC adapter for the Antigravity 2.0 SDK CLI.

## Architecture

This adapter follows the **Independent Adapter Model**. It does NOT contain any complex networking, Cloudflare tunnels, or cryptographic pairing logic. Instead, it acts purely as a "dumb" IPC client that connects to the central Antimatter Gateway.

1. **Connection**: The daemon connects locally to the Gateway via WebSocket at `ws://127.0.0.1:8765`.
2. **Registration**: Upon connection, it sends `{"type": "REGISTER_ADAPTER", "name": "ag2"}`.
3. **Execution**: When you send a message from the Antimatter Android app targeting AG2, the Gateway securely routes that payload to this adapter. This adapter interfaces with the Antigravity 2.0 SDK by monitoring the `.system_generated/logs/transcript.jsonl` files and submitting local Python subprocess commands.

## Building

Using `pip`:
```bash
pip install antimatter-ag2
```

Using `uv` (recommended for isolation):
```bash
uv tool install antimatter-ag2
```

For full system documentation, please see the `docs/` folder in the repository root.
