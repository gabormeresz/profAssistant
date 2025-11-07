from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from agent.structured_course_outline_generator import run_structured_course_outline_generator
from utils.file_processor import file_processor
from agent.prompt_enhancer import prompt_enhancer
from services.conversation_manager import conversation_manager
from schemas.conversation import (
    ConversationType, 
    ConversationList,
    CourseOutlineUpdate,
    LessonPlanUpdate
)
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


@app.post("/outline-generator")
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


# ============================================================================
# Conversation Management Endpoints
# ============================================================================

@app.get("/conversations")
async def list_conversations(
    conversation_type: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """
    List all saved conversations with optional filtering by type.
    """
    try:
        conv_type = ConversationType(conversation_type) if conversation_type else None
        conversations = conversation_manager.list_conversations(
            conversation_type=conv_type,
            limit=limit,
            offset=offset
        )
        total = conversation_manager.count_conversations(conversation_type=conv_type)
        
        return ConversationList(
            conversations=conversations,
            total=total
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid conversation type")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/conversations/{thread_id}")
async def get_conversation(thread_id: str):
    """
    Get metadata for a specific conversation.
    """
    conversation = conversation_manager.get_conversation(thread_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@app.patch("/conversations/{thread_id}")
async def update_conversation(thread_id: str, update: CourseOutlineUpdate):
    """
    Update conversation metadata.
    Note: Currently only supports CourseOutline updates. 
    For lesson plans, use a separate endpoint or extend this with Union types.
    """
    existing = conversation_manager.get_conversation(thread_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Determine type and call appropriate update method
    if existing.conversation_type == ConversationType.COURSE_OUTLINE:
        updated = conversation_manager.update_course_outline(
            thread_id=thread_id,
            data=update
        )
    else:
        raise HTTPException(status_code=400, detail="Update not supported for this conversation type via this endpoint")
    
    return updated


@app.delete("/conversations/{thread_id}")
async def delete_conversation(thread_id: str):
    """
    Delete a conversation and its metadata.
    Note: This only deletes the metadata. The checkpoint data remains in checkpoints.db.
    """
    deleted = conversation_manager.delete_conversation(thread_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return {"success": True, "message": "Conversation deleted"}


@app.get("/conversations/{thread_id}/history")
async def get_conversation_history(thread_id: str):
    """
    Retrieve the conversation history (messages) from checkpoints.db for a given thread_id.
    Returns the messages in chronological order.
    """
    try:
        from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
        
        # Get conversation metadata to verify it exists
        conversation = conversation_manager.get_conversation(thread_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Connect to checkpoints database and retrieve history
        async with AsyncSqliteSaver.from_conn_string("checkpoints.db") as checkpointer:
            # Get the checkpoint for this thread
            config = {"configurable": {"thread_id": thread_id}}
            
            # Get the latest state
            state = await checkpointer.aget(config)  # type: ignore
            
            if not state:
                # No messages yet in this thread
                return {
                    "thread_id": thread_id,
                    "messages": [],
                    "metadata": conversation.model_dump()
                }
            
            # Extract messages from state
            # In LangGraph v1, the checkpoint state is a dict with 'channel_values' key
            messages = []
            
            # State is a dict, and the actual state data is in 'channel_values'
            state_dict = state if isinstance(state, dict) else {}  # type: ignore
            
            # Access the actual channel values
            if isinstance(state_dict, dict) and 'channel_values' in state_dict:
                channel_values = state_dict['channel_values']  # type: ignore
                
                if isinstance(channel_values, dict) and 'messages' in channel_values:
                    state_dict = channel_values  # Use channel_values as the actual state
            
            if "messages" in state_dict:  # type: ignore
                raw_messages = state_dict["messages"]  # type: ignore
                
                # Handle both single message and list of messages
                if not isinstance(raw_messages, list):
                    raw_messages = [raw_messages]
                
                # Keep track of whether we have structured_response
                has_structured_response = "structured_response" in state_dict  # type: ignore
                structured_response = state_dict.get("structured_response") if has_structured_response else None  # type: ignore
                
                for i, msg in enumerate(raw_messages):
                    # Extract message content based on structure
                    content = ""
                    role = "assistant"
                    
                    # Determine role from LangChain message type first
                    if hasattr(msg, "__class__"):
                        class_name = msg.__class__.__name__  # type: ignore
                        if "Human" in class_name or "User" in class_name:
                            role = "user"
                        elif "AI" in class_name or "Assistant" in class_name:
                            role = "assistant"
                        elif "Tool" in class_name:
                            # Skip tool messages - they are internal to the agent
                            continue
                    elif hasattr(msg, "type"):
                        msg_type = str(getattr(msg, "type", ""))
                        if msg_type == "tool":
                            continue
                        role = "user" if msg_type == "human" else "assistant"
                    elif isinstance(msg, dict) and "role" in msg:  # type: ignore
                        role = str(msg["role"])  # type: ignore
                    
                    # For assistant messages, use the structured_response if available
                    # For user messages, use the message content
                    if role == "assistant" and structured_response:
                        # Return the structured response as JSON
                        import json
                        content = json.dumps(structured_response.model_dump() if hasattr(structured_response, 'model_dump') else structured_response)  # type: ignore
                    else:
                        # LangChain message objects have a content attribute
                        if hasattr(msg, "content"):
                            content = str(msg.content)  # type: ignore
                        elif isinstance(msg, dict) and "content" in msg:  # type: ignore
                            content = str(msg["content"])  # type: ignore
                        else:
                            content = str(msg)
                    
                    messages.append({
                        "role": role,
                        "content": content
                    })
            
            return {
                "thread_id": thread_id,
                "messages": messages,
                "metadata": conversation.model_dump()
            }
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to retrieve conversation history: {str(e)}")


