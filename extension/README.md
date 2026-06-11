# Antimatter Companion (VS Code Extension)

<p align="center">
  <img src="https://raw.githubusercontent.com/saifmukhtar/antimatter/main/extension/icon.png" width="128" alt="Antimatter Logo">
</p>

**Antimatter** is an ecosystem that synchronizes your live **Google AntiGravity IDE** session with a companion mobile app.

*Note: This is an unofficial, open-source tool and is not affiliated with Google or the official AntiGravity IDE project.*

## What this Extension Does
This extension provides a secure local synchronization server. It reads the local output of your active AntiGravity agent and synchronizes the trajectory (thoughts, tool calls, and outputs) to your mobile device dashboard. It also allows you to seamlessly send chat messages from your mobile device directly into your IDE.

## Features
- **Mobile Terminal UI**: Securely interact with your workspace terminal directly from the mobile app.
- **Real-Time Agent Mirroring**: See what your AI is doing on your phone dashboard.
- **Remote Control**: Send chat messages directly to your agent from your phone.
- **Diff Accept/Reject**: Review file edits directly from your phone and accept/reject them.
- **Enterprise-Grade Encryption**: All connections require a secure pairing code and cryptographic validation.
- **Secure Remote Access**: Natively supports authenticated remote synchronization.

## How to Connect
1. Ensure your AntiGravity IDE host is running Node.js 22+.
2. Install this `.vsix` extension in your AntiGravity IDE.
3. Open the VS Code Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`) and type: `Antimatter: Show Pairing QR Code`.
4. Open the **Antimatter App** on your Android device and tap the QR Scanner.
5. Scan the code on your screen to securely pair the devices.

## Configuration Settings
You can customize the synchronization by going to VS Code Settings and searching for `Antimatter`:

| Setting ID | Description | Default |
|---|---|---|
| `antimatter.autoStart` | Automatically start the synchronization server when Antigravity opens | `true` |
| `antimatter.port` | Local network port for the Antimatter synchronization server | `8765` |
| `antimatter.cloudflareHostname` | Designated secure hostname for remote synchronization | `""` |

## Commands
You can trigger these via the Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`):

| Command ID | Title |
|---|---|
| `antimatter.showPairingQR` | **Antimatter: Show Pairing QR** (Use this to connect the app!) |
| `antimatter.setCloudflareCredentials` | Antimatter: Set Remote Connection Credentials |
| `antimatter.startBridge` | Antimatter: Start Synchronization Server |
| `antimatter.stopBridge` | Antimatter: Stop Synchronization Server |
| `antimatter.showStatus` | Antimatter: Show Connection Status |

---
**Repository**: [github.com/saifmukhtar/antimatter](https://github.com/saifmukhtar/antimatter)
