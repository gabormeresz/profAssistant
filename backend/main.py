from fastapi import FastAPI, WebSocket
from agent.graph import run_graph
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
            thread_id = request_data.get("thread_id")  # Get thread_id from frontend
            
            # Pass structured data to graph including thread_id
            async for chunk in run_graph(message, topic, number_of_classes, thread_id):
                await ws.send_text(chunk)
        except json.JSONDecodeError:
            await ws.send_text("Error: Invalid JSON format")
        except Exception as e:
            await ws.send_text(f"Error: {str(e)}")


