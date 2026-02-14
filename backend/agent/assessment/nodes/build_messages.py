"""
Message construction node for the assessment generation workflow.
"""

import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage

from agent.input_sanitizer import check_prompt_injection, wrap_user_input
from ..state import AssessmentState
from ..prompts import get_system_prompt
from schemas.assessment import QUESTION_TYPE_LABELS

logger = logging.getLogger(__name__)


def build_messages(state: AssessmentState) -> dict:
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


def _build_first_call_messages(state: AssessmentState) -> dict:
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
    system_prompt = get_system_prompt(
        state["language"],
        has_ingested_documents,
        question_type_configs=state.get("question_type_configs", []),
    )
    messages.append(SystemMessage(content=system_prompt))

    # Build user message content with clear structure
    course_title = state["course_title"]
    class_title = state.get("class_title")
    key_topics = state.get("key_topics", [])
    assessment_type = state.get("assessment_type", "quiz")
    difficulty_level = state.get("difficulty_level", "mixed")
    question_type_configs = state.get("question_type_configs", [])

    # Format lists for display
    topics_str = "\n".join(f"  - {topic}" for topic in key_topics)

    # Format question type configuration
    qtc_lines = []
    total_questions = 0
    total_points = 0
    for config in question_type_configs:
        qt = config.get("question_type", "unknown")
        count = config.get("count", 0)
        pts_each = config.get("points_each", 5)
        total_questions += count
        total_points += count * pts_each
        label = QUESTION_TYPE_LABELS.get(qt, qt)
        qtc_lines.append(
            f"  - {label}: EXACTLY {count} questions, {pts_each} points each"
        )
    qtc_str = (
        "\n".join(qtc_lines) if qtc_lines else "  - (let AI decide the distribution)"
    )

    additional = state.get("additional_instructions") or state.get("message") or ""

    # Pre-screen user input for prompt injection attempts
    if additional.strip() and check_prompt_injection(additional):
        logger.warning("Prompt injection pattern detected in assessment request")

    # Wrap user-supplied fields in XML delimiters
    user_input_block = f"""Course Title: {course_title}
Assessment Type: {assessment_type}
Difficulty Level: {difficulty_level}"""

    if class_title:
        user_input_block += f"\nClass Title: {class_title}"

    user_input_block += f"""
Key Topics to Cover:
{topics_str}"""

    if additional.strip():
        user_input_block += f"\nAdditional Instructions: {additional}"

    user_content = f"""## Assessment Generation Request

**Output Language:** {state['language']}

{wrap_user_input(user_input_block)}

### ⚠️ REQUIRED Question Distribution (MANDATORY — follow exactly):
{qtc_str}
  **Total: {total_questions} questions, {total_points} points**

**STRICT RULES — You MUST obey all of these:**
1. Create ONLY the question types listed above — no other types allowed.
2. Generate EXACTLY the count specified for each type — no more, no less.
3. Each question MUST be worth exactly the points specified above for its type.
4. Create exactly one section per question type listed above.
5. Do NOT add any extra sections or question types beyond what is listed.
6. total_points MUST equal {total_points} (the sum of all question points).

Please generate a complete assessment following these constraints:
- Organize questions into sections matching the required distribution above
- Distribute points proportionally based on question difficulty
- Ensure questions cover all listed key topics
- Include an explanation for every question (for the answer key)
- Set appropriate point values and estimate realistic completion time
- Follow the difficulty level: {difficulty_level}"""

    messages.append(HumanMessage(content=user_content))

    return {"messages": messages}


def _build_follow_up_messages(state: AssessmentState) -> dict:
    """
    Build messages for follow-up calls (continuing conversation).

    Preserves existing messages and only appends new user message.

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

        new_messages.append(HumanMessage(content=follow_up_content))

    return {"messages": new_messages}
