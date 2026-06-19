import asyncio
import websockets
import json
import uuid

async def test():
    uri = "ws://127.0.0.1:8765"
    async with websockets.connect(uri) as ws:
        # Subscribe to a conversation
        await ws.send(json.dumps({
            "type": "SUBSCRIBE_CONVERSATION",
            "conversationId": "727bb88a-0437-4135-a7d8-0528355ed831",
            "agentId": "ag2"
        }))
        
        while True:
            msg = await asyncio.wait_for(ws.recv(), timeout=2.0)
            data = json.loads(msg)
            print("Received:", data.get("type"))
            if data.get("type") == "STEP_BATCH":
                steps = data.get("steps", [])
                print(f"Got {len(steps)} steps")
                for s in steps[:2]:
                    print("Step:", s)
                break

asyncio.run(test())
