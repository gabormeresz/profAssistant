from fastapi import FastAPI, WebSocket
from agent.graph import run_agent
import json

app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    while True:
        data = await ws.receive_text()
        
        # Parse the JSON data from frontend
        try:
            request_data = json.loads(data)
            message = request_data.get("message", "")
            topic = request_data.get("topic", "")
            number_of_classes = request_data.get("number_of_classes", 1)
            
            # Pass structured data to agent
            async for chunk in run_agent(message, topic, number_of_classes):
                await ws.send_text(chunk)
        except json.JSONDecodeError:
            await ws.send_text("Error: Invalid JSON format")
        except Exception as e:
            await ws.send_text(f"Error: {str(e)}")


