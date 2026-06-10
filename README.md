# Antimatter Ecosystem

[![F-Droid](https://img.shields.io/badge/F--Droid-Get_it_on-blue.svg)](https://f-droid.org/packages/dev.saifmukhtar.antimatter/)
[![GitHub Sponsor](https://img.shields.io/badge/Sponsor-❤️-blue.svg)](https://github.com/sponsors/saifmukhtar)
[![Docs](https://img.shields.io/badge/docs-Website-deep_purple.svg)](https://antimatter.saifmukhtar.dev)

> [!WARNING]
> **Community Project Disclaimer**
> Antimatter is an unofficial, community-driven, open-source project. It is **NOT** an official product of Google, nor is it officially affiliated with the Google AntiGravity IDE project.

Antimatter is an open-source bridge ecosystem that connects your mobile device directly to the local **Google AntiGravity IDE** running on your host machine.

By connecting your phone to the IDE, you can view your active AI agent's trajectory, monitor its thought process, read logs in real-time, send new prompts, execute terminal commands, and browse your workspace files—all from your mobile device.

---

## 📖 Official Documentation

**We have a dedicated documentation website!**  
👉 **[Read the Official Antimatter Documentation Here](https://antimatter.saifmukhtar.dev)**

Because this repository contains multiple sub-projects, we have split the source documentation files into the `docs/` folder for clarity:

**Getting Started**
- [**Installation & Setup**](docs/INSTALLATION.md) - End-to-end: install, tunnel, and pair your phone.
- [**Feature Breakdown**](docs/FEATURES.md) - A detailed list of everything Antimatter can do.
- [**Troubleshooting & FAQ**](docs/TROUBLESHOOTING.md) - Fix common connection, tunnel, and pairing issues.

**Architecture & Security**
- [**Architecture Deep Dive**](docs/ARCHITECTURE.md) - Understand how we reverse-engineered the IDE hooks without official APIs.
- [**Zero Trust Guide**](docs/ZERO_TRUST.md) - Learn how to set up Cloudflare Zero Trust (UI & CLI guides).
- [**Security Policy**](docs/SECURITY.md) - Read about our Biometric locks, Cryptographic Handshakes, and protections.

**Reference**
- [**WebSocket Protocol**](docs/PROTOCOL.md) - The complete message contract between the extension and the app.
- [**VS Code Extension Reference**](docs/EXTENSION.md) - Module map, commands, and settings.
- [**Android App Reference**](docs/ANDROID.md) - Module/screen/ViewModel map.

**Project**
- [**Contributing & Development**](docs/CONTRIBUTING.md) - Local setup, lint/build commands, and docs preview.
- [**Roadmap**](docs/ROADMAP.md) - Future plans for E2EE and Terminal isolation.
- [**Changelog**](docs/CHANGELOG.md) - Detailed technical tracking of all project updates.

### Sub-Project Documentation
- [**VS Code Extension README**](extension/README.md)
- [**Android App README**](android/README.md)

---

## 🚀 Quick Start & Download

You do not need to compile the code yourself to use Antimatter. 

1. **Download the Extension**: Go to our [GitHub Releases](https://github.com/saifmukhtar/antimatter/releases) page and download the latest `.vsix` file.
2. **Install in AntiGravity**: Open your AntiGravity IDE, go to the Extensions panel, click the `...` menu, and select **"Install from VSIX..."**.
3. **Download the Android App**: Also on the [GitHub Releases](https://github.com/saifmukhtar/antimatter/releases) page, download the latest `.apk` file and install it on your Android device. 
4. **Setup the Tunnel**: Follow the **Tunnel Setup** section below.
5. **Connect**: Open the VS Code Command Palette (`Ctrl+Shift+P`) and type `Antimatter: Show Pairing QR Code`. Scan this code with the Android app to securely transfer the WebSocket URL and Pairing Token.

### 🌐 Tunnel Setup
Antimatter securely bridges your desktop and phone. You can expose the server securely in two ways:

#### Method 1: TryCloudflare (No Domain Required)
1. Run `cloudflared tunnel --url localhost:8080` on your desktop.
2. Cloudflare will give you a temporary URL (e.g., `wss://funny-words.trycloudflare.com`).
3. Paste this URL into the VS Code extension settings, then scan the generated QR code.
> **Note:** TryCloudflare URLs are public. However, Antimatter generates a 256-bit cryptographic **Pairing Token**. Without this token, unauthorized users who guess your URL are mathematically blocked from connecting.

#### Method 2: Cloudflare Zero Trust (Domain Required - Recommended)
If you own a domain, this provides double-layered security.
1. Point a Cloudflare Zero Trust tunnel (e.g., `ide.yourdomain.com`) to `localhost:8080`.
2. Protect it with a Cloudflare Access App, generating a **Service Auth Client ID and Secret**.
3. In the Android App, tap **Advanced Options** and input your Client ID and Secret alongside your URL.

---

## ✨ Core Features
> See the [**Detailed Features Document**](docs/FEATURES.md) for a full breakdown.

- **Remote Terminal Execution**: Full remote shell execution secured by Biometric Fingerprint locks.
- **Real-Time Streaming**: Watch your agent's thought process character-by-character.
- **Partial Text Selection**: Long-press AI chats or code blocks to trigger native copy/share selection tools.
- **Zero Trust Security**: Cloudflare Tunnel integration + 256-bit Pairing Tokens ensure impenetrable local security.

---

## 📦 Repository Structure

This is a monorepo containing two shippable sub-projects plus the documentation site:

```text
antimatter/
├── extension/   # VS Code / AntiGravity extension (TypeScript) — the bridge server
├── android/     # Companion Android app (Kotlin / Jetpack Compose) — the mobile client
├── docs/        # MkDocs Material documentation (published to antimatter.saifmukhtar.dev)
└── mkdocs.yml   # Documentation site configuration
```

The extension and app communicate over an authenticated WebSocket — see the
[**WebSocket Protocol Reference**](docs/PROTOCOL.md) for the full message contract.

---

## 👥 Contributing & Community

We love contributions! Antimatter is built by developers, for developers.

- **[Contributing Guidelines](CONTRIBUTING.md)**: Read this to learn how to set up the Android and VS Code extension environments locally, run linting, and submit PRs.
- **[Code of Conduct](CODE_OF_CONDUCT.md)**: Please review our community interaction guidelines to ensure a welcoming environment for everyone.
- **[Contributors List](CONTRIBUTORS.md)**: A massive thank you to everyone who has helped build this ecosystem!

---

## 🛠️ Tech Stack & Credits

This project leverages several modern open-source technologies:
- **Android App**: Kotlin, Jetpack Compose, OkHttp (WebSockets), Markwon (Markdown rendering).
- **Barcode Scanning**: Pure-Java `com.google.zxing:core` ensuring 100% FOSS compliance for F-Droid.
- **VS Code Extension**: Node.js, TypeScript, `ws` (WebSocket server), `node-pty` (Planned for terminal).
- **Secure Networking**: Cloudflare Zero Trust (`cloudflared`) and free automatic Quick Tunnels.

## License
MIT License
