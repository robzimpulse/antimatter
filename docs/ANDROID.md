# Android App Reference

The client half of Antimatter is a native **Android** app built with **Jetpack Compose**,
**Hilt** (dependency injection), **Room** (local persistence), and **Gson** (JSON). It connects to
the bridge over WebSocket, renders the live agent trajectory, and sends control messages back.

- Source: [`android/`](https://github.com/saifmukhtar/antimatter/tree/main/android)
- Package: `dev.saifmukhtar.antimatter`
- Multi‑module Gradle project (`settings.gradle.kts`)

## Module graph

```text
:app                     # MainActivity, Application, navigation host
├── :core:network        # WebSocket client, foreground service, protocol model
├── :core:data           # Room database, DAOs, entities, preferences
├── :core:ui             # Compose theme, Markdown renderer, shared UI utils
├── :feature:connect     # QR scan + pairing + connection state
├── :feature:chat        # Trajectory/chat UI + prompting
├── :feature:files       # Workspace browser + file viewer
└── :feature:terminal    # Remote terminal UI
```

`:app` depends on the feature modules; feature modules depend on the `core` modules.

## `:app`
| File | Responsibility |
|------|----------------|
| `AntimatterApp.kt` | `@HiltAndroidApp` Application; app‑wide setup. |
| `MainActivity.kt` | Single‑activity host that mounts the Compose navigation graph. |
| `navigation/AntimatterNavigation.kt` | Declares routes between connect / chat / files / terminal screens. |
| `utils/LocalCrashHandler.kt` | Captures uncaught exceptions for local crash reporting. |

## `:core:network`
| File | Responsibility |
|------|----------------|
| `BridgeWebSocket.kt` | The WebSocket client: connects with the Bearer token, performs the Ed25519 `AUTH_CHALLENGE`/`AUTH_RESPONSE` handshake, and exposes inbound messages as a flow. |
| `BridgeService.kt` | A foreground `Service` that keeps the socket alive in the background and surfaces system alerts as notifications. |
| `BridgeMessage.kt` | Kotlin model of the wire protocol: `TrajectoryStep`, the `StepCase` enum, and inbound/outbound message types. |
| `NetworkModule.kt` | Hilt module providing the WebSocket/network singletons. |

See the [WebSocket Protocol](PROTOCOL.md) page for the full message contract shared with the
extension.

## `:core:data`
| File | Responsibility |
|------|----------------|
| `AppDatabase.kt` | Room database definition. |
| `AppDao.kt` | Queries for conversations, steps, and artifacts. |
| `ConversationEntity.kt` / `StepEntity.kt` / `ArtifactEntity.kt` | Room entities mirroring server payloads for offline history. |
| `UserPreferencesRepository.kt` | DataStore‑backed user preferences. |
| `GzipUtils.kt` | Compression helpers for stored payloads. |
| `DatabaseModule.kt` | Hilt module providing the database/DAO singletons. |

## `:core:ui`
| File | Responsibility |
|------|----------------|
| `theme/Theme.kt`, `theme/Color.kt` | Material 3 theme (deep purple / blue palette). |
| `MarkdownText.kt` | Renders AI responses as Markdown. |
| `utils/GrammarLocator.kt` | Syntax‑highlighting grammar lookup for code blocks. |

## Feature modules
Each feature follows a **Screen + ViewModel** (MVVM) pattern with Compose:

| Module | Screens | ViewModel |
|--------|---------|-----------|
| `:feature:connect` | `ConnectScreen`, `QRScannerScreen` | `ConnectionViewModel` |
| `:feature:chat` | `ChatScreen`, `ChatBubble`, `ThinkingBubble`, `ToolCallCard`, `MessageInput`, `TypingIndicator` | `ChatViewModel` |
| `:feature:files` | `FilesScreen`, `FileViewScreen` | `FilesViewModel` |
| `:feature:terminal` | `TerminalScreen` | `TerminalViewModel` |

- **connect** — scans the pairing QR, stores the URL + token + bridge public key, and tracks
  connection status.
- **chat** — subscribes to a conversation and renders each `TrajectoryStep` according to its
  `StepCase` (text, tool calls, run‑command, approvals, …), and sends prompts / edit decisions.
- **files** — browses the workspace `FILE_TREE` and opens file contents via `READ_FILE`.
- **terminal** — runs `EXECUTE_COMMAND`, gated behind a biometric (fingerprint/face) lock, and
  streams `COMMAND_OUTPUT`.

## Build

| Task | Command |
|------|---------|
| Lint | `./gradlew lintDebug` |
| Build debug APK | `./gradlew assembleDebug` |
| Install on device/emulator | `./gradlew installDebug` |

Open the `android/` directory in Android Studio (Koala or newer) and let Gradle sync. Crashlytics
in debug builds requires a valid `android/app/google-services.json` (optional).
