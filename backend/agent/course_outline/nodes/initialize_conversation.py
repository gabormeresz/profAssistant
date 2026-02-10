"""
Conversation initialization node for the course outline generation workflow.
"""

import logging

from schemas.conversation import (
    ConversationType,
    CourseOutlineCreate,
    CourseOutlineMetadata,
)
from services.conversation_manager import conversation_manager

from ..state import CourseOutlineState

logger = logging.getLogger(__name__)


async def initialize_conversation(state: CourseOutlineState) -> dict:
    """
    Initialize or load conversation metadata.

    For first calls, creates a new conversation record.
    For follow-ups, increments the message count, loads existing metadata,
    and resets evaluation state for a fresh evaluation cycle.

    Args:
        state: The current workflow state.

    Returns:
        Updated state with thread_id, is_first_call flag, and reset evaluation state.
    """
    thread_id = state["thread_id"]
    is_first_call = state.get("is_first_call", True)

    if is_first_call:
        # Create new conversation record
        topic = state["topic"]
        title = f"{topic[:50]}..." if len(topic) > 50 else topic

        # Extract file names from uploaded file contents
        file_contents = state.get("file_contents") or []
        uploaded_file_names = [
            fc["filename"] for fc in file_contents if fc.get("filename")
        ]

        await conversation_manager.create_course_outline(
            thread_id=thread_id,
            user_id=state["user_id"],
            conversation_type=ConversationType.COURSE_OUTLINE,
            data=CourseOutlineCreate(
                title=title,
                topic=state["topic"],
                number_of_classes=state["number_of_classes"],
                language=state["language"],
                user_comment=(
                    state.get("message")
                    if (state.get("message") or "").strip()
                    else None
                ),
                uploaded_file_names=uploaded_file_names,
            ),
        )
        return {
            "thread_id": thread_id,
            "is_first_call": is_first_call,
            "evaluation_count": 0,
            "evaluation_history": [],
            "current_score": None,
        }
    else:
        # Update existing conversation
        await conversation_manager.increment_message_count(thread_id)

        # Load parameters from saved conversation for follow-ups
        conversation = await conversation_manager.get_conversation(thread_id)
        if conversation and isinstance(conversation, CourseOutlineMetadata):
            return {
                "thread_id": thread_id,
                "is_first_call": is_first_call,
                "language": conversation.language,
                "topic": conversation.topic,
                "number_of_classes": conversation.number_of_classes,
                # Reset evaluation state for fresh evaluation cycle
                "evaluation_count": 0,
                "evaluation_history": [],
                "current_score": None,
            }

        # Fallback if conversation not found
        return {
            "thread_id": thread_id,
            "is_first_call": is_first_call,
            "evaluation_count": 0,
            "evaluation_history": [],
            "current_score": None,
        }
