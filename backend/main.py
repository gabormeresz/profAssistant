from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from agent.graph import run_graph
from agent.file_processor import FileProcessor
import json
from typing import List, Optional

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def event_generator(message: str, topic: str, number_of_classes: int, thread_id: Optional[str], file_contents: List[dict]):
    """
    Generator function that yields Server-Sent Events (SSE) formatted data.
    """
    try:
        async for chunk in run_graph(message, topic, number_of_classes, thread_id, file_contents):
            # Format as SSE: each message should be prefixed with "data: " and end with "\n\n"
            yield f"data: {json.dumps({'content': chunk})}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"

@app.post("/stream")
async def stream_lesson_plan(
    message: str = Form(""),
    topic: str = Form(...),
    number_of_classes: int = Form(...),
    thread_id: Optional[str] = Form(None),
    files: Optional[List[UploadFile]] = File(None)
):
    """
    Handle lesson plan generation with optional file uploads.
    Returns a streaming SSE response.
    """
    file_contents = []
    
    # Process uploaded files if any
    if files:
        processor = FileProcessor()
        for uploaded_file in files:
            try:
                file_bytes = await uploaded_file.read()
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
    
    # Return SSE stream
    return StreamingResponse(
        event_generator(message, topic, number_of_classes, thread_id, file_contents),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable buffering for nginx
        }
    )


