# Antimatter Testing Status & Known Issues

This document tracks the current testing status of the Antimatter ecosystem, outlining known bugs, platform limitations, and areas requiring further optimization.

## Testing Environment

- **Platform Tested**: Android App **ONLY**
- **Note**: The iOS app remains completely untested at this time due to the non-availability of an iOS testing device.

---

## Feature Status

### 1. Gateway & Connection

- **Status**: Tested
- **Functionality**: The persistent WebSocket connection between the local gateway and the Android app establishes successfully.
  - The Gateway double-forks into a silent background daemon successfully.
  - IPC token and PID files correctly persist to `~/.antimatter_daemon/`.
  - Log rotation (`gateway.log`) correctly limits file size growth.
- **🚨 Known Issues**:
  - The connection drops abruptly when the Android app is sent to the background. Background service persistence needs to be implemented.

### 2. Workspace Browser

- **Status**: Tested
- **Functionality**: Basic directory parsing and file viewing work as expected.
- **⚠️ Needed Improvements**:
  - **Multi-Workspace Selection**: Currently lacking support for seamlessly switching between multiple active workspaces.
  - **Comprehensive File Support**: Needs proper UI support for viewing all file types robustly within the Android app.

### 3. Native PTY Terminal

- **Status**: Tested
- **Functionality**: Core terminal functioning (shell execution, basic I/O) is stable.
- **⚠️ Needed Improvements**:
  - Requires significant performance optimization.
  - Proper UI/UX support and polishing are needed to bring it up to standard.

### 4. Chats Ai Agents (ag)

- **Status**: Stable & Ready for Release
- **Functionality**: The `ag` adapter is fully compatible and stable with Antimatter. The VS Code extension (Antimatter Adapter) has been polished, stripped of unnecessary dependencies, and packaged as a clean VSIX ready for publication on the Open VSX Registry.
- **Need Improvement**: Stabilizing the Tool calls, adding Accept, edit and reject Features.

---

## Active Bug Tracking

### BUG-009 — Offline cache gets wiped on reconnect due to async race condition

- **Severity**: P1 High  
- **Status**: 🟢 FIXED  
- **Reported**: 2026-06-18  
- **Symptom**: When connecting the Android app, the locally cached messages suddenly disappear, showing only the last message.  
- **Root Cause**: In `BrainWatcher.ts`, `processFile` was made async but not awaited before broadcasting `SESSION_STATE`. The adapter falsely broadcasted `stepCount = 0`, causing the Android app to aggressively delete its local cache.  
- **Fix**: Added `await` to `processFile` during initialization to ensure the true step count is broadcasted, preserving the local DB cache.

---

### BUG-010 — Multimodal image prompts dropping silently

- **Severity**: P2 Medium  
- **Status**: 🟢 FIXED  
- **Reported**: 2026-06-18  
- **Symptom**: Sending an image attachment from the Android app caused the Gateway to receive a massive base64 string, but it didn't render correctly on the IDE agent.  
- **Root Cause**: Base64 data was passed as a raw string array without converting it into a proper file that the agent could read.  
- **Fix**: Added logic in `ChatCommandHandler.ts` to decode the base64 images, save them natively as `.jpg` files in the agent's `scratch/` directory, and rewrite the prompt to use standard markdown `![Image](file://...)` syntax so the AI agent can properly "see" them.

---

### BUG-001 — File open spins forever (no file content received)

