"""
Message construction node for the presentation generation workflow.
"""

import logging

from langchain_core.messages import HumanMessage, SystemMessage

from agent.input_sanitizer import check_prompt_injection, wrap_user_input
from ..state import PresentationState
from ..prompts import get_system_prompt

logger = logging.getLogger(__name__)


def build_messages(state: PresentationState) -> dict:
    """
    Build messages for the agent.

    For first calls: Creates fresh system message and user prompt.
    For follow-ups: Preserves existing messages and appends new user message.

    Args:
        state: The current workflow state.

    Returns:
        Updated state with messages list.
    """
    is_first_call = state.get("is_first_call", True)
    user_message = state.get("message", "")

    logger.info(
        f"is_first_call={is_first_call}, "
        f"user_message='{user_message[:50] if user_message else ''}'"
    )
    logger.debug(f"existing messages count: {len(state.get('messages', []))}")

    if is_first_call:
        return _build_first_call_messages(state)
    else:
        return _build_follow_up_messages(state)


def _build_first_call_messages(state: PresentationState) -> dict:
    """
    Build messages for the first call (new conversation).

    Args:
        state: The current workflow state.

    Returns:
        Dict with messages list for state update.
    """
    messages = []

    # Add system message with document search instruction if documents are ingested
    has_ingested_documents = state.get("has_ingested_documents", False)
    system_prompt = get_system_prompt(state["language"], has_ingested_documents)
    messages.append(SystemMessage(content=system_prompt))

    # Build user message content with clear structure
    course_title = state["course_title"]
    class_number = state.get("class_number")
    class_title = state["class_title"]
    learning_objective = state.get("learning_objective") or ""
    key_points = state.get("key_points", [])
    lesson_breakdown = state.get("lesson_breakdown") or ""
    activities = state.get("activities") or ""
    homework = state.get("homework") or ""
    extra_activities = state.get("extra_activities") or ""

    # Format key points
    key_points_str = (
        "\n".join(f"  - {kp}" for kp in key_points)
        if key_points
        else "  (none provided)"
    )

    user_msg = state.get("message") or ""

    # Pre-screen user input for prompt injection attempts
    if user_msg.strip() and check_prompt_injection(user_msg):
        logger.warning("Prompt injection pattern detected in presentation request")

    # Build user input block and wrap in XML delimiters
    user_input_block = f"""Course Title: {course_title}
Class Title: {class_title}"""

    if class_number is not None:
        user_input_block += f"\nClass Number: {class_number}"

    if learning_objective:
        user_input_block += f"\nLearning Objective: {learning_objective}"

    user_input_block += f"""
Key Points to Cover:
{key_points_str}"""

    if lesson_breakdown:
        user_input_block += f"\nLesson Breakdown (for reference):\n{lesson_breakdown}"

    if activities:
        user_input_block += f"\nActivities (for reference):\n{activities}"

    if homework:
        user_input_block += f"\nHomework:\n{homework}"

    if extra_activities:
        user_input_block += f"\nExtra Activities:\n{extra_activities}"

    if user_msg.strip():
        user_input_block += f"\nAdditional Instructions: {user_msg}"

    user_content = f"""## Presentation Request

{wrap_user_input(user_input_block)}

**Output Language:** {state['language']}

Please generate a complete educational presentation (5–15 slides) for this lesson.

Requirements:
- Start with a title/agenda slide and end with a summary/closing slide
- Cover every key point in the slides
- Provide speaker notes with explanations, examples, and transition cues
- Include at least one activity/practice slide with clear instructions
- Suggest visuals (diagrams, charts, images) where they would enhance understanding
- Keep bullet points concise and slide-friendly"""

    messages.append(HumanMessage(content=user_content))

    return {"messages": messages}


def _build_follow_up_messages(state: PresentationState) -> dict:
    """
    Build messages for follow-up calls (continuing conversation).

    Preserves existing messages and only appends new user message.
    The existing messages are loaded from checkpoint automatically by LangGraph.

    Args:
        state: The current workflow state.

    Returns:
        Dict with new messages to append to state.
    """
    new_messages = []

    # Check if new documents were uploaded with this follow-up
    has_ingested_documents = state.get("has_ingested_documents", False)
    file_contents = state.get("file_contents")
    has_new_documents = has_ingested_documents and file_contents

    user_message = state.get("message") or ""
    if user_message.strip() or has_new_documents:
        # Pre-screen follow-up input for injection attempts
        if user_message.strip() and check_prompt_injection(user_message):
            logger.warning("Prompt injection pattern detected in follow-up request")

        follow_up_content = "## Follow-up Request\n\n"

        if has_new_documents:
            follow_up_content += """**IMPORTANT: New documents have been uploaded with this request.**

You MUST use the `search_uploaded_documents` tool before responding to search through these new reference materials. Query with 2-3 different searches to extract relevant information, then incorporate the findings into your response.

"""

        if user_message.strip():
            follow_up_content += wrap_user_input(user_message)
        else:
            follow_up_content += (
                "Please incorporate the information from the newly "
                "uploaded documents into your response."
            )

        # Tag uploaded file names so the frontend can recover them on reload
        if file_contents:
            names = " | ".join(fc.get("filename", "unknown") for fc in file_contents)
            follow_up_content += f"\n\n[uploaded_files: {names}]"

        new_messages.append(HumanMessage(content=follow_up_content))

    logger.debug(f"returning {len(new_messages)} new messages")
    logger.info(f"has_new_documents={has_new_documents}")
    if new_messages:
        logger.debug(f"new message content: {new_messages[0].content[:100]}")

    return {"messages": new_messages}
