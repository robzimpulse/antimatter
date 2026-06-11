# WebSocket Protocol Reference

This is the complete contract spoken between the **VS Code extension** (the *bridge server*) and
the **Android app** (the *client*). Everything on this page is derived directly from the source
code:

- Extension message types: [`extension/src/core/network/types.ts`](https://github.com/saifmukhtar/antimatter/blob/main/extension/src/core/network/types.ts)
- Server / auth behaviour: [`BridgeWebSocketServer.ts`](https://github.com/saifmukhtar/antimatter/blob/main/extension/src/core/network/BridgeWebSocketServer.ts), [`AuthHandler.ts`](https://github.com/saifmukhtar/antimatter/blob/main/extension/src/feature/connect/AuthHandler.ts)
- Client message model: [`BridgeMessage.kt`](https://github.com/saifmukhtar/antimatter/blob/main/android/core/network/src/main/java/dev/saifmukhtar/antimatter/core/network/BridgeMessage.kt)

All frames are **UTF‑8 JSON text** objects with a `type` discriminator field. `permessage-deflate`
compression is enabled, and the maximum payload size is **10 MiB**.

---

## Connection lifecycle

```text
Android App                               VS Code Extension (Bridge)
    │                                              │
    │  WSS upgrade  (Bearer token)                 │
    │ ───────────────────────────────────────────►│  verifyClient: Origin check
    │                                              │  verifyToken: timing-safe compare
    │  ◄──────────── 101 Switching Protocols ──────│  (or 401 / 403 / close)
    │                                              │
    │  AUTH_CHALLENGE { challenge }                │
    │ ───────────────────────────────────────────►│  sign(nonce) with Ed25519 key
    │  ◄──────────── AUTH_RESPONSE { signature } ──│  client marked authenticated
    │                                              │
    │  SUBSCRIBE_CONVERSATION / GET_HISTORY / ...  │
    │ ◄──────────────────────────────────────────►│  STEP / FILE_TREE / SESSION_STATE ...
```

### 1. Transport & origin validation
The server binds to `127.0.0.1` on the configured `antimatter.port` (default **8765**) and is
exposed publicly through a Cloudflare tunnel. During the HTTP upgrade, the server validates the
`Origin` header — only `vscode-webview://…` origins and `https://‹team›.cloudflareaccess.com`
origins are allowed. Anything else is rejected with **HTTP 403 Forbidden Origin**, which blocks
Cross‑Site WebSocket Hijacking (CSWSH).

### 2. Bearer token authentication
The client must present the 256‑bit pairing token (transferred via the QR pairing code). The
server reads it, in priority order, from:

1. `Authorization: Bearer ‹token›` header
2. The first `Sec-WebSocket-Protocol` value
3. A `?token=‹token›` URL query parameter

The token is compared with `crypto.timingSafeEqual`. An invalid/missing token closes the socket
with code **`4001` Unauthorized**.

### 3. Ed25519 cryptographic handshake
After the socket opens, the client sends an `AUTH_CHALLENGE` containing a base64 nonce. The bridge
signs the raw nonce bytes with its persistent **Ed25519** private key (stored in VS Code
`SecretStorage`) and returns an `AUTH_RESPONSE` with the base64 signature. The client verifies the
signature against the bridge public key it learned during pairing, which proves it is talking to
the genuine bridge and not a tunnel impostor. Only then is the client marked authenticated.

### WebSocket close codes

| Code   | Meaning        | Cause |
|--------|----------------|-------|
| `4001` | Unauthorized   | Missing or invalid pairing token |
| `403`  | Forbidden Origin (HTTP) | `Origin` header not in the allow‑list |

!!! note "Rate limiting planned"
    Per-IP rate limiting (close code `4000`) is planned as a future feature to prevent brute-force token attacks.

---

## Inbound messages (App → Bridge)

These are defined by the `InboundMessage` union in `types.ts` and dispatched by
[`MessageRouter`](https://github.com/saifmukhtar/antimatter/blob/main/extension/src/core/network/MessageRouter.ts).
If a handler throws, the bridge replies with an `ERROR` message; unknown `type`s are logged and
ignored.

| `type` | Fields | Purpose |
|--------|--------|---------|
| `AUTH_CHALLENGE` | `challenge: string` (base64 nonce) | Begin the Ed25519 handshake. |
| `PING` | — | Keepalive; bridge replies with `PONG`. |
| `SEND_MESSAGE` | `text: string` | Send a prompt to the active agent. |
| `NEW_CONVERSATION` | — | Start a fresh conversation. |
| `CANCEL_RESPONSE` | — | Cancel the in‑flight agent response. |
| `ACCEPT_EDITS` / `REJECT_EDITS` | — | Accept or reject all proposed file edits. |
| `NEXT_HUNK` / `PREV_HUNK` | — | Navigate between diff hunks. |
| `ACCEPT_HUNK` / `REJECT_HUNK` | — | Accept or reject the current diff hunk. |
| `SUBSCRIBE_CONVERSATION` | `conversationId: string`, `lastKnownStepCount?: number` | Stream a conversation; optionally resume after a known step index. |
| `GET_HISTORY` | — | Request the list of past conversations. |
| `GET_ARTIFACTS` | `conversationId: string` | Request artifacts for a conversation. |
| `GET_FILES` | `path?: string` | Request the workspace file tree (optionally scoped to a path). |
| `READ_FILE` | `path: string` | Read a file's contents. |
| `WRITE_FILE` | `path: string`, `content: string` | Overwrite a file's contents. |
| `EXECUTE_COMMAND` | `command: string` | Run a shell command on the host (biometric‑gated on the client). |

---

## Outbound messages (Bridge → App)

Defined by the `OutboundMessage` union in `types.ts`.

| `type` | Fields | Purpose |
|--------|--------|---------|
| `AUTH_RESPONSE` | `signature: string` (base64) | Signed handshake nonce. |
| `PONG` | — | Reply to `PING`. |
| `SESSION_STATE` | `conversationId: string \| null`, `model: string`, `stepCount: number`, `cloudflareUrl: string \| null` | Current bridge/session snapshot. |
| `STEP` | `step: TrajectoryStep`, `index: number` | A single new trajectory step. |
| `STEP_BATCH` | `steps: { step: TrajectoryStep; index: number }[]` | Many steps at once (e.g. on subscribe/resume). |
| `GENERATING` | `conversationId: string` | Agent has started generating a response. |
| `RESPONSE_COMPLETE` | `conversationId: string` | Agent finished the current response. |
| `ACTIVE_FILE` | `path: string`, `language: string` | The file currently focused in the IDE. |
| `FILE_CONTENT` | `path: string`, `content: string`, `language: string` | Result of `READ_FILE`. |
| `FILE_TREE` | `tree: FileNode[]` | Result of `GET_FILES`. |
| `CLOUDFLARE_URL` | `url: string` | The public tunnel URL. |
| `HISTORY_LIST` | `conversations: { id: string; timestamp: number; title: string }[]` | Result of `GET_HISTORY`. |
| `ARTIFACTS_LIST` | `artifacts: any[]` | Result of `GET_ARTIFACTS`. |
| `COMMAND_OUTPUT` | `text: string`, `isError: boolean` | Streamed output from `EXECUTE_COMMAND`. |
| `SUCCESS` | `message: string` | Generic success acknowledgement. |
| `ERROR` | `message: string` | A handler failed or a request was invalid. |

---

## Shared data structures

### `TrajectoryStep`
A single step of the agent's trajectory, parsed from AntiGravity's `transcript.jsonl`.

```ts
interface TrajectoryStep {
  case: string;        // step kind, e.g. "text", "toolCall", "runCommand"
  value?: string;      // textual content
  tool?: string;       // tool name (for tool calls)
  command?: string;    // command (for runCommand)
  [key: string]: unknown;
}
```

On Android the `case` string is mapped to a `StepCase` enum which drives rendering:

| `StepCase` | Raw `case` value |
|------------|------------------|
| `USER_INPUT` | `userInput` |
| `PLANNER_RESPONSE` | `plannerResponse` |
| `MARKDOWN_CHUNK` | `markdownChunk` |
| `TEXT` | `text` |
| `TOOL_CALL` | `toolCall` |
| `RUN_COMMAND` | `runCommand` |
| `ERROR_MESSAGE` | `errorMessage` |
| `EPHEMERAL_MESSAGE` | `ephemeralMessage` |
| `CHECKPOINT` | `checkpoint` |
| `TASK_BOUNDARY` | `taskBoundary` |
| `INVOKE_SUBAGENT` | `invokeSubagent` |
| `SEND_MESSAGE` | `sendMessage` |
| `APPROVAL_INTERACTION` | `approvalInteraction` |
| `ELICITATION` | `elicitation` |
| `ASK_QUESTION` | `askQuestion` |
| `UNKNOWN` | *(fallback)* |

### `FileNode`
A node in the workspace file tree returned by `FILE_TREE`.

```ts
interface FileNode {
  name: string;
  path: string;
  isDir: boolean;
  children?: FileNode[];
}
```

---

## Worked example

A minimal client session after the socket is authenticated:

```jsonc
// App → Bridge: open the handshake
{ "type": "AUTH_CHALLENGE", "challenge": "9b6c…base64…" }
// Bridge → App
{ "type": "AUTH_RESPONSE", "signature": "Mf3p…base64…" }

// App → Bridge: load history, then subscribe to one conversation
{ "type": "GET_HISTORY" }
{ "type": "SUBSCRIBE_CONVERSATION", "conversationId": "abc123", "lastKnownStepCount": 0 }

// Bridge → App: state + backlog + live updates
{ "type": "SESSION_STATE", "conversationId": "abc123", "model": "gpt-x", "stepCount": 42, "cloudflareUrl": "wss://ide.example.com" }
{ "type": "STEP_BATCH", "steps": [ { "index": 0, "step": { "case": "userInput", "value": "Hi" } } ] }
{ "type": "GENERATING", "conversationId": "abc123" }
{ "type": "STEP", "index": 43, "step": { "case": "text", "value": "Working on it…" } }
{ "type": "RESPONSE_COMPLETE", "conversationId": "abc123" }
```
