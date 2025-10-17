from fastapi import FastAPI
from agent.graph import run_agent
from fastapi import WebSocket

app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    while True:
        data = await ws.receive_text()
        async for chunk in run_agent(data):
            await ws.send_text(chunk)


