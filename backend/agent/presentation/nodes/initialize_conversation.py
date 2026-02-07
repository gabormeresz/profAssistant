"""
Conversation initialization node for the presentation generation workflow.
"""

import logging

from schemas.conversation import (
    ConversationType,
    PresentationCreate,
    PresentationMetadata,
)
from services.conversation_manager import conversation_manager

from ..state import PresentationState

logger = logging.getLogger(__name__)


async def initialize_conversation(state: PresentationState) -> dict:
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
        class_title = state["class_title"]
        title = f"{class_title[:50]}..." if len(class_title) > 50 else class_title

        await conversation_manager.create_presentation(
            thread_id=thread_id,
            user_id=state["user_id"],
            conversation_type=ConversationType.PRESENTATION,
            data=PresentationCreate(
                title=title,
                course_title=state["course_title"],
                class_number=state["class_number"],
                class_title=state["class_title"],
                learning_objective=state.get("learning_objective"),
                key_points=state.get("key_points", []),
                lesson_breakdown=state.get("lesson_breakdown"),
                activities=state.get("activities"),
                homework=state.get("homework"),
                extra_activities=state.get("extra_activities"),
                language=state["language"],
                user_comment=(
                    state.get("message")
                    if (state.get("message") or "").strip()
                    else None
                ),
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
        if conversation and isinstance(conversation, PresentationMetadata):
            return {
                "thread_id": thread_id,
                "is_first_call": is_first_call,
                "language": conversation.language,
                "course_title": conversation.course_title,
                "class_number": conversation.class_number,
                "class_title": conversation.class_title,
                "learning_objective": conversation.learning_objective,
                "key_points": conversation.key_points,
                "lesson_breakdown": conversation.lesson_breakdown,
                "activities": conversation.activities,
                "homework": conversation.homework,
                "extra_activities": conversation.extra_activities,
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
