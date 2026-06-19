# Adapters Changelog

All notable changes to the Antimatter integrations (AG, AG2, CC) will be documented here.

## [2.0.0] - 2026-06-19

### Antigravity IDE (AG) Adapter
* **Changed:** Stripped out Cloudflare, Localtunnel, and crypto logic. The extension is now a pure UI and workspace-watcher layer that communicates via IPC to the Core Gateway.
* **Changed:** Removed `bs58`, `qrcode-terminal`, and `tweetnacl` dependencies as security is now handled by the Gateway.
* **Removed:** Unsanitized Command Injection (replaced raw text inputs with structured `vscode.commands.executeCommand` calls).
* **Removed:** Plaintext Cloudflare Config from `package.json`.
* **Fixed:** Dynamic Watcher Reattachment to handle race conditions where `fs.watch` missed logs.
* **Fixed:** Atomic File Operations — `manual_input.json` writes now use `fs.renameSync` with temp files, fixing intermittent message delivery failures.

### Antigravity 2.0 (AG2) Adapter
* **Added:** New native Python (`asyncio`) daemon adapter for monitoring the standalone Antigravity 2.0 application.
* **Added:** Dual-Bridge compatibility to ensure the same WebSocket protocol is maintained via the Gateway.
* **Fixed:** Path Traversal vulnerability (Arbitrary File Read) in `READ_ARTIFACT` by properly resolving and checking bounds against the workspace directory.
* **Fixed:** Removed raw Base64 image data from exception logs.

### Claude Code (CC) Adapter
* **Added:** New standalone Node.js daemon using `@anthropic-ai/claude-agent-sdk` to stream Claude Code events via the Antimatter Gateway.
