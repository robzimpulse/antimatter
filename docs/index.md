---
hide:
  - navigation
  - toc
---

<div class="hero" markdown>

# Antimatter

<p class="hero-subtitle">
The open-source bridge that connects your phone to the <strong>Google AntiGravity IDE</strong>. Monitor your AI agent, send prompts, execute commands, and browse files — all from your pocket.
</p>

<div class="badge-row" markdown>

[![F-Droid](https://img.shields.io/badge/F--Droid-Get_it_on-blue.svg?style=flat-square)](https://f-droid.org/packages/dev.saifmukhtar.antimatter/)
[![GitHub](https://img.shields.io/badge/GitHub-Source-181717.svg?style=flat-square&logo=github)](https://github.com/saifmukhtar/antimatter)
[![Docs](https://img.shields.io/badge/Docs-Website-673ab7.svg?style=flat-square)](https://antimatter.saifmukhtar.dev)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)](https://github.com/saifmukhtar/antimatter/blob/main/LICENSE)

</div>

<div class="hero-buttons" markdown>

[Get Started :material-rocket-launch:](INSTALLATION.md){ .md-button .md-button--primary }
[Download :material-download:](https://github.com/saifmukhtar/antimatter/releases){ .md-button }
[API Reference :material-api:](PROTOCOL.md){ .md-button }

</div>

</div>

!!! warning "Community Project Disclaimer"
    Antimatter is an unofficial, community-driven, open-source project. It is **NOT** an official product of Google, nor is it officially affiliated with the Google AntiGravity IDE project.

---

## :material-star-shooting: Why Antimatter?

Developing with autonomous AI agents often means leaving them running for long periods. Antimatter ensures you aren't chained to your desk — monitor, control, and interact with your agent from anywhere using your phone, secured by **enterprise-grade cryptography**.

<div class="grid cards" markdown>

-   :material-console-line:{ .lg .middle } **Remote Terminal**

    ---

    Execute shell commands on your host PC, secured by a biometric fingerprint/face lock.

-   :material-broadcast:{ .lg .middle } **Real-Time Streaming**

    ---

    Watch your agent's thought process, tool calls, and file edits as they happen.

-   :material-shield-lock:{ .lg .middle } **Zero Trust Security**

    ---

    256-bit pairing tokens + Ed25519 handshakes + Cloudflare tunnels. No open ports.

-   :material-cellphone-link:{ .lg .middle } **QR Pairing**

    ---

    One scan transfers the WebSocket URL, token, and public key. Paired in seconds.

-   :material-folder-eye:{ .lg .middle } **Workspace Browser**

    ---

    Browse files in your IDE workspace and view contents remotely from your phone.

-   :material-message-text:{ .lg .middle } **Remote Prompting**

    ---

    Send messages directly to your AI agent and start new conversations from your phone.

</div>

---

## :material-camera: Screenshots

<div class="screenshot-gallery" markdown>

![Login Screen](images/login.png){ loading=lazy }
![Chat Screen](images/chats.png){ loading=lazy }
![Workspace Browser](images/workspace.png){ loading=lazy }
![File Viewer](images/file-viewer.png){ loading=lazy }
![Remote Terminal](images/terminal.png){ loading=lazy }
![Artifacts](images/artifact.png){ loading=lazy }

</div>

---

## :material-map-marker-path: Quick Navigation

<div class="grid cards" markdown>

-   :material-download-circle:{ .lg .middle } **Getting Started**

    ---

    Download, install, set up the tunnel, and pair your phone in minutes.

    [:octicons-arrow-right-24: Installation & Setup](INSTALLATION.md)

-   :material-puzzle:{ .lg .middle } **Features**

    ---

    Explore every capability: chat, terminal, file browsing, diff review, and more.

    [:octicons-arrow-right-24: Feature Breakdown](FEATURES.md)

-   :material-cog:{ .lg .middle } **Architecture**

    ---

    Learn how Antimatter reverse-engineers the IDE without official APIs.

    [:octicons-arrow-right-24: Deep Dive](ARCHITECTURE.md)

-   :material-api:{ .lg .middle } **API Reference**

    ---

    The complete WebSocket protocol: every message, auth flow, and data structure.

    [:octicons-arrow-right-24: Protocol Reference](PROTOCOL.md)

-   :material-shield-check:{ .lg .middle } **Security**

    ---

    Zero Trust tunnels, Ed25519 handshakes, biometric locks, and more.

    [:octicons-arrow-right-24: Security & Zero Trust](ZERO_TRUST.md)

-   :material-source-pull:{ .lg .middle } **Contributing**

    ---

    Set up the dev environment, run lint/build, preview docs, and submit PRs.

    [:octicons-arrow-right-24: Contributor Guide](CONTRIBUTING.md)

</div>
