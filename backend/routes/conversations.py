"""
Conversation management API routes: list, get, delete, and history.

All endpoints are mounted under the root prefix in ``main.py``.
"""

import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from schemas.conversation import ConversationType, ConversationList
from services.auth_service import get_current_user
from services.conversation_manager import conversation_manager
from services.rag_pipeline import get_rag_pipeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/conversations", tags=["Conversations"])


@router.get("")
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
        conversations = await conversation_manager.list_conversations(
            user_id=effective_user_id,
            conversation_type=conv_type,
            limit=limit,
            offset=offset,
        )
        total = await conversation_manager.count_conversations(
            user_id=effective_user_id,
            conversation_type=conv_type,
        )

        return ConversationList(conversations=conversations, total=total)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid conversation type")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{thread_id}")
async def get_conversation(
    thread_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Get metadata for a specific conversation.
    Non-admin users can only access their own conversations.
    """
    conversation = await conversation_manager.get_conversation(thread_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if (
        current_user["role"] != "admin"
        and conversation.user_id != current_user["user_id"]
    ):
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.delete("/{thread_id}")
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
    conversation = await conversation_manager.get_conversation(thread_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if (
        current_user["role"] != "admin"
        and conversation.user_id != current_user["user_id"]
    ):
        raise HTTPException(status_code=404, detail="Conversation not found")

    deleted = await conversation_manager.delete_conversation(thread_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Delete associated RAG documents for this session
    try:
        rag = get_rag_pipeline()
        chunks_deleted = await rag.delete_session(thread_id)
        if chunks_deleted > 0:
            logger.info(f"Deleted {chunks_deleted} RAG chunks for session {thread_id}")
    except Exception as e:
        logger.warning(f"Failed to delete RAG session {thread_id}: {e}")

    return {"success": True, "message": "Conversation deleted"}


@router.get("/{thread_id}/history")
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
        conversation = await conversation_manager.get_conversation(thread_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        if (
            current_user["role"] != "admin"
            and conversation.user_id != current_user["user_id"]
        ):
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Connect to checkpoints database and retrieve history
        async with AsyncSqliteSaver.from_conn_string("checkpoints.db") as checkpointer:
            config = {"configurable": {"thread_id": thread_id}}
            checkpoint = await checkpointer.aget(config)  # type: ignore

            if not checkpoint:
                return {
                    "thread_id": thread_id,
                    "messages": [],
                    "metadata": conversation.model_dump(),
                }

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

                if not isinstance(raw_messages, list):
                    raw_messages = [raw_messages]

                # Course outline generator uses 'final_response', lesson plan uses 'structured_response'
                final_response = channel_values.get("final_response") or channel_values.get("structured_response")  # type: ignore

                # Find the last assistant message index
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
                    content = ""
                    role = "assistant"

                    # Determine role from LangChain message type
                    if hasattr(msg, "__class__"):
                        class_name = msg.__class__.__name__  # type: ignore
                        if "Human" in class_name or "User" in class_name:
                            role = "user"
                        elif "AI" in class_name or "Assistant" in class_name:
                            role = "assistant"
                        elif "Tool" in class_name:
                            continue
                        elif "System" in class_name:
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
                    if (
                        role == "assistant"
                        and final_response
                        and i == last_assistant_idx
                    ):
                        content = json.dumps(final_response.model_dump() if hasattr(final_response, "model_dump") else final_response)  # type: ignore
                    else:
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

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve conversation history: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve conversation history: {str(e)}"
        )
