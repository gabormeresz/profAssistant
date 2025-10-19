from fastapi import FastAPI, WebSocket, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from agent.graph import run_graph
from agent.file_processor import FileProcessor
import json
from typing import List

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    """
    Handle file uploads and extract text content.
    Returns the extracted text content from all files.
    """
    try:
        file_contents = []
        processor = FileProcessor()
        
        for uploaded_file in files:
            # Read file bytes
            file_bytes = await uploaded_file.read()
            
            # Process the file
            try:
                content = processor.process_file(uploaded_file.filename or "unknown", file_bytes)
                file_contents.append({
                    "filename": uploaded_file.filename,
                    "content": content
                })
            except Exception as e:
                file_contents.append({
                    "filename": uploaded_file.filename,
                    "content": f"[Error processing file: {str(e)}]"
                })
        
        return {"files": file_contents}
    except Exception as e:
        return {"error": str(e)}, 500

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            data = await ws.receive_text()
            
            # Parse the JSON data from frontend
            try:
                request_data = json.loads(data)
                message = request_data.get("message", "")
                topic = request_data.get("topic", "")
                number_of_classes = request_data.get("number_of_classes", 1)
                thread_id = request_data.get("thread_id")  # Get thread_id from frontend
                file_contents = request_data.get("file_contents", [])  # Get file contents
                
                # Pass structured data to graph including thread_id and file contents
                async for chunk in run_graph(message, topic, number_of_classes, thread_id, file_contents):
                    await ws.send_text(chunk)
                
                # Close the connection after streaming is complete
                await ws.close()
                break
            except json.JSONDecodeError:
                await ws.send_text("Error: Invalid JSON format")
                await ws.close()
                break
            except Exception as e:
                await ws.send_text(f"Error: {str(e)}")
                await ws.close()
                break
    except Exception as e:
        print(f"WebSocket error: {e}")
        await ws.close()


