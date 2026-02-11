"""
Conversation initialization node for the assessment generation workflow.
"""

import json
import logging

from schemas.conversation import (
    ConversationType,
    AssessmentCreate,
    AssessmentMetadata,
)
from services.conversation_manager import conversation_manager

from ..state import AssessmentState

logger = logging.getLogger(__name__)


async def initialize_conversation(state: AssessmentState) -> dict:
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
        course_title = state["course_title"]
        assessment_type = state.get("assessment_type", "quiz")
        title = f"{assessment_type.capitalize()}: {course_title[:40]}..."
        if len(course_title) <= 40:
            title = f"{assessment_type.capitalize()}: {course_title}"

        # Extract file names from uploaded file contents
        file_contents = state.get("file_contents") or []
        uploaded_file_names = [
            fc["filename"] for fc in file_contents if fc.get("filename")
        ]

        await conversation_manager.create_assessment(
            thread_id=thread_id,
            user_id=state["user_id"],
            conversation_type=ConversationType.ASSESSMENT,
            data=AssessmentCreate(
                title=title,
                course_title=state["course_title"],
                class_title=state.get("class_title"),
                key_topics=state.get("key_topics", []),
                assessment_type=state.get("assessment_type", "quiz"),
                difficulty_level=state.get("difficulty_level", "mixed"),
                question_type_configs=json.dumps(
                    state.get("question_type_configs", [])
                ),
                language=state["language"],
                user_comment=(
                    state.get("additional_instructions")
                    if (state.get("additional_instructions") or "").strip()
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
        if conversation and isinstance(conversation, AssessmentMetadata):
            # Parse question_type_configs back from JSON string
            qtc = conversation.question_type_configs
            if isinstance(qtc, str):
                try:
                    qtc = json.loads(qtc)
                except (json.JSONDecodeError, TypeError):
                    qtc = []

            return {
                "thread_id": thread_id,
                "is_first_call": is_first_call,
                "language": conversation.language,
                "course_title": conversation.course_title,
                "class_title": conversation.class_title,
                "key_topics": conversation.key_topics,
                "assessment_type": conversation.assessment_type,
                "difficulty_level": conversation.difficulty_level,
                "question_type_configs": qtc,
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
