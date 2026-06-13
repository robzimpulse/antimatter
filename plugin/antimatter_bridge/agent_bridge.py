import asyncio
import json
import os
import glob
from pathlib import Path

class AgentBridge:
    def __init__(self, websocket, app_data_dir: str, current_convo_id: str):
        self.websocket = websocket
        self.agent = None
        self.app_data_dir = app_data_dir
        self.conversation_id = current_convo_id
        self.step_index = 0
        # BUG-005: Initialize last_position here so poll_transcript never raises AttributeError
        # even if send_transcript was not called first
        self.last_position = 0
        # BUG-006: Stop event for graceful shutdown of poll_transcript
        self._stop_event = asyncio.Event()

    async def _send_step(self, case: str, value: str = None, tool: str = None):
        step_payload = {"case": case}
        if value is not None:
            step_payload["value"] = value
        if tool is not None:
            step_payload["tool"] = tool

        await self.websocket.send(json.dumps({
            "type": "STEP",
            "index": self.step_index,
            "step": step_payload
        }))
        self.step_index += 1

    async def _send_generating(self):
        await self.websocket.send(json.dumps({
            "type": "GENERATING",
            "conversationId": self.conversation_id
        }))

    async def _send_response_complete(self):
        await self.websocket.send(json.dumps({
            "type": "RESPONSE_COMPLETE",
            "conversationId": self.conversation_id
        }))

    async def send_history(self):
        # We just return the current conversation as the only one in history
        # In a real app, you would scan brain/ for all conversations
        conversations = [{
            "id": self.conversation_id,
            "timestamp": 0,
            "title": "Current Session"
        }]
        await self.websocket.send(json.dumps({
            "type": "HISTORY_LIST",
            "conversations": conversations
        }))

    def _parse_line(self, line: str):
        import json
        import re
        try:
            data = json.loads(line)
            msg_type = data.get("type")
            content = data.get("content", "")

            steps_to_return = []
            
            def add_step(case_type, value):
                steps_to_return.append({
                    "index": self.step_index,
                    "step": {"case": case_type, "value": value}
                })
                self.step_index += 1
            
            if msg_type == "USER_INPUT":
                match = re.search(r'<USER_REQUEST>\s*(.*?)\s*</USER_REQUEST>', content, re.DOTALL)
                if match:
                    content = match.group(1).strip()
                else:
                    content = re.sub(r'<[^>]+>', '', content).strip()
                add_step("userInput", content)
            elif msg_type == "SYSTEM_MESSAGE":
                match = re.search(r'content=(.*?)(?:\n</SYSTEM_MESSAGE>|$)', content, re.DOTALL)
                if match:
                    parsed_content = match.group(1).strip()
                    if not parsed_content.startswith("Task id") and not parsed_content.startswith("Tool is running"):
                        add_step("userInput", parsed_content)
            elif msg_type == "PLANNER_RESPONSE":
                thinking = data.get("thinking", "")
                if thinking:
                    add_step("plannerResponse", thinking)
                if content:
                    add_step("text", content)
            elif msg_type == "SYSTEM_ALERT":
                add_step("ephemeralMessage", content)
            elif msg_type == "MODEL_TEXT":
                add_step("text", content)
            elif msg_type in ["RUN_COMMAND", "VIEW_FILE", "LIST_DIRECTORY", "CODE_ACTION", "GREP_SEARCH", "READ_URL_CONTENT", "SEARCH_WEB"]:
                pass
            elif msg_type == "ERROR_MESSAGE":
                add_step("errorMessage", content)
                
            return steps_to_return
        except Exception:
            return []

    async def send_transcript(self, convo_id: str):
        transcript_path = os.path.join(self.app_data_dir, "brain", convo_id, ".system_generated", "logs", "transcript.jsonl")
        steps = []
        
        self.step_index = 0
        self.last_position = 0

        if os.path.exists(transcript_path):
            with open(transcript_path, 'r', encoding='utf-8') as f:
                for line in f:
                    parsed_steps = self._parse_line(line)
                    if parsed_steps:
                        steps.extend(parsed_steps)
                self.last_position = f.tell()

        await self.websocket.send(json.dumps({
            "type": "STEP_BATCH",
            "steps": steps
        }))

    async def poll_transcript(self):
        """Poll the transcript file for new lines, with graceful shutdown and debouncing."""
        import asyncio
        transcript_path = os.path.join(
            self.app_data_dir, "brain", self.conversation_id,
            ".system_generated", "logs", "transcript.jsonl"
        )

        # Wait for file to exist, but respect the stop event
        while not os.path.exists(transcript_path):
            if self._stop_event.is_set():
                return
            await asyncio.sleep(1)

        with open(transcript_path, 'r', encoding='utf-8') as f:
            f.seek(self.last_position)
            # BUG-006 / STAB-004: Loop checks stop event for graceful shutdown;
            # a short sleep acts as a debounce to avoid spinning on rapid writes.
            while not self._stop_event.is_set():
                line = f.readline()
                if not line:
                    # STAB-004: 100ms sleep as debounce instead of tight 0ms spin
                    await asyncio.sleep(0.1)
                    continue

                parsed_steps = self._parse_line(line)
                if parsed_steps:
                    for s in parsed_steps:
                        if s["step"]["case"] in ["userInput", "toolCall"]:
                            await self._send_generating()
                        elif s["step"]["case"] in ["text", "errorMessage", "ephemeralMessage"]:
                            await self._send_response_complete()

                    await self.websocket.send(json.dumps({
                        "type": "STEP_BATCH",
                        "steps": parsed_steps
                    }))

    async def send_artifacts(self, convo_id: str):
        artifacts_dir = os.path.join(self.app_data_dir, "brain", convo_id)
        artifacts = []
        if os.path.exists(artifacts_dir):
            for file in os.listdir(artifacts_dir):
                if file.endswith(".md") and file not in ["task.md", "walkthrough.md", "implementation_plan.md"]:
                    artifacts.append({
                        "name": file,
                        "path": os.path.join(artifacts_dir, file),
                        "isDir": False
                    })
            # Add standard artifacts
            for std in ["implementation_plan.md", "task.md", "walkthrough.md"]:
                if os.path.exists(os.path.join(artifacts_dir, std)):
                    artifacts.append({
                        "name": std,
                        "path": os.path.join(artifacts_dir, std),
                        "isDir": False
                    })
                    
        await self.websocket.send(json.dumps({
            "type": "ARTIFACTS_LIST",
            "artifacts": artifacts
        }))

    async def send_workspace(self, root_path=None):
        if root_path is None:
            root_path = os.getcwd()
            
        # Build a 2-level deep file tree for the workspace to prevent overwhelming the socket
        def build_tree(path, depth=0):
            if depth > 2:
                return []
            nodes = []
            try:
                for item in os.listdir(path):
                    if item.startswith('.') or item == "__pycache__":
                        continue
                    full_path = os.path.join(path, item)
                    is_dir = os.path.isdir(full_path)
                    node = {
                        "name": item,
                        "path": full_path,
                        "isDir": is_dir
                    }
                    if is_dir and depth < 2:
                        node["children"] = build_tree(full_path, depth + 1)
                    nodes.append(node)
            except Exception:
                pass
            return sorted(nodes, key=lambda x: (not x["isDir"], x["name"]))
            
        tree = build_tree(root_path)
        await self.websocket.send(json.dumps({
            "type": "FILE_TREE",
            "tree": tree
        }))

    async def read_file(self, path: str):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            await self.websocket.send(json.dumps({
                "type": "FILE_CONTENT",
                "path": path,
                "content": content,
                "language": "markdown" if path.endswith(".md") else "text"
            }))
        except Exception as e:
            await self.websocket.send(json.dumps({
                "type": "ERROR",
                "message": f"Failed to read file: {e}"
            }))

    async def process_message(self, text: str):
        # Notify Android app we received the input
        await self._send_step("userInput", text)
        await self._send_generating()

        try:
            import subprocess
            agentapi_path = os.path.expanduser("~/.gemini/antigravity/bin/agentapi")
            result = subprocess.run([agentapi_path, "send-message", self.conversation_id, text], capture_output=True, text=True)
            if result.returncode != 0:
                await self._send_step("errorMessage", f"Failed to inject message into IDE: {result.stderr}")
            else:
                # Let the IDE handle generating the response!
                await self._send_step("ephemeralMessage", "Message successfully queued to IDE Agent. Pull to refresh history.")
        except Exception as e:
            await self._send_step("errorMessage", f"Agent Error: {str(e)}")
        finally:
            await self._send_response_complete()

    async def cleanup(self):
        # BUG-006: Signal poll_transcript to stop gracefully
        self._stop_event.set()
