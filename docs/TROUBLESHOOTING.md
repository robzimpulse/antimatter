# Troubleshooting & FAQ

Common issues when connecting the Antimatter app to the bridge, and how to resolve them. Most
connection failures map to a specific [WebSocket close code](PROTOCOL.md#websocket-close-codes).

## Connection issues

### The phone can't connect / immediately disconnects
- **Invalid token (close `4001`)** — re‑pair: run `Antimatter: Show Pairing QR Code` and scan
  again so the phone receives the current pairing token.
- **Rate limited (close `4000`)** — after 5 failed attempts your IP is banned for 60 seconds. Wait
  a minute, then retry with a fresh QR scan.
- **Forbidden origin (HTTP 403)** — the bridge only accepts `vscode-webview://` and
  `*.cloudflareaccess.com` origins. Make sure you're connecting through the Cloudflare tunnel URL,
  not directly to a raw IP/port.

### "Bridge not running"
- Run **`Antimatter: Start Bridge Server`** from the Command Palette.
- Confirm `antimatter.autoStart` is enabled in Settings.
- Make sure the host has **Node.js 22+** installed.

### Port already in use
- Another process may hold the default port. Change **`antimatter.port`** (default `8765`) in
  Settings, then restart the bridge.

### Tunnel / Cloudflare problems
- Run **`Antimatter: Restart Cloudflare Tunnel`** to respawn `cloudflared`.
- For Zero Trust setups, verify your **Client ID / Secret** via
  **`Antimatter: Set Cloudflare Credentials`** and that `antimatter.cloudflareHostname` matches the
  Access app hostname.
- Check the public URL with **`Antimatter: Show Connection Status`**.

## Usage

### Remote terminal asks for a fingerprint
That's expected — `EXECUTE_COMMAND` is gated behind a biometric (fingerprint/face) lock on the
phone for safety. Enroll a biometric on the device to use the remote terminal.

### No agent activity shows up
The bridge tails the agent's `transcript.jsonl` under the AntiGravity `brain/` directory. Make sure
an agent conversation is actually running in the IDE; the bridge follows the most recently modified
conversation.

## FAQ

**Is Antimatter affiliated with Google?**
No. Antimatter is an unofficial, community‑driven, open‑source project and is **not** affiliated
with Google or the official AntiGravity IDE project.

**Do I need a domain?**
No. TryCloudflare works with no domain. A domain (Cloudflare Zero Trust) is recommended for the
strongest, double‑layered security.

**Is my connection secure on a public TryCloudflare URL?**
The URL is public, but every connection requires the 256‑bit pairing token and an Ed25519
handshake, so guessing the URL alone is not enough to connect.

**Where are my pairing token and keys stored?**
On the host, in VS Code `SecretStorage` (the 32‑byte pairing token and the persistent Ed25519
keypair). They survive restarts and are not written to plain settings.

**Still stuck?**
Open an issue on [GitHub](https://github.com/saifmukhtar/antimatter/issues). For security
vulnerabilities, follow the [Security Policy](SECURITY.md) instead of filing a public issue.
