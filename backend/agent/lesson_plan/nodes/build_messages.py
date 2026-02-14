"""
Message construction node for the lesson plan generation workflow.
"""

import logging

from langchain_core.messages import HumanMessage, SystemMessage

from agent.input_sanitizer import check_prompt_injection, wrap_user_input
from ..state import LessonPlanState
from ..prompts import get_system_prompt

logger = logging.getLogger(__name__)


def build_messages(state: LessonPlanState) -> dict:
    """
    Build messages for the agent.

    For first calls: Creates fresh system message and user prompt.
    For follow-ups: Preserves existing messages and appends new user message.

    The messages from previous runs are automatically loaded from the
    checkpoint by LangGraph when using a checkpointer.

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


def _build_first_call_messages(state: LessonPlanState) -> dict:
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
    class_number = state["class_number"]
    class_title = state["class_title"]
    learning_objectives = state["learning_objectives"]
    key_topics = state["key_topics"]
    activities_projects = state["activities_projects"]

    # Format lists for display
    objectives_str = "\n".join(f"  - {obj}" for obj in learning_objectives)
    topics_str = "\n".join(f"  - {topic}" for topic in key_topics)
    activities_str = "\n".join(f"  - {act}" for act in activities_projects)

    user_message = state.get("message") or ""

    # Pre-screen user input for prompt injection attempts
    if user_message.strip() and check_prompt_injection(user_message):
        logger.warning("Prompt injection pattern detected in lesson plan request")

    # Wrap user-supplied fields in XML delimiters
    user_input_block = f"""Course Title: {course_title}
Class Number: {class_number}
Class Title: {class_title}
Learning Objectives:
{objectives_str}
Key Topics to Cover:
{topics_str}
Suggested Activities/Projects:
{activities_str}"""
    if user_message.strip():
        user_input_block += f"\nAdditional Instructions: {user_message}"

    user_content = f"""## Lesson Plan Request

{wrap_user_input(user_input_block)}

**Output Language:** {state['language']}

Please generate a complete, detailed lesson plan for this class.

Requirements:
- Create a clear lesson breakdown with opening, instruction, practice, and closing sections
- Design engaging activities with specific, step-by-step instructions
- Ensure all content directly supports the learning objectives
- Include meaningful homework and extension activities
- Identify the essential key points students must understand"""

    messages.append(HumanMessage(content=user_content))

    return {"messages": messages}


def _build_follow_up_messages(state: LessonPlanState) -> dict:
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

        # Build the follow-up content
        follow_up_content = "## Follow-up Request\n\n"

        # Add document search instruction if new documents were uploaded
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

    # Return new messages to be appended (MessagesState will handle accumulation)
    return {"messages": new_messages}
