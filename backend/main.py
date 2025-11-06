from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from agent.course_outline_generator import run_markdown_course_outline_generator
from agent.structured_course_outline_generator import run_structured_course_outline_generator
from utils.file_processor import file_processor
from agent.prompt_enhancer import prompt_enhancer
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
    Uses proper SSE event types to separate metadata from content.
    """
    first_chunk = True
    try:
        async for chunk in run_markdown_course_outline_generator(message, topic, number_of_classes, thread_id, file_contents):
            # First chunk contains the thread_id metadata
            if first_chunk and chunk.startswith("__THREAD_ID__:"):
                thread_id_value = chunk.replace("__THREAD_ID__:", "").strip()
                # Send thread_id as a separate SSE event type
                yield f"event: thread_id\ndata: {json.dumps({'thread_id': thread_id_value})}\n\n"
                first_chunk = False
            else:
                # Regular content chunks
                yield f"data: {json.dumps({'content': chunk})}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"

@app.post("/stream-outline")
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
        file_contents += await file_processor(files)
    
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


@app.post("/enhance-prompt")
async def enhance_prompt(
    message: str = Form(...),
    topic: str = Form(...),
    num_classes: int = Form(...),
):
    """
    Enhance the user's prompt to provide better instructions for course outline generation.
    """
    try:
        if not message.strip() or not topic.strip() or not num_classes:
            return JSONResponse(
                content={"error": "Message, topic, and number of classes are required"},
                status_code=400
            )

        enhanced = await prompt_enhancer(message, topic, num_classes)
        return JSONResponse(content={"enhanced_prompt": enhanced})
    
    except Exception as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )


async def structured_event_generator(
    message: str, 
    topic: str, 
    number_of_classes: int, 
    thread_id: Optional[str], 
    file_contents: List[dict]
):
    """
    Generator function that yields Server-Sent Events (SSE) for structured output.
    Yields progress updates and the final structured course outline.
    """
    try:
        async for event in run_structured_course_outline_generator(message, topic, number_of_classes, thread_id, file_contents):
            if isinstance(event, dict):
                event_type = event.get("type", "data")
                
                if event_type == "thread_id":
                    # Send thread_id as a separate SSE event type
                    yield f"event: thread_id\ndata: {json.dumps({'thread_id': event['thread_id']})}\n\n"
                elif event_type == "progress":
                    # Send progress updates
                    yield f"event: progress\ndata: {json.dumps({'message': event['message']})}\n\n"
                elif event_type == "complete":
                    # Send the complete structured data
                    yield f"event: complete\ndata: {json.dumps(event['data'])}\n\n"
                elif event_type == "error":
                    # Send error
                    yield f"event: error\ndata: {json.dumps({'message': event['message']})}\n\n"
            else:
                # Fallback for any other data
                yield f"data: {json.dumps({'content': str(event)})}\n\n"
    except Exception as e:
        yield f"event: error\ndata: {json.dumps({'message': str(e)})}\n\n"


@app.post("/structured-outline")
async def generate_structured_outline(
    message: str = Form(""),
    topic: str = Form(...),
    number_of_classes: int = Form(...),
    thread_id: Optional[str] = Form(None),
    files: Optional[List[UploadFile]] = File(None)
):
    """
    Handle lesson plan generation with structured output and optional file uploads.
    Returns a streaming SSE response with progress updates and structured data.
    """
    file_contents = []
    
    # Process uploaded files if any
    if files:
        file_contents += await file_processor(files)
    
    # Return SSE stream
    return StreamingResponse(
        structured_event_generator(message, topic, number_of_classes, thread_id, file_contents),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable buffering for nginx
        }
    )
