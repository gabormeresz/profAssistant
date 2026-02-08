from typing import Optional, Dict, Any, List, Literal

from langchain_core.messages import HumanMessage, SystemMessage

from agent.model import get_model


def _build_system_prompt(language: Optional[str], context_text: str) -> str:
    """Build system prompt with language instruction and context if provided."""
    base_prompt = (
        "You are an expert prompt engineer specializing in **Higher Education (University-level)** content.\n"
        "Your task: Transform the user's basic prompt into a clear, specific, and effective instruction.\n\n"
        "## Rules\n"
        "1. **Enhance, don't change intent**: Preserve what the user wants, just make it clearer\n"
        "2. **Be specific**: Replace vague words with concrete requirements\n"
        "3. **Add structure hints**: Suggest focus areas or emphasis without changing the topic\n"
        "4. **Keep it concise**: Use bullet points or short phrases, not paragraphs\n"
        "5. **No external context**: Do NOT include topic, class title, or objectives from the context below\n\n"
        "## What makes a good enhanced prompt:\n"
        "- Specifies desired emphasis or focus areas\n"
        "- Mentions relevant pedagogical approaches (if applicable)\n"
        "- Clarifies ambiguous terms from the original\n"
        "- Adds relevant constraints or preferences\n\n"
        "## Examples:\n"
        "Original: 'make it practical'\n"
        "Enhanced: 'emphasize hands-on exercises, include real-world examples, minimize theory'\n\n"
        "Original: 'beginner friendly'\n"
        "Enhanced: 'use simple terminology, include prerequisite review, add step-by-step explanations'\n\n"
        "Original: 'focus on coding'\n"
        "Enhanced: 'prioritize code examples over theory, include debugging tips, hands-on programming exercises each class'\n\n"
    )

    if language:
        base_prompt += (
            f"## Language Requirement\nWrite the enhanced prompt in {language}.\n\n"
        )

    base_prompt += (
        "## Output Format\n"
        "Output ONLY the enhanced prompt. No explanations, headers, or additional text.\n\n"
        f"## Context (for understanding only - do NOT include in output):\n{context_text}\n"
    )

    return base_prompt


def _build_context_text(context_type: str, additional_context: Dict[str, Any]) -> str:
    """Build context text based on context type."""
    if context_type == "lesson_plan":
        return (
            f"Topic: {additional_context.get('topic', 'N/A')}, "
            f"Class Title: {additional_context.get('class_title', 'N/A')}, "
            f"Learning Objectives: {additional_context.get('learning_objectives', [])}, "
            f"Key Topics: {additional_context.get('key_topics', [])}, "
            f"Activities/Projects: {additional_context.get('activities_projects', [])}"
        )
    elif context_type == "presentation":
        return (
            f"Course Title: {additional_context.get('course_title', 'N/A')}, "
            f"Class Title: {additional_context.get('class_title', 'N/A')}, "
            f"Learning Objective: {additional_context.get('learning_objective', 'N/A')}, "
            f"Key Points: {additional_context.get('key_points', [])}"
        )
    else:  # course_outline
        return (
            f"Topic: {additional_context.get('topic', 'N/A')}, "
            f"Number of Classes: {additional_context.get('num_classes', 'N/A')}"
        )


def _build_user_message(message: str, context_type: str) -> str:
    """Build the user message for prompt enhancement."""
    type_map = {
        "lesson_plan": "detailed lesson plan",
        "presentation": "educational presentation",
        "course_outline": "course outline",
    }
    content_type = type_map.get(context_type, "course outline")
    return (
        f"My initial prompt is: '''{message}'''.\n"
        f"Please refine it into a clearer, richer, and more effective instruction for generating a {content_type}. "
        "Do not include any context details in your output."
    )


def _build_messages(
    message: str, context_type: str, context_text: str, language: Optional[str]
) -> List:
    """Build the messages array for the LLM call."""
    return [
        SystemMessage(content=_build_system_prompt(language, context_text)),
        HumanMessage(content=_build_user_message(message, context_type)),
    ]


async def prompt_enhancer(
    message: str,
    context_type: Literal[
        "course_outline", "lesson_plan", "presentation"
    ] = "course_outline",
    additional_context: Optional[Dict[str, Any]] = None,
    language: Optional[str] = None,
    user_id: Optional[str] = None,
) -> str:
    """
    Enhance the user prompt with additional context.

    Args:
        message: The main user message/prompt
        context_type: Type of content being generated ("course_outline" or "lesson_plan")
        additional_context: Optional dict with context-specific fields:
            - For course_outline: topic, num_classes
            - For lesson_plan: topic (course_title), class_title, learning_objectives,
              key_topics, activities_projects
        language: Optional language for the output (e.g., "English", "Hungarian")
        user_id: Optional user ID. Resolves the per-user API key via api_key_service.

    Returns:
        Enhanced prompt string

    Raises:
        Exception: If enhancement fails
    """
    additional_context = additional_context or {}

    context_text = _build_context_text(context_type, additional_context)
    messages = _build_messages(message, context_type, context_text, language)

    # Resolve per-user API key via the centralised service.
    # Always use the default model (gpt-4o-mini) for prompt enhancement
    # regardless of the user's preferred model.
    from services.api_key_service import resolve_user_llm_config

    if user_id:
        api_key, _ = await resolve_user_llm_config(user_id)
    else:
        api_key = None

    model = get_model(
        api_key=api_key,
        purpose="enhancer",
    )
    response = await model.ainvoke(messages)

    enhanced = response.content if hasattr(response, "content") else None

    if not enhanced:
        raise Exception("Failed to enhance prompt")

    return str(enhanced).strip()
