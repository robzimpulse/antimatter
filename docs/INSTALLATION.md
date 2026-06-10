# Installation & Setup

This guide walks you end‑to‑end from a fresh machine to a paired phone. You do **not** need to
compile anything to use Antimatter — pre‑built releases are provided.

!!! note "Prerequisites"
    - **Google AntiGravity IDE** running on your host machine
    - **Node.js 22+** on the host (required by the bridge server)
    - An **Android device** (or emulator) to install the companion app

## Step 1 — Install the VS Code / AntiGravity extension

1. Download the latest `.vsix` from the [GitHub Releases](https://github.com/saifmukhtar/antimatter/releases) page.
2. In AntiGravity, open the **Extensions** panel → `...` menu → **Install from VSIX…**, and select
   the downloaded file.
3. The bridge starts automatically on startup (controlled by `antimatter.autoStart`).

## Step 2 — Install the Android app

1. Download the latest `.apk` from [GitHub Releases](https://github.com/saifmukhtar/antimatter/releases),
   **or** get it on [F‑Droid](https://f-droid.org/packages/dev.saifmukhtar.antimatter/).
2. Install it on your device (you may need to allow installs from unknown sources for the APK).

## Step 3 — Set up the tunnel

Antimatter bridges your desktop and phone securely without opening firewall ports. Pick one:

=== "TryCloudflare (no domain)"
    The extension automatically spawns a free Cloudflare Quick Tunnel and secures it with a
    256‑bit pairing token — no configuration needed. If you prefer to run it yourself:

    ```bash
    cloudflared tunnel --url localhost:8080
    ```

    Cloudflare returns a temporary URL like `wss://funny-words.trycloudflare.com`.

    !!! warning
        TryCloudflare URLs are public, but the 256‑bit **pairing token** mathematically blocks
        anyone who guesses your URL from connecting.

=== "Cloudflare Zero Trust (domain — recommended)"
    For double‑layered security if you own a domain:

    1. Point a Cloudflare Zero Trust tunnel (e.g. `ide.yourdomain.com`) to `localhost:8080`.
    2. Protect it with a Cloudflare Access App and generate a **Service Auth Client ID + Secret**.
    3. In the Android app, tap **Advanced Options** and enter your Client ID and Secret alongside
       the URL.

    See the full [Zero Trust Guide](ZERO_TRUST.md) for UI and CLI walkthroughs.

## Step 4 — Pair your phone

1. In AntiGravity, open the Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`) and run
   **`Antimatter: Show Pairing QR Code`**.
2. Open the Antimatter app and tap the **QR Scanner**.
3. Scan the code. The QR transfers the WebSocket URL, the 256‑bit pairing token, and the bridge's
   Ed25519 public key — your phone is now securely paired.

## Verify the connection

- Run **`Antimatter: Show Connection Status`** in AntiGravity to confirm the bridge is running.
- On the phone, you should see the live agent trajectory stream in as your agent works.

Having trouble? See [Troubleshooting & FAQ](TROUBLESHOOTING.md).
