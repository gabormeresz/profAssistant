import logging
from config import LoggingConfig

# Configure logging
logging.basicConfig(
    level=LoggingConfig.LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from agent.course_outline_generator import run_course_outline_generator
from agent.course_outline.dummy_generator import run_dummy_course_outline_generator
from agent.lesson_plan import run_lesson_plan_generator
from utils.file_processor import file_processor
from agent.prompt_enhancer import prompt_enhancer
from services.conversation_manager import conversation_manager
from services.rag_pipeline import get_rag_pipeline
from services.mcp_client import mcp_manager
from routes.auth import router as auth_router
from services.auth_service import get_current_user
from schemas.conversation import (
    ConversationType,
    ConversationList,
)
from config import DebugConfig
import json
from typing import List, Optional

logger = logging.getLogger(__name__)

# Log dummy graph status at import time
if DebugConfig.USE_DUMMY_GRAPH:
    logger.warning(
        "⚠️  DUMMY GRAPH ENABLED — course outline requests use fake data (no LLM calls)"
    )


def _resolve_api_key(user: dict) -> str:
    """
    Validate that the user has a usable OpenAI API key.

    Delegates to ``api_key_service`` so that the logic lives in one
    place.  The returned key is used **only** for early HTTP-level
    validation — nodes and helpers resolve it themselves from
    ``user_id``.

    Raises HTTPException 403/500 when no key is available.
    """
    from services.api_key_service import require_api_key

    try:
        return require_api_key(user["user_id"])
    except ValueError:
        if user["role"] == "admin":
            raise HTTPException(
                status_code=500,
                detail="Server-side OPENAI_API_KEY is not configured.",
            )
        raise HTTPException(
            status_code=403,
            detail="errors.apiKeyRequired",
        )


def _classify_error(exc: Exception) -> dict:
    """
    Map common OpenAI / API-key errors to frontend-translatable message keys.

    Returns a dict suitable for ``json.dumps`` inside an SSE error event,
    containing both ``message`` (raw) and ``message_key`` (i18n key).
    """
    import openai

    raw = str(exc)

    if isinstance(exc, openai.AuthenticationError):
        return {"message": raw, "message_key": "errors.invalidApiKey"}
    if isinstance(exc, openai.RateLimitError):
        # OpenAI uses 429 for both rate-limit and insufficient-quota
        lower = raw.lower()
        if "quota" in lower or "billing" in lower or "exceeded" in lower:
            return {"message": raw, "message_key": "errors.insufficientQuota"}
        return {"message": raw, "message_key": "errors.rateLimited"}
    if isinstance(exc, openai.APIStatusError) and exc.status_code >= 500:
        return {"message": raw, "message_key": "errors.openaiUnavailable"}
    if isinstance(exc, ValueError) and "API key" in raw:
        return {"message": raw, "message_key": "errors.apiKeyRequired"}

    return {"message": raw, "message_key": "errors.generationFailed"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan handler for FastAPI application startup/shutdown.

    Initializes MCP clients on startup and cleans up on shutdown.
    """
    # Startup
    print("[Startup] Initializing MCP clients...")
    await mcp_manager.initialize()
    print("[Startup] Application ready")

    yield

    # Shutdown
    print("[Shutdown] Cleaning up MCP clients...")
    await mcp_manager.cleanup()
    print("[Shutdown] Application stopped")


app = FastAPI(lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
    ],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Auth routes ──
app.include_router(auth_router)


@app.post("/enhance-prompt")
async def enhance_prompt(
    message: str = Form(...),
    context_type: str = Form("course_outline"),
    additional_context: Optional[str] = Form(None),
    language: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user),
):
    """
    Enhance the user's prompt to provide better instructions for educational content generation.

    Args:
        message: The user's message/instructions to enhance
        context_type: Type of content being generated ("course_outline" or "lesson_plan")
        additional_context: JSON string with context-specific fields:
            - For course_outline: topic, num_classes
            - For lesson_plan: topic, class_title, learning_objectives, key_topics, activities_projects
        language: Optional language for the output (e.g., "English", "Hungarian")
    """
    try:
        if not message.strip():
            return JSONResponse(
                content={"error": "Message is required"}, status_code=400
            )

        # Resolve per-user API key
        _resolve_api_key(current_user)

        # Validate context_type
        valid_contexts = ["course_outline", "lesson_plan"]
        if context_type not in valid_contexts:
            return JSONResponse(
                content={
                    "error": f"Invalid context_type. Must be one of: {', '.join(valid_contexts)}"
                },
                status_code=400,
            )

        # Parse additional_context if provided
        context_dict = None
        if additional_context:
            try:
                context_dict = json.loads(additional_context)
            except json.JSONDecodeError:
                return JSONResponse(
                    content={"error": "Invalid JSON in additional_context"},
                    status_code=400,
                )

        # Cast to Literal type after validation
        from typing import Literal, cast

        validated_context_type = cast(
            Literal["course_outline", "lesson_plan"], context_type
        )
        enhanced = await prompt_enhancer(
            message,
            validated_context_type,
            context_dict,
            language,
            user_id=current_user["user_id"],
        )
        return JSONResponse(content={"enhanced_prompt": enhanced})

    except HTTPException:
        raise  # Let FastAPI handle 403/500 from _resolve_api_key directly
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


async def course_outline_event_generator(
    message: str,
    topic: Optional[str],
    number_of_classes: Optional[int],
    language: Optional[str],
    thread_id: Optional[str],
    file_contents: List[dict],
    user_id: str,
):
    """
    Generator function that yields Server-Sent Events (SSE) for structured output.
    Yields progress updates and the final structured course outline.

    When DebugConfig.USE_DUMMY_GRAPH is True, uses a fast dummy generator
    that returns hardcoded data (no LLM calls).
    """
    try:
        # Pick the generator based on debug flag
        if DebugConfig.USE_DUMMY_GRAPH:
            generator = run_dummy_course_outline_generator(
                message, topic, number_of_classes, thread_id, file_contents, language
            )
        else:
            generator = run_course_outline_generator(
                message,
                topic,
                number_of_classes,
                thread_id,
                file_contents,
                language,
                user_id=user_id,
            )

        async for event in generator:
            if isinstance(event, dict):
                event_type = event.get("type", "data")

                if event_type == "thread_id":
                    # Send thread_id as a separate SSE event type
                    yield f"event: thread_id\ndata: {json.dumps({'thread_id': event['thread_id']})}\n\n"
                elif event_type == "progress":
                    # Send progress updates with translation key
                    progress_data = {
                        "message_key": event.get(
                            "message_key", event.get("message", "")
                        ),
                    }
                    # Include params if present (for dynamic translations)
                    if "params" in event:
                        progress_data["params"] = event["params"]
                    yield f"event: progress\ndata: {json.dumps(progress_data)}\n\n"
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
        logger.error(f"Course outline generation error: {e}", exc_info=True)
        error_payload = _classify_error(e)
        yield f"event: error\ndata: {json.dumps(error_payload)}\n\n"


@app.post("/course-outline-generator")
async def generate_course_outline(
    message: str = Form(""),
    topic: Optional[str] = Form(None),
    number_of_classes: Optional[int] = Form(None),
    language: Optional[str] = Form(None),
    thread_id: Optional[str] = Form(None),
    files: Optional[List[UploadFile]] = File(None),
    current_user: dict = Depends(get_current_user),
):
    """
    Handle course outline generation with structured output and optional file uploads.
    Returns a streaming SSE response with progress updates and structured data.

    For initial requests: topic, number_of_classes, and language are required.
    For follow-up requests (with thread_id): only message and files are needed.
    """
    file_contents = []

    # Process uploaded files if any
    if files:
        file_contents += await file_processor(files)

    # Validate that the user has an API key (fail-fast before streaming)
    _resolve_api_key(current_user)

    # Return SSE stream
    return StreamingResponse(
        course_outline_event_generator(
            message,
            topic,
            number_of_classes,
            language,
            thread_id,
            file_contents,
            user_id=current_user["user_id"],
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable buffering for nginx
        },
    )


async def lesson_plan_event_generator(
    message: str,
    course_title: Optional[str],
    class_number: Optional[int],
    class_title: Optional[str],
    learning_objectives: Optional[List[str]],
    key_topics: Optional[List[str]],
    activities_projects: Optional[List[str]],
    language: Optional[str],
    thread_id: Optional[str],
    file_contents: List[dict],
    user_id: str,
):
    """
    Generator function that yields Server-Sent Events (SSE) for lesson plan generation.
    Yields progress updates and the final structured lesson plan.
    """
    try:
        async for event in run_lesson_plan_generator(
            message,
            course_title,
            class_number,
            class_title,
            learning_objectives,
            key_topics,
            activities_projects,
            thread_id,
            file_contents,
            language,
            user_id=user_id,
        ):
            if isinstance(event, dict):
                event_type = event.get("type", "data")

                if event_type == "thread_id":
                    # Send thread_id as a separate SSE event type
                    yield f"event: thread_id\ndata: {json.dumps({'thread_id': event['thread_id']})}\n\n"
                elif event_type == "progress":
                    # Send progress updates with translation key
                    progress_data = {
                        "message_key": event.get(
                            "message_key", event.get("message", "")
                        ),
                    }
                    # Include params if present (for dynamic translations)
                    if "params" in event:
                        progress_data["params"] = event["params"]
                    yield f"event: progress\ndata: {json.dumps(progress_data)}\n\n"
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
        logger.error(f"Lesson plan generation error: {e}", exc_info=True)
        error_payload = _classify_error(e)
        yield f"event: error\ndata: {json.dumps(error_payload)}\n\n"


@app.post("/lesson-plan-generator")
async def generate_lesson_plan(
    message: str = Form(""),
    course_title: Optional[str] = Form(None),
    class_number: Optional[int] = Form(None),
    class_title: Optional[str] = Form(None),
    learning_objectives: Optional[str] = Form(None),  # JSON string
    key_topics: Optional[str] = Form(None),  # JSON string
    activities_projects: Optional[str] = Form(None),  # JSON string
    language: Optional[str] = Form(None),
    thread_id: Optional[str] = Form(None),
    files: Optional[List[UploadFile]] = File(None),
    current_user: dict = Depends(get_current_user),
):
    """
    Handle lesson plan generation with structured output and optional file uploads.
    Returns a streaming SSE response with progress updates and structured data.

    For initial requests: all lesson plan parameters are required.
    For follow-up requests (with thread_id): only message and files are needed.
    """
    try:
        # Parse JSON strings to lists only if they are provided
        learning_objectives_list = (
            json.loads(learning_objectives) if learning_objectives else None
        )
        key_topics_list = json.loads(key_topics) if key_topics else None
        activities_projects_list = (
            json.loads(activities_projects) if activities_projects else None
        )
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid JSON in form fields: {str(e)}"
        )

    file_contents = []

    # Process uploaded files if any
    if files:
        file_contents += await file_processor(files)

    # Validate that the user has an API key (fail-fast before streaming)
    _resolve_api_key(current_user)

    # Return SSE stream
    return StreamingResponse(
        lesson_plan_event_generator(
            message,
            course_title,
            class_number,
            class_title,
            learning_objectives_list,
            key_topics_list,
            activities_projects_list,
            language,
            thread_id,
            file_contents,
            user_id=current_user["user_id"],
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable buffering for nginx
        },
    )


# ============================================================================
# Conversation Management Endpoints
# ============================================================================


@app.get("/conversations")
async def list_conversations(
    conversation_type: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
):
    """
    List all saved conversations for the current user with optional filtering by type.
    """
    try:
        conv_type = ConversationType(conversation_type) if conversation_type else None
        # Admin sees all conversations; regular users only their own
        effective_user_id = (
            None if current_user["role"] == "admin" else current_user["user_id"]
        )
        conversations = conversation_manager.list_conversations(
            user_id=effective_user_id,
            conversation_type=conv_type,
            limit=limit,
            offset=offset,
        )
        total = conversation_manager.count_conversations(
            user_id=effective_user_id,
            conversation_type=conv_type,
        )

        return ConversationList(conversations=conversations, total=total)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid conversation type")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/conversations/{thread_id}")
async def get_conversation(
    thread_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Get metadata for a specific conversation.
    Non-admin users can only access their own conversations.
    """
    conversation = conversation_manager.get_conversation(thread_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    # Ownership check: non-admin users can only access their own conversations
    if (
        current_user["role"] != "admin"
        and conversation.user_id != current_user["user_id"]
    ):
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@app.delete("/conversations/{thread_id}")
async def delete_conversation(
    thread_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Delete a conversation and its metadata.
    Also deletes associated RAG documents for this session.
    Note: The checkpoint data remains in checkpoints.db.
    Non-admin users can only delete their own conversations.
    """
    # Ownership check before deleting
    conversation = conversation_manager.get_conversation(thread_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if (
        current_user["role"] != "admin"
        and conversation.user_id != current_user["user_id"]
    ):
        raise HTTPException(status_code=404, detail="Conversation not found")

    deleted = conversation_manager.delete_conversation(thread_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Delete associated RAG documents for this session
    try:
        rag = get_rag_pipeline()
        chunks_deleted = rag.delete_session(thread_id)
        if chunks_deleted > 0:
            print(f"[RAG] Deleted {chunks_deleted} chunks for session {thread_id}")
    except Exception as e:
        # Log but don't fail the request if RAG cleanup fails
        print(f"[RAG] Warning: Failed to delete RAG session {thread_id}: {e}")

    return {"success": True, "message": "Conversation deleted"}


@app.get("/conversations/{thread_id}/history")
async def get_conversation_history(
    thread_id: str,
    current_user: dict = Depends(get_current_user),
):
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
        # Ownership check: non-admin users can only access their own conversations
        if (
            current_user["role"] != "admin"
            and conversation.user_id != current_user["user_id"]
        ):
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Connect to checkpoints database and retrieve history
        async with AsyncSqliteSaver.from_conn_string("checkpoints.db") as checkpointer:
            # Get the checkpoint for this thread
            config = {"configurable": {"thread_id": thread_id}}

            # Get the latest state
            checkpoint = await checkpointer.aget(config)  # type: ignore

            if not checkpoint:
                # No messages yet in this thread
                return {
                    "thread_id": thread_id,
                    "messages": [],
                    "metadata": conversation.model_dump(),
                }

            # Extract messages from checkpoint
            # LangGraph checkpoint objects have channel_values attribute
            messages = []

            # Get channel_values from the checkpoint
            channel_values = {}
            if hasattr(checkpoint, "channel_values"):
                channel_values = checkpoint.channel_values  # type: ignore
            elif isinstance(checkpoint, dict) and "channel_values" in checkpoint:
                channel_values = checkpoint["channel_values"]  # type: ignore
            elif isinstance(checkpoint, dict):
                channel_values = checkpoint  # type: ignore

            if "messages" in channel_values:  # type: ignore
                raw_messages = channel_values["messages"]  # type: ignore

                # Handle both single message and list of messages
                if not isinstance(raw_messages, list):
                    raw_messages = [raw_messages]

                # Keep track of whether we have a structured response
                # Course outline generator uses 'final_response', lesson plan uses 'structured_response'
                final_response = channel_values.get("final_response") or channel_values.get("structured_response")  # type: ignore

                # Count assistant messages to know which is the last one
                assistant_indices = []
                for i, msg in enumerate(raw_messages):
                    if hasattr(msg, "__class__"):
                        class_name = msg.__class__.__name__  # type: ignore
                        if "AI" in class_name or "Assistant" in class_name:
                            assistant_indices.append(i)
                    elif hasattr(msg, "type") and str(getattr(msg, "type", "")) == "ai":
                        assistant_indices.append(i)

                last_assistant_idx = assistant_indices[-1] if assistant_indices else -1

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
                        elif "System" in class_name:
                            # Skip system messages - they are internal prompts
                            continue
                    elif hasattr(msg, "type"):
                        msg_type = str(getattr(msg, "type", ""))
                        if msg_type == "tool":
                            continue
                        if msg_type == "system":
                            continue
                        role = "user" if msg_type == "human" else "assistant"
                    elif isinstance(msg, dict) and "role" in msg:  # type: ignore
                        if msg["role"] == "system":  # type: ignore
                            continue
                        role = str(msg["role"])  # type: ignore

                    # For the LAST assistant message, use final_response if available
                    # For other messages (user or earlier assistant), use the message content
                    if (
                        role == "assistant"
                        and final_response
                        and i == last_assistant_idx
                    ):
                        # Return the final response as JSON for the last assistant message
                        import json

                        content = json.dumps(final_response.model_dump() if hasattr(final_response, "model_dump") else final_response)  # type: ignore
                    else:
                        # LangChain message objects have a content attribute
                        if hasattr(msg, "content"):
                            content = str(msg.content)  # type: ignore
                        elif isinstance(msg, dict) and "content" in msg:  # type: ignore
                            content = str(msg["content"])  # type: ignore
                        else:
                            content = str(msg)

                    messages.append({"role": role, "content": content})

            return {
                "thread_id": thread_id,
                "messages": messages,
                "metadata": conversation.model_dump(),
            }

    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve conversation history: {str(e)}"
        )
