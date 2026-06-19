# Core Infrastructure Changelog

## [2.0.0] - 2026-06-19
### Added
- Extracted Gateway functionality from monolithic IDE extension into a standalone Python daemon.
- Independent Cloudflare Zero Trust tunnel management.
- OS Keyring support for secure Ed25519 secret storage.
- Local `127.0.0.1:8765` WebSocket IPC router for handling multi-adapter messages.
- Local IPC Token Authentication (`~/.antimatter_daemon/.ipc_token`) to secure adapter connections against rogue local processes.
- Forward Secrecy enforcement: generating ephemeral X25519 keys per session instead of persisting them in the configuration file.

### Fixed
- Replay Attack vulnerability by validating monotonically increasing `msg_id`s in the E2EE decryption layer.
- PTY backpressure issue: Gateway now sends `PTY_OVERFLOW` notifications to the client instead of silently dropping output frames under heavy load.
- Weak headless vault encryption: Increased PBKDF2 iterations from 100,000 to 600,000 (OWASP 2023 standard).
- Removed plaintext logging of IPC command payloads and Ed25519 authentication material.

## [1.0.0] - 2026-06-10
### Added
- Strict Origin Validation against `cloudflareaccess.com` to prevent Cross-Site WebSocket Hijacking.
- Strict Localhost Binding, blocking unauthenticated LAN access.
- Token Authentication (256-bit Bearer Token) with `crypto.timingSafeEqual()`.
- Ed25519 Handshake logic for persistent keypair verification.
- Rate Limiting (per-IP token-bucket) to prevent DoS.
