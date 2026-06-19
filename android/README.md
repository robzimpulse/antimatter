# Antimatter Companion App (Android)

<p align="center">
  <img src="https://raw.githubusercontent.com/saifmukhtar/antimatter/main/extension/icon.png" width="128" alt="Antimatter Logo">
</p>

**Antimatter** is the companion mobile app for your live **Google AntiGravity IDE** session. It securely connects to the Antimatter Bridge extension running on your host machine, letting you manage your AI agent from anywhere.

*Note: This is an unofficial, open-source tool and is not affiliated with Google or the official AntiGravity IDE project.*

## What this App Does
This Android app connects via WebSocket to the Antimatter Bridge server on your host machine. It receives a live trajectory of your AntiGravity agent (including thoughts, tool calls, and outputs) and allows you to remotely control the agent from your phone. 

### Screenshots
<p align="center">
  <img src="../docs/images/login.png" width="200" alt="Login Screen">
  <img src="../docs/images/chats.png" width="200" alt="Chat Screen">
  <img src="../docs/images/workspace.png" width="200" alt="Workspace Browser">
</p>
<p align="center">
  <img src="../docs/images/file-viewer.png" width="200" alt="File Viewer">

  <img src="../docs/images/artifact.png" width="200" alt="Artifacts UI">
</p>

## Features

- **Real-Time Agent Mirroring**: Watch your agent's thought process, tool executions, and file edits in real-time as they happen in your IDE.
- **Remote Control**: Send chat messages to your agent without being at your computer.
- **Partial Text Selection**: Long-press messages to select specific text and use native Android copy/share options.
- **Review Edits**: Accept or reject code changes diffs directly from your phone.
- **Instant Pairing**: Just scan the QR code in VS Code to establish a secure WebSocket connection.
- **Zero Trust Security**: Built-in support for Cloudflare Zero Trust and Quick Tunnels. All connections are secured with a cryptographically generated 256-bit token and Ed25519 handshakes.

## How to Connect
1. Ensure the **Antimatter Bridge** extension is installed and running in your AntiGravity IDE.
2. In VS Code, open the Command Palette and select `Antimatter: Show Pairing QR Code`.
3. Open this app on your Android device and tap **Scan Pairing QR**.
4. Scan the code. The app will automatically securely connect to your machine!

## Build Instructions
To build the app locally from source:
```bash
./gradlew assembleDebug
```

### Dependency Note (Biometric)
You may notice the app uses `androidx.biometric:biometric:1.2.0-alpha05`. While normally `alpha` indicates unstable software, this specific version is considered the industry standard for production apps needing proper Device Credential (PIN/Pattern) fallback on Android 11+ (API 30+). The stable `1.1.0` release has known bugs with these modern APIs, so this alpha version is intentionally selected for maximum stability.

---
**Repository**: [github.com/saifmukhtar/antimatter](https://github.com/saifmukhtar/antimatter)
