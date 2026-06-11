# Security Policy

Operating a remote-control interface for an IDE with terminal access demands enterprise-grade security. The Antimatter project takes the security of your host development environment **extremely seriously**.

!!! danger "Reporting a vulnerability"
    If you discover a security vulnerability, please do **NOT** open a public issue. Instead, use [GitHub's private vulnerability reporting](https://github.com/saifmukhtar/antimatter/security/advisories/new) or email the maintainers directly.

---

## :material-check-decagram: Supported Versions

| Version | Supported |
|---------|-----------|
| `main` branch | :material-check: |
| Latest GitHub Release | :material-check: |
| Older releases | :material-close: |

---

## :material-shield-check: Security Mechanisms

Because Antimatter exposes a local WebSocket server that can proxy terminal commands, we implement **multiple overlapping security layers** so that compromising any single layer is not sufficient for an attacker to gain access.

### :material-numeric-1-circle: 256-bit Bearer Token + Ed25519 Handshake

<div class="step-card" markdown>

**Token generation:** On first run, the extension generates a 256-bit Bearer Token with `crypto.randomBytes(32)` — equivalent entropy to AES-256. It's stored securely in VS Code `SecretStorage` (OS keychain: Keychain on macOS, Credential Manager on Windows, `libsecret` on Linux) and **persists across IDE restarts, reloads, and even uninstall/reinstall cycles**.

**Token verification:** Every WebSocket connection must present this token. The server checks it with `crypto.timingSafeEqual` — immune to timing side-channel attacks. Invalid tokens → close code `4001 Unauthorized`.

**Ed25519 handshake:** After the token check, the client sends an `AUTH_CHALLENGE` nonce. The bridge signs it with its persistent Ed25519 private key and returns `AUTH_RESPONSE`. The client verifies the signature against the public key received during QR pairing — this proves the bridge's identity and prevents Man-in-the-Middle attacks.

</div>

!!! info "Full details"
    See the [WebSocket Protocol Reference](PROTOCOL.md) for the complete handshake flow, message fields, and close codes.

### :material-numeric-2-circle: Biometric Lock (Physical Security)

<div class="step-card" markdown>

The Android app gates sensitive features — particularly the **Remote Terminal** — behind Android's `androidx.biometric` API. The terminal proxy **only** opens after successful fingerprint or face unlock.

Even if your phone is left unlocked on a desk, an unauthorized person cannot execute host commands without passing the biometric check.

</div>

### :material-numeric-3-circle: Origin Header Validation (CSWSH Protection)

<div class="step-card" markdown>

To protect against **Cross-Site WebSocket Hijacking (CSWSH)**, the bridge enforces strict `Origin` header validation. Only these origins are accepted:

- `vscode-webview://…` (the extension's own webview)
- `https://<team>.cloudflareaccess.com` (Cloudflare Access)

Malicious websites in your browser **cannot** silently connect to `ws://localhost:8765`.

</div>

### :material-numeric-4-circle: Path Normalization & Sandboxing

<div class="step-card" markdown>

The app can request file tree data and file contents. To prevent **Local File Arbitrary Read** vulnerabilities (e.g. `../../../../etc/passwd`), the extension strictly sanitizes and normalizes all incoming file paths. Reads are sandboxed to:

- The active VS Code workspace
- The `.gemini/antigravity-ide` directory

Path traversal attempts are rejected before reaching the filesystem.

</div>

### :material-numeric-5-circle: Rate Limiting (DoS Mitigation) — Planned

<div class="step-card" markdown>

!!! info "Status: Planned for future release"
    Rate limiting is not yet implemented but is planned as a future hardening feature.

The extension will implement **per-IP rate limiting** to prevent connection-flood attacks:

- **5 failed token attempts** → IP banned for **60 seconds**
- Prevents connection-flood attacks that could exhaust host memory and crash the IDE

</div>

### :material-numeric-6-circle: Secure Tunnels (Cloudflare)

<div class="step-card" markdown>

We actively discourage unencrypted public tunnels. Antimatter natively supports:

- **Cloudflare Quick Tunnels** — free, auto-provisioned, TLS-encrypted
- **Cloudflare Zero Trust** — persistent hostname, OAuth/SAML access policies, service auth

The WebSocket server binds exclusively to `127.0.0.1` — it is **never** directly accessible from the network. Only Cloudflare's tunnel connector can reach it.

</div>

---

## :material-layers-triple: Defense-in-Depth Summary

| Layer | Protects against | Mechanism |
|-------|-----------------|-----------|
| TLS (Cloudflare) | Network eavesdropping | End-to-end encryption between app ↔ Cloudflare edge |
| Bearer token | Unauthorized connections | 256-bit random token, timing-safe comparison |
| Ed25519 handshake | MITM / server spoofing | Cryptographic identity proof |
| Origin validation | CSWSH attacks | Strict allow-list of Origins |
| Biometric lock | Physical device theft | Fingerprint/face required for terminal |
| Path sandboxing | Arbitrary file read | Normalize + restrict to workspace |
| Localhost binding | LAN snooping | Server only on `127.0.0.1` |

---

## :material-arrow-right-bold: Related

- [**Zero Trust Guide**](ZERO_TRUST.md) — setting up Cloudflare Access for double-layered security
- [**WebSocket Protocol**](PROTOCOL.md) — full auth flow, close codes, and message contract
