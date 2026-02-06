"""
Conversation initialization node for the lesson plan generation workflow.
"""

import logging

from schemas.conversation import (
    ConversationType,
    LessonPlanCreate,
    LessonPlanMetadata,
)
from services.conversation_manager import conversation_manager

from ..state import LessonPlanState

logger = logging.getLogger(__name__)


def initialize_conversation(state: LessonPlanState) -> dict:
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

        conversation_manager.create_lesson_plan(
            thread_id=thread_id,
            user_id=state["user_id"],
            conversation_type=ConversationType.LESSON_PLAN,
            data=LessonPlanCreate(
                title=title,
                course_title=state["course_title"],
                class_number=state["class_number"],
                class_title=state["class_title"],
                learning_objectives=state["learning_objectives"],
                key_topics=state["key_topics"],
                activities_projects=state["activities_projects"],
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
        conversation_manager.increment_message_count(thread_id)

        # Load parameters from saved conversation for follow-ups
        conversation = conversation_manager.get_conversation(thread_id)
        if conversation and isinstance(conversation, LessonPlanMetadata):
            return {
                "thread_id": thread_id,
                "is_first_call": is_first_call,
                "language": conversation.language,
                "course_title": conversation.course_title,
                "class_number": conversation.class_number,
                "class_title": conversation.class_title,
                "learning_objectives": conversation.learning_objectives,
                "key_topics": conversation.key_topics,
                "activities_projects": conversation.activities_projects,
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
