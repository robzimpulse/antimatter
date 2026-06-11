# Troubleshooting & FAQ

Common issues when connecting the Antimatter app to the bridge, and how to resolve them. Most
connection failures map to a specific [WebSocket close code](PROTOCOL.md#websocket-close-codes).

---

## :material-connection: Connection Issues

### :material-close-circle: Phone can't connect / immediately disconnects

??? failure "Invalid token (close `4001`)"
    The pairing token on the phone doesn't match the bridge. **Fix:** re-pair by running `Antimatter: Show Pairing QR Code` in the Command Palette and scanning again.

??? failure "Rate limited (close `4000`)"
    After 5 failed token attempts, your IP is banned for 60 seconds. **Fix:** wait a minute, then re-scan the QR code with a fresh pairing.

??? failure "Forbidden origin (HTTP 403)"
    The bridge only accepts `vscode-webview://` and `*.cloudflareaccess.com` origins. **Fix:** make sure you're connecting through the Cloudflare tunnel URL, not directly to a raw IP/port.

### :material-server-off: "Bridge not running"

1. Run **`Antimatter: Start Bridge Server`** from the Command Palette.
2. Confirm `antimatter.autoStart` is enabled in Settings.
3. Verify the host has **Node.js 22+** installed (`node --version`).

### :material-lan-disconnect: Port already in use

Another process may hold the default port. Change **`antimatter.port`** (default `8765`) in VS Code Settings, then restart the bridge.

```bash
# Check what's using the port
lsof -i :8765
```

### :material-cloud-off-outline: Tunnel / Cloudflare problems

- Run **`Antimatter: Restart Cloudflare Tunnel`** to respawn `cloudflared`.
- For Zero Trust setups, verify your **Client ID / Secret** via **`Antimatter: Set Cloudflare Credentials`**.
- Check that `antimatter.cloudflareHostname` matches your Cloudflare Access app hostname.
- Run **`Antimatter: Show Connection Status`** to see the current public URL.

!!! tip "Quick diagnostic"
    The extension output panel (`Output → Antimatter`) shows connection logs, token verification results, and tunnel status in real-time.

---

## :material-help-circle: Usage Questions

### :material-fingerprint: Remote terminal asks for a fingerprint

That's expected — `EXECUTE_COMMAND` is gated behind a biometric (fingerprint/face) lock for safety. Enroll a biometric on the device to use the remote terminal.

### :material-eye-off: No agent activity shows up

The bridge tails `transcript.jsonl` under the AntiGravity `brain/` directory. Make sure:

- An agent conversation is **actually running** in the IDE.
- The bridge is following the correct conversation (it picks the most recently modified one).
- Check the extension output panel for `BrainWatcher` logs.

### :material-refresh: QR code expired

QR codes embed the current tunnel URL. If the tunnel restarted (URL changed), generate a new QR: **`Antimatter: Show Pairing QR Code`**.

---

## :material-frequently-asked-questions: FAQ

??? question "Is Antimatter affiliated with Google?"
    No. Antimatter is an unofficial, community-driven, open-source project and is **not** affiliated with Google or the official AntiGravity IDE project.

??? question "Do I need a domain?"
    No. TryCloudflare works with no domain and zero configuration. A domain (Cloudflare Zero Trust) is recommended for the strongest, double-layered security. See the [Zero Trust Guide](ZERO_TRUST.md).

??? question "Is my connection secure on a public TryCloudflare URL?"
    The URL is publicly reachable, but every connection requires the **256-bit pairing token** and an **Ed25519 handshake**. Guessing the URL alone is not enough to connect — it's mathematically infeasible to brute-force the token.

??? question "Where are my pairing token and keys stored?"
    On the host, in VS Code `SecretStorage` (backed by your OS keychain). The 32-byte pairing token and the persistent Ed25519 keypair survive restarts and are **never** written to plain settings files.

??? question "Can I use Antimatter with multiple devices?"
    Currently, the bridge supports one connected client at a time. Multiple-device support is not yet implemented.

??? question "What data does Antimatter collect?"
    None. Antimatter is fully local + tunnel. No telemetry, no analytics, no cloud services beyond the Cloudflare tunnel. All data stays between your machine and your phone.

---

## :material-lifebuoy: Still Stuck?

Open an issue on [**GitHub**](https://github.com/saifmukhtar/antimatter/issues). For security
vulnerabilities, follow the [**Security Policy**](SECURITY.md) instead of filing a public issue.
