import asyncio
import json
import logging
import os
import websockets
from pathlib import Path
from .agent_bridge import AgentBridge

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

APP_DATA_DIR = Path(os.environ.get("AGY_APP_DATA_DIR", os.path.expanduser("~/.gemini/antigravity")))
IPC_TOKEN_PATH = Path(os.path.expanduser("~/.antimatter_daemon/.ipc_token"))

def get_latest_conversation_id(app_data_dir: Path) -> str:
    brain_dir = app_data_dir / "brain"
    if not brain_dir.exists():
        return "default"
    
    conv_dirs = [d.name for d in brain_dir.iterdir() if d.is_dir() and (brain_dir / d / ".system_generated").exists()]
    if not conv_dirs:
        return "default"
        
    conv_dirs.sort(key=lambda d: (brain_dir / d).stat().st_mtime, reverse=True)
    return conv_dirs[0]

def get_default_workspace() -> str:
    if "AGY_WORKSPACE_DIR" in os.environ:
        return os.environ["AGY_WORKSPACE_DIR"]
    try:
        current = Path(__file__).resolve().parent
        while current != current.parent:
            if (current / ".git").exists():
                return str(current)
            current = current.parent
    except Exception:
        pass
    return os.getcwd()

async def main():
    uri = "ws://127.0.0.1:8765"

    # Read the IPC token written by the gateway on startup.
    # If missing, the gateway is not running — fail fast with a clear message.
    if not IPC_TOKEN_PATH.exists():
        print(
            f"[antimatter-ag2] Gateway IPC token not found at {IPC_TOKEN_PATH}.\n"
            "Make sure the Antimatter Gateway is running before starting the adapter."
        )
        return
    logger.info(f"[AG2 Adapter] Connecting to Gateway at {uri}...")

    while True:
        try:
            # Read token inside the loop so we get the fresh token if Gateway restarts
            # Read token inside the loop so we get the fresh token if Gateway restarts
            if IPC_TOKEN_PATH.exists():
                ipc_token = IPC_TOKEN_PATH.read_text().strip()
                logger.info(f"[AG2 Adapter] Found token of length {len(ipc_token)}")
            else:
                ipc_token = ""
                logger.warning(f"[AG2 Adapter] Token file {IPC_TOKEN_PATH} not found!")
                
            async with websockets.connect(uri) as websocket:
                logger.info("[AG2 Adapter] Connected to Gateway IPC.")

                import uuid
                id_file = APP_DATA_DIR / ".agent_id"
                if id_file.exists():
                    agent_id = id_file.read_text().strip()
                else:
                    agent_id = str(uuid.uuid4())
                    id_file.write_text(agent_id)

                # Include ipc_token so the gateway can verify this is a
                # legitimate local adapter and not a rogue process (AM-010).
                await websocket.send(json.dumps({
                    "type": "REGISTER_ADAPTER",
                    "ipc_token": ipc_token,
                    "id": agent_id,
                    "name": "ag2",
                    "workspaceRoot": get_default_workspace()
                }))
                
                convo_id = os.environ.get("AGY_CONVERSATION_ID") or get_latest_conversation_id(APP_DATA_DIR)
                bridge = AgentBridge(websocket, str(APP_DATA_DIR), convo_id)
                bridge._watch_task = asyncio.create_task(bridge.watch_brain_dir())
                bridge._poll_task = asyncio.create_task(bridge.poll_transcript())
                
                try:
                    async for message in websocket:
                        try:
                            data = json.loads(message)
                            msg_type = data.get("type")
                            
                            if msg_type == "SUBSCRIBE_CONVERSATION":
                                cid = data.get("conversationId")
                                if cid:
                                    bridge.conversation_id = cid
                                if bridge.conversation_id:
                                    await bridge.send_transcript(bridge.conversation_id)
                                    await bridge.send_artifacts(bridge.conversation_id)
                                await bridge.send_workspace(get_default_workspace())

                            elif msg_type == "NEW_CONVERSATION":
                                # ag2 does not support new conversations, but we shouldn't throw an error
                                # because the Android app calls this automatically when switching agents.
                                # Instead, just send the current session state.
                                if bridge.conversation_id:
                                    await bridge.send_transcript(bridge.conversation_id)

                            elif msg_type == "GET_HISTORY":
                                await bridge.send_history()

                            elif msg_type == "GET_ARTIFACTS":
                                cid = data.get("conversationId", bridge.conversation_id)
                                if cid:
                                    await bridge.send_artifacts(cid)

                            elif msg_type == "READ_ARTIFACT":
                                path = data.get("path")
                                if path:
                                    await bridge.read_artifact(path)

                            elif msg_type == "GET_FILES":
                                await bridge.send_workspace(get_default_workspace())
                                
                            elif msg_type == "READ_FILE":
                                path = data.get("path")
                                if path:
                                    await bridge.read_file(path)
                                
                            elif msg_type == "SEND_MESSAGE":
                                logger.debug("[AG2 Adapter] Received SEND_MESSAGE")
                                text = data.get("text", "")
                                images = data.get("images", [])
                                asyncio.create_task(bridge.process_message(text, images))
                                
                            elif msg_type == "PING":
                                await websocket.send(json.dumps({"type": "PONG"}))
                                
                        except json.JSONDecodeError:
                            pass
                finally:
                    await bridge.cleanup()
                    
        except Exception as e:
            logger.warning(f"[AG2 Adapter] Connection error: {e}. Reconnecting in 3s...")
            await asyncio.sleep(3)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nAdapter shut down gracefully.")
