# Features

A detailed breakdown of every capability in the Antimatter ecosystem. The system is split into two halves — the **VS Code Extension** (the bridge server on your desktop) and the **Android App** (the mobile client in your pocket) — connected by a secure WebSocket channel.

---

## :material-cellphone: Android App

### :material-message-text: AI Chat Interface

<div class="screenshot-gallery" markdown>

![Chat Interface](images/chats.png){ loading=lazy }
![Chat History](images/chat-history.png){ loading=lazy }

</div>

The chat screen gives you a full view of your AI agent's conversation:

- **Seamless Prompting** — type a message and it's injected directly into the active AntiGravity agent. No copy-paste; the bridge proxies it via `vscode.commands.executeCommand`.
- **Partial Text Selection** — long-press on any AI response or user message to select specific lines of text, triggering the native Android copy/share toolbar.
- **Rich Markdown Rendering** — AI responses render with full Markdown support: **bold**, *italic*, `code`, links, and fenced code blocks with syntax highlighting.
- **Edit Decisions** — when the agent proposes file edits, accept or reject them directly from the chat UI. You can also navigate and act on individual diff hunks.
- **Thinking Indicator** — a live typing/thinking animation shows when the agent is generating.
- **Conversation History** — browse past conversations, tap to subscribe and replay the full trajectory.

### :material-folder-multiple: Workspace Explorer

<div class="screenshot-gallery" markdown>

![Workspace Browser](images/workspace.png){ loading=lazy }
![File Viewer](images/file-viewer.png){ loading=lazy }

</div>

- **Live File Tree** — browse the files in your VS Code workspace. The tree syncs in real-time via the `GET_FILES` / `FILE_TREE` messages.
- **File Viewing** — tap any file to read its contents, syntax-highlighted by language.
- **File Writing** — write file contents back via `WRITE_FILE` (for quick edits on the go).
- **Real-Time Sync** — navigate subdirectories; the tree refreshes as your workspace changes.

### :material-console: Remote Terminal

<div class="screenshot-gallery" markdown>

![Remote Terminal](images/terminal.png){ loading=lazy }

</div>

- **Biometric-Gated** — tapping the terminal icon triggers a **Fingerprint / Face** biometric prompt. The terminal only opens if you're the physical owner of the device.
- **Live Command Proxy** — type a command and it's executed on your host machine's shell via `child_process`. Output streams back in real-time.
- **Real-Time Output** — `stdout` and `stderr` are streamed character-by-character as `COMMAND_OUTPUT` messages. It feels like you're sitting at your desk.
- **Full Permissions** — the terminal runs with the same permissions as your VS Code instance: `git`, `npm`, system configs — full control.

!!! danger "Use responsibly"
    The remote terminal gives full shell access to your host. The biometric lock is your safeguard — treat it accordingly.

### :material-puzzle: Artifacts

<div class="screenshot-gallery" markdown>

![Artifacts UI](images/artifact.png){ loading=lazy }

</div>

- Browse artifacts generated during agent conversations (code files, images, etc.).
- Tap to view artifact contents with syntax highlighting.

### :material-shield-lock: Network Security (Client-side)

- **Cloudflare Zero Trust Integration** — enter your Cloudflare Client ID and Client Secret in the app's Advanced Options for enterprise-grade access control.
- **QR Code Pairing** — scan one QR code to transfer the WebSocket URL, 256-bit pairing token, and Ed25519 public key. No manual entry needed.
- **Token-Based Auth** — every WebSocket connection includes the pairing token as a Bearer credential.
- **Ed25519 Verification** — the app verifies the bridge's identity via a cryptographic handshake after connecting.

---

## :material-puzzle-outline: VS Code Extension

### :material-server-network: Background Bridge Server

- **Silent Operation** — runs an invisible WebSocket server on `127.0.0.1` (default port `8765`), streaming trajectory data, file trees, and chat messages.
- **Auto-Start** — automatically initializes when AntiGravity opens (configurable via `antimatter.autoStart`).
- **Per-Message Compression** — `permessage-deflate` keeps bandwidth low, even for large trajectory payloads.

### :material-key-variant: Cryptographic Authentication

- **256-bit Pairing Token** — generated on first run and stored in VS Code `SecretStorage`. Every connection must present this token (checked with `crypto.timingSafeEqual`).
- **Ed25519 Handshake** — after the token check, the bridge signs a client-provided nonce with its persistent private key, proving its identity and preventing Man-in-the-Middle attacks.
- **Rate Limiting** — 5 failed token attempts = 60-second IP ban (close code `4000`).

!!! info "Full protocol details"
    See the [**WebSocket Protocol Reference**](PROTOCOL.md) for every message type, close code, and handshake step.

### :material-cloud-sync: Cloudflare Tunnel Management

- **Auto-Tunnel** — when `cloudflareHostname` is blank, the extension automatically downloads `cloudflared`, spawns a free Quick Tunnel, and resolves the public URL.
- **Zero Trust Support** — set your hostname and credentials for persistent, enterprise-grade tunnels.
- **One-Click Restart** — run `Antimatter: Restart Cloudflare Tunnel` from the Command Palette.
- **QR Code Generation** — embeds the pairing token, public URL, and bridge public key into a scannable QR code right inside your IDE.

### :material-brain: Agent Trajectory Watcher

- **File System Monitoring** — uses `fs.watch` to follow `brain/<conversation-id>/.system_generated/logs/transcript.jsonl`, parsing each JSON line into a `TrajectoryStep`.
- **Live Streaming** — new steps are broadcast to connected clients as `STEP` frames in real-time.
- **Batch Replay** — when a client subscribes (or resumes), the full backlog is sent as a single `STEP_BATCH`.

---

## :material-compare: Feature Matrix

| Capability | Android App | VS Code Extension |
|-----------|:-----------:|:-----------------:|
| View agent trajectory | :material-check: | :material-check: (generates) |
| Send prompts to agent | :material-check: | :material-check: (proxies) |
| Accept/reject edits | :material-check: | :material-check: (executes) |
| Hunk navigation | :material-check: | :material-check: (executes) |
| Browse workspace files | :material-check: | :material-check: (serves) |
| Read/write files | :material-check: | :material-check: (serves) |
| Remote terminal | :material-check: (biometric) | :material-check: (executes) |
| Conversation history | :material-check: | :material-check: (serves) |
| Artifacts | :material-check: | :material-check: (serves) |
| QR pairing | :material-check: (scans) | :material-check: (generates) |
| Cloudflare tunnels | :material-check: (connects) | :material-check: (manages) |
| Ed25519 handshake | :material-check: (verifies) | :material-check: (signs) |
| Offline history | :material-check: (Room DB) | — |
| Biometric lock | :material-check: | — |

---

## :material-arrow-right-bold: What's Next?

- See the [**Architecture**](ARCHITECTURE.md) page to understand how the bridge reverse-engineers the IDE.
- Read the [**WebSocket Protocol**](PROTOCOL.md) for the full message contract.
- Check the [**Roadmap**](ROADMAP.md) for upcoming features like E2EE and terminal isolation.
