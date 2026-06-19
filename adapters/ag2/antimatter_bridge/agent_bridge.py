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
        self.active_session_id = current_convo_id
        self.conversation_id = current_convo_id
        self.step_index = 0
        # BUG-005: Initialize last_position here so poll_transcript never raises AttributeError
        # even if send_transcript was not called first
        self.last_position = 0
        # BUG-006: Stop event for graceful shutdown of poll_transcript
        self._stop_event = asyncio.Event()
        self._watch_task = None

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
        """Sends the history list of conversations.
        Since ag2 connects to an external agent that doesn't explicitly expose conversation history,
        we just return the current session as the history.
        """
        import os
        import json
        import re
        
        timestamp = 0
        title = "Current Session"
        transcript_path = os.path.join(self.app_data_dir, "brain", self.active_session_id, ".system_generated", "logs", "transcript.jsonl")
        
        if os.path.exists(transcript_path):
            timestamp = int(os.path.getmtime(transcript_path) * 1000)
            try:
                with open(transcript_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            data = json.loads(line)
                            if data.get("type") == "USER_INPUT":
                                content = data.get("content", "")
                                match = re.search(r'<USER_REQUEST>\s*(.*?)\s*</USER_REQUEST>', content, re.DOTALL)
                                if match:
                                    title = match.group(1).strip()
                                else:
                                    title = re.sub(r'<[^>]+>', '', content).strip()
                                # Truncate title
                                if len(title) > 50:
                                    title = title[:47] + "..."
                                break
                        except Exception:
                            pass
            except Exception:
                pass
                
        conversations = [{
            "id": self.active_session_id,
            "timestamp": timestamp,
            "title": title
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
                        add_step("SYSTEM_MESSAGE", parsed_content)
            elif msg_type == "PLANNER_RESPONSE":
                thinking = data.get("thinking", "")
                if thinking:
                    clean_thinking = []
                    for paragraph in thinking.split("\n\n"):
                        p_lower = paragraph.lower()
                        is_boilerplate = (
                            "critical instruction" in p_lower or
                            "tool specificity" in p_lower or
                            "tool usage" in p_lower or
                            "tool ecosystem" in p_lower or
                            "tool repertoire" in p_lower or
                            "instruction to avoid cat" in p_lower or
                            "eliminating the use of ls" in p_lower or
                            "default to grep_search" in p_lower or
                            "actively avoiding using ls" in p_lower or
                            "avoiding cat within bash" in p_lower or
                            "before making tool calls" in p_lower or
                            "list related tools" in p_lower or
                            "tool list: `" in p_lower or
                            "i must prioritize using the most specific tool" in p_lower or
                            (p_lower.startswith("#") and ("tool" in p_lower or "instruction" in p_lower))
                        )
                        if not is_boilerplate:
                            clean_thinking.append(paragraph)
                    
                    final_thinking = "\n\n".join(clean_thinking).strip()
                    if final_thinking:
                        stripped_of_punctuation = re.sub(r'[#\s*\-=_]+', '', final_thinking).strip()
                        if stripped_of_punctuation:
                            add_step("plannerResponse", final_thinking)
                if content:
                    add_step("text", content)
            elif msg_type == "SYSTEM_ALERT":
                add_step("ephemeralMessage", content)
            elif msg_type == "MODEL_TEXT":
                add_step("text", content)
            elif msg_type in ["VIEW_FILE", "LIST_DIRECTORY", "CODE_ACTION", "GREP_SEARCH", "READ_URL_CONTENT", "SEARCH_WEB"]:
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
            try:
                with open(transcript_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        parsed_steps = self._parse_line(line)
                        if parsed_steps:
                            steps.extend(parsed_steps)
                    self.last_position = f.tell()

            except Exception as e:
                print(f"[Gateway] ERROR in reading transcript: {e}", flush=True)

        await self.websocket.send(json.dumps({
            "type": "STEP_BATCH",
            "steps": steps
        }))

    async def poll_transcript(self):
        """Poll the transcript file for new lines, with graceful shutdown and debouncing."""
        import asyncio
        current_opened_convo_id = None
        f = None

        try:
            while not self._stop_event.is_set():
                if current_opened_convo_id != self.conversation_id:
                    if f:
                        f.close()
                    transcript_path = os.path.join(
                        self.app_data_dir, "brain", self.conversation_id,
                        ".system_generated", "logs", "transcript.jsonl"
                    )
                    # Wait for file to exist
                    while not os.path.exists(transcript_path):
                        if self._stop_event.is_set() or current_opened_convo_id != self.conversation_id:
                            break
                        await asyncio.sleep(1)
                        
                    if self._stop_event.is_set():
                        break
                    
                    if os.path.exists(transcript_path):
                        f = open(transcript_path, 'r', encoding='utf-8')
                        f.seek(self.last_position)
                        current_opened_convo_id = self.conversation_id
                
                if f:
                    line = f.readline()
                    if not line:
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
                else:
                    await asyncio.sleep(0.5)
        finally:
            if f:
                f.close()

    async def watch_brain_dir(self):
        brain_dir = os.path.join(self.app_data_dir, "brain")
        while not self._stop_event.is_set():
            try:
                if os.path.exists(brain_dir):
                    subdirs = [os.path.join(brain_dir, d) for d in os.listdir(brain_dir) if os.path.isdir(os.path.join(brain_dir, d))]
                    if subdirs:
                        newest_dir = max(subdirs, key=os.path.getmtime)
                        newest_convo_id = os.path.basename(newest_dir)
                        if newest_convo_id != "scratch":
                            # Only broadcast history so the sidebar updates, don't force a UI switch
                            await self.send_history()
            except Exception:
                pass
            await asyncio.sleep(2)

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

    async def read_artifact(self, path: str):
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                await self.websocket.send(json.dumps({
                    "type": "ARTIFACT_CONTENT",
                    "path": path,
                    "content": content
                }))
            except Exception:
                pass

    async def send_workspace(self, root_path=None):
        if root_path is None:
            root_path = os.getcwd()

        IGNORED = {
            'node_modules', '.git', 'dist', 'build', 'out', '.gradle',
            '__pycache__', '.venv', 'venv', '.idea', '.DS_Store', '.kotlin',
        }

        # Performance: Build the file tree in a thread pool so the synchronous
        # os.listdir/os.path.isdir calls don't block the asyncio event loop.
        def build_tree(path: str, depth: int = 0) -> list:
            if depth > 2:
                return []
            nodes = []
            try:
                for item in sorted(os.listdir(path)):
                    if item.startswith('.') or item in IGNORED:
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
            except PermissionError:
                pass
            except Exception:
                pass
            # Directories first, then files, both alphabetical
            return sorted(nodes, key=lambda x: (not x["isDir"], x["name"]))

        # Run synchronous tree scan off the event loop
        tree = await asyncio.to_thread(build_tree, root_path)
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

    async def process_message(self, text: str, images: list = None):
        if images is None:
            images = []
            
        # Process images
        if images:
            import base64
            import time
            scratch_dir = os.path.join(self.app_data_dir, "brain", self.conversation_id, "scratch")
            os.makedirs(scratch_dir, exist_ok=True)
            
            for i, b64_str in enumerate(images):
                try:
                    # Strip data URI prefix if present (e.g. data:image/jpeg;base64,)
                    if "," in b64_str:
                        b64_str = b64_str.split(",")[1]
                        
                    img_data = base64.b64decode(b64_str)
                    timestamp = int(time.time() * 1000)
                    filename = f"upload_{timestamp}_{i}.jpg"
                    filepath = os.path.join(scratch_dir, filename)
                    
                    with open(filepath, "wb") as f:
                        f.write(img_data)
                        
                    text += f"\n\n![Image](file://{filepath})"
                except Exception as e:
                    print(f"Failed to decode image {i}: {e}")

        # Notify Android app we received the input
        await self._send_step("userInput", text)
        await self._send_generating()

        try:
            import asyncio
            agentapi_path = os.path.expanduser("~/.gemini/antigravity/bin/agentapi")
            
            proc = await asyncio.create_subprocess_exec(
                agentapi_path, "send-message", self.conversation_id, text,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            
            if proc.returncode != 0:
                await self._send_step("errorMessage", f"Failed to inject message into IDE: {stderr.decode()}")
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