- **Severity**: P1 High  
- **Status**: 🟢 FIXED  
- **Reported**: 2026-06-18  
- **Symptom**: Tapping any file in the workspace browser shows a circular progress indicator that never resolves. The file content screen stays blank.  
- **Root Cause**: `READ_FILE` and `WRITE_FILE` commands were not handled as internal gateway commands. They fell through to the adapter-routing block in `router.py` which requires an `agentId`. Since `FilesViewModel.openFile()` sends `ReadFile(path)` with no `agentId`, the gateway logged `[WARNING] No agentId specified in command: READ_FILE` and silently dropped the command. The Android client was left waiting for a `FILE_CONTENT` message that would never arrive.  
- **Fix**:
  - `core/gateway/src/antimatter_gateway/router.py`: Added native `READ_FILE` and `WRITE_FILE` handlers before the adapter-routing fallthrough. Files are read/written against `self.current_workspace`.
  - `core/gateway/pyproject.toml`: Added `aiofiles>=23.0.0` dependency (required for async file I/O in the gateway).
  - Added path-traversal guard (`_resolve_path`) that rejects any path that escapes `current_workspace`.
- **Reproduce**: Open workspace browser → tap any file.

---

### BUG-002 — Workspace tied to AI agent (files unavailable without agent)

- **Severity**: P1 High  
- **Status**: 🟢 FIXED  
- **Reported**: 2026-06-18  
- **Symptom**: File browsing and file read/write only worked (partially) when an AI agent/adapter was connected. When no agent was online, `GET_FILES` fell back to `"."` (the gateway process CWD), and `current_workspace` was never initialized from the configured `allowed_workspaces`. The workspace browser was effectively broken without an active AI session.  
- **Root Cause**:  
  - `MessageRouter.__init__` set no initial `current_workspace`.  
  - `GET_FILES` tried to use `adapter["workspace_root"]` when an agent was present, mixing file browsing state with AI agent state.  
  - `FilesViewModel` on Android derived `currentWorkspace` from `message.agents.firstOrNull()?.workspaceRoot` — meaning workspace was lost the moment the agent disconnected.  
- **Fix**:
  - `core/gateway/src/antimatter_gateway/router.py`:
    - `MessageRouter.__init__` now initialises `self.current_workspace` from `config.allowed_workspaces[0]`, falling back to `Path.cwd()`.
    - `GET_FILES`, `READ_FILE`, `WRITE_FILE` always use `self.current_workspace` — no agent lookup.
    - `broadcast_system_state` now includes `"current_workspace": self.current_workspace` so the app always receives the gateway's active workspace.
    - `FILE_TREE` response now includes `"workspace"` field.
    - `CHANGE_WORKSPACE` only modifies `self.current_workspace`, never the adapter dict.
  - `android/core/network/.../BridgeMessage.kt`:
    - `AvailableAgents` data class gains `@SerializedName("current_workspace") val currentWorkspace: String`.
    - `FileTree` data class gains `val workspace: String`.
  - `android/feature/files/.../FilesViewModel.kt`:
    - `AvailableAgents` handler now reads `message.currentWorkspace` (gateway-owned), not any agent's `workspaceRoot`.
    - `FileTree` handler syncs `currentWorkspace` from `message.workspace`.
