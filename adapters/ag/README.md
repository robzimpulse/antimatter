# Antimatter

Unleash the power of AI coding on the go. Antimatter seamlessly syncs your live VS Code workspace with your Android device in real-time.

## Features

- **Live Chat Sync:** Pick up right where you left off. Continue your AI agent conversation seamlessly on your phone.
- **Artifact Viewing:** Review complex markdown artifacts, code diffs, and generated files natively on your device.
- **End-to-End Encryption:** Your workspace code and agent history are synced over a secure, E2EE WebSocket connection directly to your phone. No middlemen.
- **Image Uploads:** Upload images from your phone directly into the agent's context in VS Code.

## Getting Started

1. Open VS Code and ensure the Antimatter extension is enabled.
2. The Antimatter Bridge will automatically start. You'll see an `[Antimatter]` badge in the status bar indicating the bridge is ready.
3. Click the `[Antimatter]` badge or run the `Antimatter: Show Pairing QR` command from the Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`).
4. Open the Antimatter app on your Android device and tap **Pair with IDE**.
5. Scan the QR code displayed in VS Code.
6. You're connected! 

## Troubleshooting

- **"Connection Refused" / "Gateway Offline":** Ensure that you are connected to the internet and the central gateway is running.
- **"Agent Offline":** The VS Code extension may have been paused or crashed. Reload your VS Code window to restart the bridge.
- **Offline Mode:** The Android app caches conversations. You can view past messages and artifacts even when disconnected from VS Code!

## Requirements

- VS Code 1.80.0 or higher.
- An active internet connection for the initial pairing.
- The Antimatter Android App installed on your device.
