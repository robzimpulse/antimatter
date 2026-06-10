# Zero Trust Security Guide

Antimatter securely connects your mobile device to your local machine **without opening any firewall ports** or exposing your local IP address. It achieves this using [**Cloudflare Zero Trust**](https://developers.cloudflare.com/cloudflare-one/) (via `cloudflared`).

!!! abstract "Two methods"
    - **TryCloudflare (free, automatic)** — the extension handles everything. No domain needed.
    - **Cloudflare Zero Trust (recommended)** — persistent hostname + Access policies. Requires a domain.

---

## :material-tunnel: How the Tunnel Works

```text
┌──────────────┐      outbound      ┌──────────────────┐      WSS      ┌──────────────┐
│  VS Code     │ ──────────────────▶│  Cloudflare Edge │◀────────────── │  Android App │
│  Extension   │  cloudflared conn  │  (TLS termination│  Bearer token  │  (Client)    │
│  :8765       │                    │   + routing)     │  + Ed25519     │              │
└──────────────┘                    └──────────────────┘                └──────────────┘
```

1. The extension starts a WebSocket server on `127.0.0.1:8765`.
2. It downloads (if missing) and launches `cloudflared` in the background.
3. `cloudflared` creates an **outbound** connection to Cloudflare's edge — no inbound ports needed.
4. Cloudflare assigns a public URL (e.g. `wss://funny-words.trycloudflare.com`).
5. The Android app connects to this URL; Cloudflare routes traffic back through the tunnel.

---

## :material-shield-half-full: Double-Layered Protection

Even if someone discovers your tunnel URL, they **cannot** connect:

| Layer | Where | What happens |
|-------|-------|-------------|
| **Cloudflare Access** *(optional)* | Edge | Blocked before traffic reaches your machine. Requires OAuth/SAML identity or service auth headers. |
| **256-bit Pairing Token** | Local | Timing-safe comparison. Invalid token → close `4001`. |
| **Ed25519 Handshake** | Local | Bridge signs a client nonce, proving its identity. Prevents MITM even if the tunnel is compromised. |

---

## :material-auto-fix: Automatic Quick Tunnel (TryCloudflare)

This is the default — **zero configuration required**.

When the bridge starts and `antimatter.cloudflareHostname` is blank:

1. The extension downloads `cloudflared` if it's not in `PATH`.
2. Spawns: `cloudflared tunnel --url localhost:8765`
3. Parses the assigned URL from `cloudflared` output.
4. Embeds the URL + pairing token + public key into the QR code.

!!! tip "Nothing to configure"
    Just install the extension, scan the QR, and go.

!!! warning "Ephemeral URL"
    The URL changes every time `cloudflared` restarts. Re-scan the QR code after restarting the bridge or your machine.

---

## :material-shield-lock: Manual Cloudflare Zero Trust Setup

For a **persistent, enterprise-grade** setup with your own domain.

### :material-numeric-1-circle: Install `cloudflared`

Download from the official [Cloudflare downloads page](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/).

=== ":material-linux: Linux"
    ```bash
    curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o cloudflared
    chmod +x cloudflared
    sudo mv cloudflared /usr/local/bin/
    ```

=== ":material-apple: macOS"
    ```bash
    brew install cloudflared
    ```

=== ":material-microsoft-windows: Windows"
    Download the `.msi` from the [releases page](https://github.com/cloudflare/cloudflared/releases) and run the installer.

### :material-numeric-2-circle: Authenticate

```bash
cloudflared tunnel login
```

This opens a browser to authenticate with your Cloudflare account and stores a certificate locally.

### :material-numeric-3-circle: Create a Tunnel

```bash
cloudflared tunnel create antimatter
```

Note the tunnel UUID that's printed — you'll need it for routing.

### :material-numeric-4-circle: Route Your Domain

Point your custom domain (e.g. `ide.yourdomain.com`) to the tunnel:

```bash
cloudflared tunnel route dns antimatter ide.yourdomain.com
```

### :material-numeric-5-circle: Configure `cloudflared`

Create `~/.cloudflared/config.yml`:

```yaml
tunnel: <YOUR_TUNNEL_UUID>
credentials-file: ~/.cloudflared/<YOUR_TUNNEL_UUID>.json

ingress:
  - hostname: ide.yourdomain.com
    service: ws://localhost:8765
  - service: http_status:404
```

Start the tunnel:

```bash
cloudflared tunnel run antimatter
```

### :material-numeric-6-circle: Add Cloudflare Access (Enterprise Security)

For the ultimate setup, protect the route with an **Access Application**:

1. In the [Cloudflare Zero Trust Dashboard](https://one.dash.cloudflare.com/), go to **Access → Applications → Add an application**.
2. Create a **Self-hosted** app matching `ide.yourdomain.com`.
3. Add an **Access Policy** (e.g. allow your email domain, or specific users).
4. Generate a **Service Auth Client ID and Client Secret**.

This creates the double-layered protection:

- **Layer 1 (Edge):** Attackers are blocked at Cloudflare — they lack the Service Auth headers.
- **Layer 2 (Local):** Even if an attacker somehow bypasses the edge, the extension rejects them without the 256-bit token and Ed25519 handshake.

### :material-numeric-7-circle: Configure the Extension

1. Open VS Code Settings and search for **"Antimatter"**.
2. Set **`antimatter.cloudflareHostname`** to your hostname (e.g. `ide.yourdomain.com`).
3. Run **`Antimatter: Set Cloudflare Credentials`** from the Command Palette.
4. Enter your **Client ID** and **Client Secret** (stored securely in your OS keychain).

The extension now uses your persistent tunnel instead of spawning a Quick Tunnel.

### :material-numeric-8-circle: Configure the Android App

1. Open the Antimatter app on your phone.
2. On the Connect screen, tap **Advanced Options**.
3. Enter your custom URL: `wss://ide.yourdomain.com`
4. Enter your **Client ID** and **Client Secret**.
5. Tap **Connect** (or scan the QR code, which now embeds your hostname).

---

## :material-frequently-asked-questions: FAQ

??? question "Can I use a different tunnel provider?"
    Antimatter is designed around Cloudflare. Other providers (ngrok, localtunnel, etc.) may work if they support WebSocket proxying, but they are **not officially supported** and may not provide the same security guarantees.

??? question "Do I need Cloudflare Zero Trust to use Antimatter?"
    No. The free TryCloudflare Quick Tunnel works out of the box with zero configuration. Zero Trust is recommended for persistent setups and teams.

??? question "What if my tunnel URL changes?"
    Quick Tunnel URLs change on restart — re-scan the QR code. Zero Trust tunnels with a custom domain are persistent.

---

## :material-arrow-right-bold: Related

- [**Security Policy**](SECURITY.md) — all security mechanisms in detail
- [**WebSocket Protocol**](PROTOCOL.md) — auth flow, close codes, and full message contract
- [**Installation & Setup**](INSTALLATION.md) — quick-start guide
