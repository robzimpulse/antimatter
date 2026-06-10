# Roadmap

Planned features and architectural improvements for the Antimatter ecosystem. Items are prioritized by security first, then core functionality, then quality-of-life.

!!! info "Want to help?"
    Many of these items are great first contributions. Check the [Contributing Guide](CONTRIBUTING.md) to get started.

---

## :material-shield-lock: Security & Privacy

### :material-lock: End-to-End Encryption (E2EE)

**Status:** :material-clock-outline: Planned

Currently, the WebSocket connection is secured by TLS (via Cloudflare) and a 256-bit pairing token with Ed25519 handshake. However, to ensure **absolute privacy even from tunnel providers**, we plan to implement true E2EE using a Diffie-Hellman key exchange:

- Traffic encrypted *before* leaving the VS Code extension
- Decrypted only on the Android device
- **Zero-knowledge routing** through any intermediary (Cloudflare, proxies, etc.)

---

## :material-rocket-launch: Core Features

### :material-console-line: Advanced Terminal Integration

**Status:** :material-clock-outline: Planned

The current terminal uses `child_process.spawn` to proxy commands. The future goal is a fully featured, isolated terminal:

| Feature | Description |
|---------|-------------|
| **PTY support** | Use `node-pty` for a true TTY environment — interactive commands like `vim`, `htop`, and prompts |
| **Sandboxing** | Restrict terminal sessions to the workspace directory to prevent accidental global changes |
| **ANSI rendering** | Xterm.js-style renderer in Jetpack Compose for colored output, cursor movements, and complex TUI layouts |

### :material-swap-horizontal: Remote Workspace Switching

**Status:** :material-thought-bubble: Under consideration (long-term)

Allow users to browse and switch the active VS Code workspace from the Android app.

!!! warning "Security implications"
    Granting the companion app filesystem navigation vastly expands the attack surface. If implemented, this will require:

    - Pre-approved workspace whitelists
    - Secondary biometric confirmations
    - Restricted filesystem read access

---

## :material-timeline-check: Status Legend

| Icon | Meaning |
|------|---------|
| :material-check-circle: | Shipped |
| :material-progress-wrench: | In progress |
| :material-clock-outline: | Planned |
| :material-thought-bubble: | Under consideration |