- **Architecture Note**: AI agents can still browse and operate on files (the gateway's workspace is the same filesystem they run on), but the workspace browser is now a standalone gateway feature — it works correctly with zero agents connected.

---

### BUG-008 — Antigravity IDE adapter (ag) hardcodes WebSocket port

- **Severity**: P3 Low
- **Status**: 🟢 FIXED
- **Reported**: 2026-06-18
- **Symptom**: The `ag` adapter connects strictly to `ws://127.0.0.1:8765`, ignoring the `antimatter.port` setting configured in VS Code.
- **Root Cause**: The `GatewayClient` hardcoded the port string.
- **Fix**: Updated `adapters/ag/src/core/network/GatewayClient.ts` to read `vscode.workspace.getConfiguration('antimatter').get<number>('port')`.

---

### BUG-007 — Android app shows "No history" for Antigravity IDE adapter (ag)

- **Severity**: P2 Medium
- **Status**: 🟢 FIXED
- **Reported**: 2026-06-18
- **Symptom**: The Android app shows no history or falls back to "New Conversation" for sessions running on the `ag` adapter.
- **Root Cause**: `HistoryManager.ts` read exactly 4096 bytes from `transcript.jsonl` using `fs.readSync()`. Modern trajectories inject a huge system prompt into the first line, meaning the `USER_INPUT` line exceeded 4KB, causing `JSON.parse` to fail and the title extraction loop to silently drop the history.
- **Fix**: Updated `adapters/ag/src/feature/chat/HistoryManager.ts` to use Node's `readline` module, robustly reading the file line by line with no arbitrary byte limits. Strips HTML tags (`<[^>]+>`) if `<USER_REQUEST>` is missing.

---

### BUG-006 — Opening regular markdown files triggers the Artifact UI in Chat

- **Severity**: P2 Medium
- **Status**: 🟢 FIXED
- **Reported**: 2026-06-18
- **Symptom**: If the user browses the workspace, opens a markdown file (e.g., a README), and then navigates back to the Chat screen, the file content is incorrectly displayed inside the "Artifact" sliding window pane as if it were an AI-generated artifact.
- **Root Cause**: Investigating state leakage between the file browser and the artifact viewer. `ChatViewModel` listened globally to `FILE_CONTENT` broadcasts from the gateway. If any file ending in `.md` arrived (even if requested by `FilesScreen`), `ChatViewModel` blindly loaded it into `activeArtifactContent`.
- **Fix**:
  - `core/network/src/.../ChatViewModel.kt`: Added `pendingArtifactPath` to track explicit requests originating from the Chat UI's `requestArtifactContent()`.
  - The `FILE_CONTENT` handler now strictly verifies `if (message.path == pendingArtifactPath)` before populating the artifact window, cleanly isolating file browsing from chat artifacts.

---

### BUG-005 — Android app does not auto-reconnect if the Gateway restarts

- **Severity**: P2 Medium
- **Status**: 🟢 FIXED
- **Reported**: 2026-06-18
- **Symptom**: If the gateway server is restarted or the connection drops, the Android app remains disconnected indefinitely. The user has to force-close and restart the Android app to reconnect.
- **Root Cause**: Two issues in `BridgeWebSocket.kt`:
  1. `clientSecret` was aggressively zeroed out `clientSecret!!.fill(0)` after the initial handshake to clear it from memory. The exponential backoff timer tried to reconnect but failed because the Cloudflare token was zeroed.
  2. The exponential backoff counter `reconnectAttempt` capped out at 20, but was never reset back to 0 on subsequent manual reconnections.
- **Fix**:
  - `core/network/src/.../BridgeWebSocket.kt`:
    - Removed `clientSecret!!.fill(0)` to keep the secret alive for background reconnections.
    - Added `reconnectAttempt = 0` to `connect()` so manual triggers always reset the backoff cycle.

---

### BUG-004 — Folders in nested directories are not clickable / show "failed to load"

- **Severity**: P1 High  
- **Status**: 🟢 FIXED  
- **Reported**: 2026-06-18  
- **Symptom**: Clicking on any folder that is **not** a top-level item in the workspace tree sends a `READ_FILE` command for that folder's path. The gateway responds with `[ERROR] READ_FILE failed: [Errno 21] Is a directory` and the app shows "failed to load file". Top-level folders could toggle correctly; only nested folders were broken.  
- **Root Cause (two-part)**:

  **Part A — Gateway serialisation bug (primary)**  
  `GET_FILES` in `router.py` converted the tree with a flat loop:

  ```python
  for node in tree:
      d = node.model_dump()
      d["isDir"] = d.pop("is_directory", False)
  ```

  `model_dump()` serialises the full nested tree recursively, but the `is_directory → isDir` rename only happened for the **top-level** list items. All child/grandchild nodes in the `children` arrays were emitted with the Pydantic field name `is_directory`, which Gson on Android cannot map to `isDir`. Gson defaults unknown fields to `false`, so every nested folder had `isDir == false` — making Android treat it as a plain file and call `openFile()` instead of `toggleFolder()`.

  **Part B — Gateway crash (secondary)**  
  Even with Part A fixed, the `READ_FILE` handler had no guard: it called `aiofiles.open()` unconditionally, which throws `EISDIR` when given a directory path.

- **Fix**:
  - `core/gateway/src/antimatter_gateway/router.py`:
    - Added `_node_to_dict(node)` — a recursive helper that manually builds the dict with `"isDir": node.is_directory` at **every** depth level, correctly serialising the full tree.
    - `GET_FILES` now calls `[self._node_to_dict(n) for n in tree]` instead of the broken flat loop.
    - `READ_FILE` now calls `resolved.is_dir()` before opening and returns a clear `ERROR` message (`"'src' is a folder, not a file."`) if the path is a directory, preventing the EISDIR crash.

---

### BUG-003 — No way to switch workspace from UI (allowlist not exposed)

- **Severity**: P2 Medium  
- **Status**: 🟢 FIXED  
- **Reported**: 2026-06-18  
- **Symptom**: The workspace header showed a small plain `TextButton` in the top-right actions area alongside the refresh icon. There was no clear way for the user to know they could tap it to switch workspaces, and it was visually merged with the refresh button making it easy to miss.  
- **Fix**: `android/feature/files/src/main/java/.../FilesScreen.kt`
  - Removed workspace `TextButton` from the `actions` slot.
  - Added a pill-shaped **workspace chip** in the `title` slot, centered in the app bar with a slight right bias from the leading nav area.
  - Chip shows: folder icon + current workspace folder name (last path segment) + chevron arrow (up/down depending on state).
  - Tapping opens a `DropdownMenu` listing every workspace from `allowedWorkspaces`.
  - Each dropdown item shows: folder icon (open if active), folder name bold, full path below in smaller text, and a ✓ checkmark on the currently active workspace.
  - If only one workspace is configured the chip is shown but is non-interactive (no dropdown arrow shown).
  - Refresh `IconButton` kept on the right.

---

### BUG-004 — Missing `agentId` in `GET_HISTORY`

- **Severity**: P1 High  
- **Status**: 🟢 FIXED  
- **Reported**: 2026-06-18  
- **Symptom**: When attempting to fetch chat history, the Gateway logs `[WARNING] No agentId specified in command: GET_HISTORY` and refuses to process the request, leaving the UI empty.
- **Root Cause**: Following the multi-adapter migration, the Gateway requires an `agentId` on all incoming commands. The Android app's `BridgeWebSocket` payload defaulted to `null` instead of attaching the `activeAgentId`.
- **Fix**: Updated `ChatViewModel.kt` to explicitly inject `agentId = _uiState.value.activeAgentId` into all `OutboundMessage.GetHistory` and related payloads. Also fixed a UX issue where the app forcefully auto-selected the first adapter on startup, preventing proper history requests. The app now starts with a null adapter requiring explicit manual selection.

---

### BUG-005 — WebSocket Buffer Overflow (Dropped Chat History Chunks)

- **Severity**: P1 High  
- **Status**: 🟢 FIXED  
- **Reported**: 2026-06-18  
- **Symptom**: Large chat histories load extremely slowly and eventually get "stuck." If the user sends a new message, the UI updates instantly, but the "middle" portion of the history is replaced with `...` and lost forever.
- **Root Cause**: When `BrainWatcher.ts` read massive `transcript.jsonl` files, it chunked steps into batches. However, because Node.js's `ws.send()` operates synchronously, blasting hundreds of massive payloads into the WebSocket in a tight loop overflowed the TCP network window and the Python Gateway's `max_queue`. This resulted in chunks being silently dropped. When a later chunk arrived, the Android UI filled the missing index gap with permanent `...` dots. Additionally, the Android UI had a debounce race-condition dropping concurrent incoming batches.
- **Fix**:
  1. Raised Python Gateway's `max_size=None` in `websockets.serve`.
  2. Added an explicit `await new Promise(r => setTimeout(r, 10))` pacing delay inside `BrainWatcher.ts` after every two chunk broadcasts to allow the network to drain.
  3. Rewrote the debounce coroutine inside Android's `ChatViewModel.kt` (`is InboundMessage.StepBatch`) to use a `while(true)` loop that safely grabs and clears pending buffer items without race conditions.

### BUG-006 — Artifact Workspace Path Traversal Rejection

- **Severity**: P2 Medium  
- **Status**: 🟢 FIXED  
- **Reported**: 2026-06-18  
- **Symptom**: Tapping on an artifact in the Android app results in an error message stating "Path traversal rejected" (interpreted by users as "conversation id is not in allowed workspace"). The artifact viewer opens but fails to load the content.
- **Root Cause**: The Android app requested artifact contents using the Gateway-native `READ_FILE` command. Since the gateway correctly isolates file access to the user-selected workspace, reading from the `~/.gemini/antigravity-ide/brain/` agent directory triggered a path traversal security rejection. Additionally, the backend filtered artifacts exclusively to `.md` files, ignoring other text formats like `.csv`.
- **Fix**: 
  1. Created a specialized `READ_ARTIFACT` routing command between the Android app and the `ag` adapter, bypassing the Gateway's workspace restriction entirely and isolating the read strictly to the active conversation's directory.
  2. Relaxed the artifact file filter in `HistoryManager.ts` to expose `.csv`, `.txt`, and `.json` in addition to `.md`. Note: Native image/PDF viewing within the `MarkdownText` renderer is intentionally omitted at this stage to prevent complex crashes.

---

### BUG-011 — Legacy Conversations Visibility

- **Severity**: P2 Medium
- **Status**: 🔴 UNRESOLVED
- **Reported**: 2026-06-18
- **Symptom**: The AG2 adapter only reads conversations that use the new `transcript.jsonl` format. There are ~14 older conversations in the `.system_generated/messages/` legacy format that do not appear in the sidebar and cannot be accessed.
- **Fix Needed**: Add a fallback or migration logic in `AgentBridge` to parse and serve the older legacy messages if `transcript.jsonl` does not exist.

---

### BUG-012 — Publishing to Open VSX

- **Severity**: P3 Low
- **Status**: 🔴 PENDING
- **Reported**: 2026-06-18
- **Symptom**: Need to finalize stability and readiness for publishing the VSCode extension. The extension is not yet published under `antimatter-saifmukhtar-dev`.
- **Fix Needed**: Run final integration tests, package the VSIX, and push to the Open VSX registry.

---

### BUG-013 — Unspecified User-Reported Bugs

- **Severity**: Unknown
- **Status**: 🔴 PENDING DETAILS
- **Reported**: 2026-06-18
- **Symptom**: User mentioned finding additional bugs during the last testing session but has not detailed them yet.
- **Fix Needed**: Update this block with specifics once the user provides details.

---
    
    ### BUG-015 — Release Build Fails to Connect / Circles Endlessly
    
    - **Severity**: P1 High
    - **Status**: 🟢 FIXED
    - **Reported**: 2026-06-20
    - **Symptom**: Debug builds of the Android app connect flawlessly to the Gateway, but Release builds (installed on physical devices) show a permanent loading circle when trying to access the workspace, and the terminal/agent connection fails silently.
    - **Root Cause**: ProGuard / R8 code minification was aggressively stripping and renaming the properties of Antimatter's internal network data models (e.g., `E2EESession$EncryptedEnvelope`, `AgentInfo`, `FileNode`). Because Gson relies on exact field names (like `iv`, `ct`, `aad` for E2EE payloads) to correctly parse JSON, the release build sent malformed `{"a":"...", "b":"..."}` packets to the Python Gateway and crashed silently upon receiving `{"current_workspace": "..."}`.
    - **Fix**: Added `-keep class dev.saifmukhtar.antimatter.core.network.** { *; }` to the `proguard-rules.pro` file, ensuring all network and domain objects retain their exact class structures and property names in the Release bundle.
    
    ---

### 4. Biometric Auth Gates

- **Status**: Tested
- **Functionality**: Fingerprint unlock integration is perfectly stable and working as expected.(Not Tested Face Unlock)
- **Known Issues**: None.

### 5. Cloudflare Tunnels

- **Status**: Tested
- **Functionality**: Permanent Cloudflare domain tunnels (`cloudflared tunnel run <name>`) work perfectly.
- **🚨 Known Issues**:
  - **Trycloudflare (Quick Tunnels)**: Removed. The temporary `trycloudflare.com` tunnels were unstable during the authentication challenge and have been entirely removed from the gateway codebase.

### 6. All Other Features

- **Status**: Untested
- **Note**: Any features not explicitly listed above (e.g., remote prompting) have not been formally tested yet. We cannot guarantee their stability or working order at this time.

---

### BUG-014 — "Message from self" UI Label when injecting user prompts

- **Severity**: P3 Low
- **Status**: 🔴 KNOWN LIMITATION
- **Reported**: 2026-06-19
- **Symptom**: When injecting prompts from the Android app without an API key (via the `agentapi send-message` mechanism in the `AG2 Adapter`), the IDE's UI renders the message as coming from a system/subagent source (e.g., "Message from self") rather than a physical user keyboard input.
- **Root Cause**: This is purely a visual limitation of headless IPC injection in Antigravity IDE. The `agentapi` binary designates inputs as system events.
- **Impact**: The underlying AI agent correctly interprets it as a high-priority user instruction regardless of the UI label. No functional impact.

---

## Reporting Issues

Community testing is vital! If you test these features and find any unexpected behavior, or if you manage to test the untried features (especially on iOS), it is highly encouraged to report the issues. Your feedback helps stabilize Antimatter!

---

## Architectural Logs & Decisions

### DECISION-001 — Connectivity & Global Naming (Zooko's Triangle)

- **Date**: 2026-06-20
- **Context**: Explored methods to completely remove third-party tunnel dependencies (like Cloudflare, Ngrok, Tailscale) and create a 100% decentralized, zero-setup connection between the Antimatter Gateway and the Android App.
- **The Ideal Vision**: A system where the user chooses a global username (e.g., `saif`), broadcasts it peer-to-peer, and connects seamlessly without any central server or crypto gas fees.
- **The Constraint (Zooko's Triangle)**: We discovered it is mathematically impossible to have global unique human-readable names + decentralization without implementing **Sybil Resistance** (which requires either a central authority like GitHub/Google, or an economic cost like Ethereum gas fees).
- **The Failed Approach**: Considered a "Central Spreadsheet" (e.g., a free GitHub repo) to register usernames. This was rejected because (a) it violates the Cypherpunk ethos by introducing a central supervisor (us), and (b) it is highly vulnerable to bot-spam registering all usernames.
- **The Workaround (Current Implementation)**:
  1. **Decentralized P2P DHT**: The Gateway generates a long cryptographic Public Key (e.g., `hyper://abc123xyz`) and broadcasts its IP to a public Distributed Hash Table (like Hyperswarm or BitTorrent Mainline). This acts as a decentralized NAT hole-punch.
  2. **QR Code OTP**: The QR code embeds both the DHT Public Key AND a highly secure One-Time Password (OTP) or AES Key.
  3. **Local Petnames**: The Android app scans the QR code, securely queries the DHT, authenticates the connection using the OTP to prevent MITM spoofing, and allows the user to save it locally with a human-readable "Petname" (e.g., `"My MacBook"`).
- **Conclusion**: We abandoned the "Global Username" dream for Antimatter as it belongs to a separate unproven moonshot project. We successfully solved the core routing problem using pure P2P DHT + QR code verification.
