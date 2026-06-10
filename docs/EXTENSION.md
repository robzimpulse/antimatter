# VS Code Extension Reference

The bridge half of Antimatter is a VS Code / AntiGravity extension written in **TypeScript** and
bundled with **esbuild**. It runs a local WebSocket server, watches the agent's `transcript.jsonl`,
and proxies commands back into the IDE.

- Source: [`extension/`](https://github.com/saifmukhtar/antimatter/tree/main/extension)
- Entry point: [`extension/src/extension.ts`](https://github.com/saifmukhtar/antimatter/blob/main/extension/src/extension.ts)
- Bundle output: `dist/extension.js` (`main` in `package.json`)

## Source layout

```text
extension/src/
├── extension.ts                 # activate(): wires everything together
├── core/
│   ├── network/
│   │   ├── BridgeWebSocketServer.ts   # ws server: origin check, auth, rate limit
│   │   ├── MessageRouter.ts           # type → handler dispatch
│   │   └── types.ts                   # InboundMessage / OutboundMessage / TrajectoryStep / FileNode
│   ├── state/
│   │   └── ChatStateManager.ts        # tracks active conversation + step counts
│   └── data/
│       └── FileSystemHelper.ts        # workspace file tree / read / write helpers
└── feature/
    ├── connect/
    │   ├── AuthHandler.ts             # pairing token + Ed25519 keypair + handshake
    │   ├── ConnectionManager.ts       # connected/authenticated client registry + broadcast
    │   ├── CloudflareTunnel.ts        # spawns/manages cloudflared, resolves public URL
    │   └── QrWebviewProvider.ts       # renders the pairing QR webview
    ├── chat/
    │   ├── BrainWatcher.ts            # fs.watch on the brain/ dir, parses transcript.jsonl
    │   ├── ChatCommandHandler.ts      # SEND_MESSAGE / NEW_CONVERSATION / edit + hunk actions
    │   └── HistoryManager.ts          # enumerates past conversations
    ├── files/
    │   └── FileCommandHandler.ts      # GET_FILES / READ_FILE / WRITE_FILE
    └── terminal/
        └── TerminalCommandHandler.ts  # EXECUTE_COMMAND via child_process
```

## Key modules

### `core/network`
- **`BridgeWebSocketServer`** — creates the `ws` server bound to `127.0.0.1`. Enforces the
  `Origin` allow‑list, extracts and verifies the Bearer token, applies per‑IP rate limiting, and
  forwards every frame to the `MessageRouter`. See the [WebSocket Protocol](PROTOCOL.md) page for
  the exact rules and close codes.
- **`MessageRouter`** — a typed registry mapping each `InboundMessage['type']` to an async handler.
  Parses JSON, dispatches, and converts thrown errors into `ERROR` frames.
- **`types.ts`** — the single source of truth for the wire protocol (`InboundMessage`,
  `OutboundMessage`, `TrajectoryStep`, `FileNode`).

### `feature/connect`
- **`AuthHandler`** — generates/restores a 32‑byte pairing token and a persistent **Ed25519**
  keypair in VS Code `SecretStorage`, performs timing‑safe token verification, and signs
  `AUTH_CHALLENGE` nonces.
- **`ConnectionManager`** — tracks connected sockets, marks them authenticated after the handshake,
  and broadcasts outbound messages to clients.
- **`CloudflareTunnel`** — downloads (if missing) and spawns the `cloudflared` binary, exposing the
  local server and resolving the public `wss://` URL.
- **`QrWebviewProvider`** — renders the pairing QR code (URL + token + bridge public key) as a
  webview.

### `feature/chat`
- **`BrainWatcher`** — uses `fs.watch` to follow the most‑recently‑modified conversation under the
  AntiGravity `brain/<conversation-id>/.system_generated/logs/transcript.jsonl`, parsing each JSON
  line into a `TrajectoryStep` and streaming `STEP` / `STEP_BATCH` frames.
- **`ChatCommandHandler`** — injects prompts and control actions into the agent via
  `vscode.commands.executeCommand` (send message, new conversation, accept/reject edits, hunk
  navigation).
- **`HistoryManager`** — enumerates past conversations for `GET_HISTORY`.

### `feature/files` & `feature/terminal`
- **`FileCommandHandler`** + **`FileSystemHelper`** — serve the workspace file tree and read/write
  individual files.
- **`TerminalCommandHandler`** — proxies `EXECUTE_COMMAND` to a host shell via `child_process`
  (gated behind a biometric lock on the mobile client).

## Commands

Registered in `extension.ts` and declared under `contributes.commands`. Trigger via the Command
Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`):

| Command ID | Title |
|------------|-------|
| `antimatter.showPairingQR` | Antimatter: Show Pairing QR |
| `antimatter.startBridge` | Antimatter: Start Bridge Server |
| `antimatter.stopBridge` | Antimatter: Stop Bridge Server |
| `antimatter.showStatus` | Antimatter: Show Connection Status |
| `antimatter.setCloudflareCredentials` | Antimatter: Set Cloudflare Credentials |
| `antimatter.restartTunnel` | Antimatter: Restart Cloudflare Tunnel |

## Settings

Declared under `contributes.configuration` (search "Antimatter" in VS Code Settings):

| Setting ID | Type | Default | Description |
|------------|------|---------|-------------|
| `antimatter.port` | number | `8765` | WebSocket port for the bridge server. |
| `antimatter.autoStart` | boolean | `true` | Start the bridge automatically when AntiGravity opens. |
| `antimatter.cloudflareHostname` | string | `""` | Cloudflare Zero Trust hostname (e.g. `ide.mydomain.com`). Blank = spawn a free Quick Tunnel. |
| `antimatter.cloudflareClientId` | string | `""` | Cloudflare Zero Trust Access Client ID. |

## Build & scripts

From `extension/package.json`:

| Script | Command | Purpose |
|--------|---------|---------|
| `build` | `node build.mjs` | Bundle to `dist/extension.js` with esbuild. |
| `watch` | `node build.mjs --watch` | Rebuild on change (use with `F5`). |
| `package` | `vsce package` | Produce the `.vsix`. |
| `lint` | `tsc --noEmit` | Type‑check the project. |

Runtime dependencies: `ws` (WebSocket server) and `qrcode` (pairing QR). Requires Node.js 22+.
