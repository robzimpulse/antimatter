import asyncio
import json
import logging
from antimatter_crypto.e2ee import E2EESession
from antimatter_gateway.pty_manager import PtyManager

logger = logging.getLogger(__name__)

class MessageRouter:
    def __init__(self, gateway=None):
        self.gateway = gateway
        self.clients = set()
        self.adapters = {} # id -> {"name": str, "ws": websocket}
        self.pty_manager = PtyManager(self)

    def add_client(self, websocket):
        self.clients.add(websocket)
        # When a client connects, instantly send them the list of agents
        asyncio.create_task(self.broadcast_system_state())

    def remove_client(self, websocket):
        self.clients.discard(websocket)

    async def register_adapter(self, agent_id: str, agent_name: str, websocket, workspace_root: str = None):
        self.adapters[agent_id] = {"name": agent_name, "ws": websocket, "workspace_root": workspace_root}
        await self.broadcast_system_state()

    async def unregister_adapter(self, agent_id: str):
        if agent_id in self.adapters:
            del self.adapters[agent_id]
            await self.broadcast_system_state()

    async def broadcast_system_state(self):
        # Implementation to send AVAILABLE_AGENTS to clients
        if not self.clients or not self.gateway:
            return
            
        agents = [
            {"id": aid, "name": info["name"], "status": "online", "workspaceRoot": info["workspace_root"]}
            for aid, info in self.adapters.items()
        ]
        
        payload = {
            "type": "AVAILABLE_AGENTS", 
            "agents": agents,
            "allowed_workspaces": self.gateway.config.allowed_workspaces
        }
        
        await self.broadcast_to_clients(payload, self.gateway.e2ee)

    async def route_to_adapter(self, parsed_cmd: dict, e2ee: E2EESession, websocket):
        """
        Receives decrypted command from client, routes to local adapter or handles it internally.
        """
        cmd_type = parsed_cmd.get("type")
        
        # Internal Gateway Commands (no agentId required)
        if cmd_type == "PTY_START":
            # For simplicity, session ID is the client websocket id or 'default'
            session_id = id(websocket)
            cols = parsed_cmd.get("cols", 80)
            rows = parsed_cmd.get("rows", 24)
            await self.pty_manager.start_pty(session_id, cols, rows)
            return
            
        if cmd_type == "PTY_INPUT":
            session_id = id(websocket)
            data = parsed_cmd.get("data", "")
            self.pty_manager.write_input(session_id, data)
            return
            
        if cmd_type == "PTY_RESIZE":
            session_id = id(websocket)
            cols = parsed_cmd.get("cols", 80)
            rows = parsed_cmd.get("rows", 24)
            self.pty_manager.resize(session_id, cols, rows)
            return
            
        if cmd_type == "PTY_PING":
            session_id = id(websocket)
            self.pty_manager.ping(session_id)
            return

        # Internal commands that can optionally apply to an adapter, but work natively too
        if cmd_type == "CHANGE_WORKSPACE":
            new_path = parsed_cmd.get("path")
            agent_id = parsed_cmd.get("agentId")
            if new_path in self.gateway.config.allowed_workspaces:
                if agent_id and agent_id in self.adapters:
                    self.adapters[agent_id]["workspace_root"] = new_path
                    logger.info(f"Workspace for agent {agent_id} changed to {new_path}")
                else:
                    self.current_workspace = new_path
                    logger.info(f"Native gateway workspace changed to {new_path}")
                await self.broadcast_system_state()
            else:
                logger.warning(f"Rejected workspace change: {new_path} is not in allowed_workspaces")
            return
            
        if cmd_type == "GET_FILES":
            from antimatter_fs.tree import build_file_tree
            agent_id = parsed_cmd.get("agentId")
            if agent_id and agent_id in self.adapters:
                root_path = self.adapters[agent_id].get("workspace_root") or getattr(self, "current_workspace", ".")
            else:
                root_path = getattr(self, "current_workspace", ".")
                
            tree = await build_file_tree(root_path)
            
            tree_dict = []
            for node in tree:
                d = node.model_dump()
                d["isDir"] = d.pop("is_directory", False)
                tree_dict.append(d)
            
            await self.broadcast_to_clients({
                "type": "FILE_TREE",
                "tree": tree_dict
            }, e2ee)
            return

        # Commands routed to specific agents
        agent_id = parsed_cmd.get("agentId")
        if not agent_id:
            logger.warning(f"No agentId specified in command: {cmd_type}")
            return
            
        adapter = self.adapters.get(agent_id)
        if not adapter:
            logger.warning(f"Target agent {agent_id} is offline. Dropping command.")
            return

        try:
            await adapter["ws"].send(json.dumps(parsed_cmd))
        except Exception as e:
            logger.error(f"Failed to route to adapter {agent_id}: {e}")

    async def broadcast_to_clients(self, payload: dict, e2ee: E2EESession):
        """
        Takes raw JSON payload from an adapter, encrypts it with the 
        server-to-client key, and sends it to all Android apps.
        """
        plaintext = json.dumps(payload)
        envelope = e2ee.encrypt(plaintext, direction="output")
        payload_str = json.dumps(envelope)
        
        for client in list(self.clients):
            try:
                await client.send(payload_str)
            except Exception:
                self.clients.discard(client)
