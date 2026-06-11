# Installation & Setup

This guide walks you end-to-end — from a fresh machine to a fully paired phone — in about **5-10 minutes** (depending on internet speed and initial downloads). You do **not** need to compile anything; pre-built releases are provided.

---

## :material-clipboard-check: Prerequisites

Before you begin, make sure you have the following:

| Requirement | Version | Purpose |
|-------------|---------|---------|
| **AntiGravity IDE** | Latest | The host IDE your AI agent runs inside |
| **Node.js** | 22+ | Required by the bridge server (the extension) |
| **Android device** | Android 8.0+ | Or an emulator with camera (for QR scanning) |
| **Cloudflare** *(optional)* | `cloudflared` CLI | Only needed for Cloudflare Zero Trust (recommended, not required) |

!!! tip "Don't have Node.js 22+?"
    Install via [nvm](https://github.com/nvm-sh/nvm):
    ```bash
    nvm install 22
    nvm use 22
    ```

---

## :material-numeric-1-circle: Install the VS Code Extension

The Antimatter bridge runs as a VS Code / AntiGravity extension. It starts a local WebSocket server, watches the agent's trajectory logs, and tunnels everything securely to your phone.

1. Go to the [**GitHub Releases**](https://github.com/saifmukhtar/antimatter/releases) page.
2. Download the latest **`.vsix`** file (e.g. `antimatter-1.0.0.vsix`).
3. Open your **AntiGravity IDE** (or VS Code):
    - Open the **Extensions** panel (++ctrl+shift+x++)
    - Click the `···` menu in the top-right corner
    - Select **"Install from VSIX…"**
    - Choose the downloaded `.vsix` file.
4. Reload the window when prompted.

!!! success "Auto-start"
    By default the bridge server starts automatically when AntiGravity opens. You can toggle this via `antimatter.autoStart` in Settings.

### Extension settings at a glance

| Setting | Default | What it does |
|---------|---------|-------------|
| `antimatter.port` | `8765` | The local WebSocket port the bridge binds to |
| `antimatter.autoStart` | `true` | Start the bridge automatically on IDE launch |
| `antimatter.cloudflareHostname` | *(empty)* | Your Zero Trust hostname (leave blank for free Quick Tunnel) |
| `antimatter.cloudflareClientId` | *(empty)* | Cloudflare Access Client ID (Zero Trust only) |

---

## :material-numeric-2-circle: Install the Android App

The companion app connects to the bridge and gives you full control of the agent from your phone.

=== ":material-google-play: GitHub Releases"

    1. Go to [**GitHub Releases**](https://github.com/saifmukhtar/antimatter/releases).
    2. Download the latest **`.apk`** file.
    3. On your Android device, open the APK to install.

    !!! note "Unknown sources"
        You may need to allow installs from unknown sources. Go to **Settings → Security → Install unknown apps** and enable it for your file manager or browser.

=== ":material-store: F-Droid"

    Antimatter is available on [**F-Droid**](https://f-droid.org/packages/dev.saifmukhtar.antimatter/) for 100% FOSS compliance:

    1. Install [F-Droid](https://f-droid.org/) if you haven't.
    2. Search for **"Antimatter"** and install.
    3. F-Droid handles updates automatically.

---

## :material-numeric-3-circle: Set Up the Tunnel

Antimatter bridges your desktop and phone securely without opening any firewall ports. The extension spawns a [Cloudflare tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/) to expose the local WebSocket server over a public `wss://` URL.

!!! info "How it works under the hood"
    1. The extension starts a WebSocket server on `127.0.0.1:8765`.
    2. It spawns `cloudflared` to create an outbound tunnel to Cloudflare's edge.
    3. Cloudflare assigns a secure public URL (e.g. `wss://funny-words.trycloudflare.com`).
    4. Your phone connects to this URL; Cloudflare routes traffic back through the tunnel.

    No inbound ports are opened on your machine at any point.

### Pick your method

=== ":material-cloud-outline: TryCloudflare (no domain required)"

    **The extension does this automatically** — no configuration needed. When the bridge starts, it downloads `cloudflared` (if missing), spawns a free Quick Tunnel, and resolves the public URL for the QR code.

    If you prefer to run it manually:

    ```bash
    cloudflared tunnel --url localhost:8765
    ```

    Cloudflare returns a temporary URL like `wss://funny-words.trycloudflare.com`.

    !!! warning "Public URL — but still secure"
        TryCloudflare URLs are publicly reachable, but **every connection requires the 256-bit pairing token**. Without scanning the QR code, an attacker who guesses your URL is mathematically blocked from connecting. After the token, an **Ed25519 cryptographic handshake** further verifies the bridge's identity.

    **Pros:** Zero config, works immediately.
    **Cons:** URL changes on each restart; no additional auth layer beyond the token.

=== ":material-shield-lock: Cloudflare Zero Trust (domain — recommended)"

    If you own a domain, this provides **double-layered security**: Cloudflare Access auth + the pairing token.

    **Step-by-step:**

    1. **Create a tunnel** in the [Cloudflare Zero Trust Dashboard](https://one.dash.cloudflare.com/):
        - Go to **Networks → Tunnels → Create a tunnel**.
        - Install and run the connector on your host machine.
        - Add a **public hostname** (e.g. `ide.yourdomain.com`) pointing to `localhost:8765`.

    2. **Protect with Access:**
        - Go to **Access → Applications → Add an application**.
        - Create a **Self-hosted** application matching your hostname.
        - Add an Access Policy (e.g. allow your email domain).
        - Generate a **Service Auth Client ID and Secret**.

    3. **Configure the extension:**
        - Set `antimatter.cloudflareHostname` to your hostname (e.g. `ide.yourdomain.com`).
        - Run `Antimatter: Set Cloudflare Credentials` from the Command Palette and enter the Client ID and Secret (stored securely in your OS keychain).

    4. **Configure the Android app:**
        - In the app, tap **Advanced Options** on the connect screen.
        - Enter your **Client ID** and **Client Secret** alongside your URL.

    !!! tip "Full walkthrough"
        See the [**Zero Trust Guide**](ZERO_TRUST.md) for detailed UI and CLI walkthroughs with screenshots.

    **Pros:** Persistent URL, enterprise-grade access control, ideal for teams.
    **Cons:** Requires a domain and Cloudflare account.

---

## :material-numeric-4-circle: Pair Your Phone

This is the moment of truth — connecting the app to the bridge.

1. In AntiGravity, open the **Command Palette** (++ctrl+shift+p++ / ++cmd+shift+p++).
2. Type and select: **`Antimatter: Show Pairing QR Code`**.
3. A QR code appears in a new editor tab. Open the **Antimatter app** on your phone.
4. Tap the **QR Scanner** button and scan the code on your screen.

!!! abstract "What the QR code contains"
    The QR code securely transfers three values:

    - **WebSocket URL** — the public `wss://` address of your tunnel
    - **Pairing Token** — a cryptographically random 256-bit Bearer token
    - **Bridge Public Key** — the Ed25519 public key for the handshake

    These are **never** sent over the network unencrypted — they're transferred optically via the QR code.

---

## :material-check-circle: Verify the Connection

After scanning, the app should connect within a few seconds.

**On the desktop:**

- Run **`Antimatter: Show Connection Status`** from the Command Palette.
- The output panel should show: `Client connected` and `Client authenticated successfully via Ed25519 challenge`.

**On the phone:**

- The app navigates to the **Chat** screen.
- If an agent conversation is active, you should see the live trajectory streaming in.

!!! success "You're all set!"
    Your phone is now securely paired to your IDE. Start an agent task in AntiGravity and watch it appear on your phone in real-time.

---

## :material-frequently-asked-questions: Common Issues

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| Immediate disconnect | Invalid/expired token | Re-scan the QR code |
| `Rate Limited` (code 4000) | 5+ failed auth attempts | Wait 60 seconds, then re-scan |
| `Forbidden Origin` (403) | Direct connection to IP | Connect through the Cloudflare tunnel URL |
| Bridge not running | Extension inactive | Run `Antimatter: Start Bridge Server` |
| Port conflict | Port 8765 in use | Change `antimatter.port` in Settings |

For more, see the full [**Troubleshooting & FAQ**](TROUBLESHOOTING.md) page.
