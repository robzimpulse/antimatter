# Android App Changelog

## [2.0.0] - 2026-06-19
### Added
- Multi-adapter support: UI to select between active integrations (AG, AG2, CC) during the connection phase.
- Thought Process Streaming improvements to correctly index `plannerResponse` and `text` streams.

### Fixed
- History Leakage bug (BUG-015): `ChatViewModel` now properly filters `HISTORY_LIST` by `agentId` to prevent history corruption across adapters.
- Step Crosstalk bug (BUG-018): `STEP` messages are now correctly scoped to the active `agentId` and `conversationId`.

## [1.0.0] - 2026-06-10
### Added
- **Biometric Authentication** — integrated Android `BiometricPrompt` (fingerprint/face) to gate sensitive features.
- **Partial Text Selection** — long-press user/AI chat messages to select specific lines and trigger the native Android copy/share toolbar.
- **Android App Links (HTTPS)** — replaced legacy `antimatter://` deep links with verified HTTPS App Links to prevent intent hijacking.
- **SQLCipher Data-at-Rest Encryption** — all chat histories and trajectory data encrypted at rest with a 256-bit key from the Android Keystore.
- **Secure QR Pairing** — one-scan transfer of WebSocket URL, Bearer Token, and Ed25519 public key.
- **ZXing Core Migration** — replaced `com.google.mlkit:barcode-scanning` with pure-Java `com.google.zxing:core` for F-Droid FOSS compliance.

### Changed
- UI/UX Polish: Fixed keyboard padding overlaps and double-inset spacing in the Compose `Scaffold` hierarchy.
