from typing import Optional, Dict, Any, List, Literal

from langchain_core.messages import HumanMessage, SystemMessage

from agent.input_sanitizer import check_prompt_injection, SYSTEM_PROMPT_INJECTION_GUARD
from agent.model import get_model
from config import LLMConfig


def _build_system_prompt(language: Optional[str], context_text: str) -> str:
    """Build system prompt with language instruction and context if provided."""
    base_prompt = (
        "You are an expert prompt engineer specializing in **Higher Education (University-level)** content.\n"
        "Your task: Transform the user's basic prompt into a clear, specific, and effective instruction "
        "while enriching it with relevant content suggestions.\n\n"
        "## Rules\n"
        "1. **Enhance, don't change intent**: Preserve what the user wants, just make it clearer\n"
        "2. **Ground in context**: The context below (topic, course title, objectives) defines the course's "
        "domain. All enrichment MUST stay within this domain. The user's input is an instruction within "
        "this context — not a standalone topic\n"
        "3. **Be specific**: Replace vague words with concrete requirements\n"
        "4. **Enrich with content ideas**: Suggest concrete subtopics, concepts, or areas that fit "
        "both the user's input AND the course context. Only suggest ideas that naturally "
        "belong to the course domain\n"
        "5. **Add structure hints**: Suggest focus areas or emphasis without changing the topic\n"
        "6. **Keep it concise**: Use bullet points or short phrases, not paragraphs\n"
        "7. **Don't repeat context verbatim**: Use the context to guide your suggestions, "
        "but don't just copy field names or values into the output\n\n"
        "## What makes a good enhanced prompt:\n"
        "- Specifies desired emphasis or focus areas\n"
        "- Suggests relevant subtopics or concepts the user may not have mentioned explicitly\n"
        "- Mentions relevant pedagogical approaches (if applicable)\n"
        "- Clarifies ambiguous terms from the original\n"
        "- Adds relevant constraints or preferences\n\n"
        "## Examples:\n"
        "Original: make it practical\n"
        "Enhanced: emphasize hands-on exercises, include real-world examples, minimize theory\n\n"
        "Original: beginner friendly\n"
        "Enhanced: use simple terminology, include prerequisite review, add step-by-step explanations\n\n"
        "Original: focus on coding\n"
        "Enhanced: prioritize code examples over theory, include debugging tips, hands-on programming exercises each class\n\n"
        "Original: python basics (Context: Python programozás course)\n"
        "Enhanced: cover core Python fundamentals including variables and data types, control flow (loops, conditionals), "
        "functions and scope, basic data structures (lists, dicts, tuples), file I/O, and error handling; "
        "include practical coding exercises for each concept\n\n"
        "Original: from basics to AI (Context: Python programozás course, 4 classes)\n"
        "Enhanced: start with Python fundamentals (syntax, data types, control flow), progress through "
        "data manipulation with pandas/numpy, introduce ML basics using scikit-learn (model training, evaluation), "
        "and conclude with building a simple AI application in Python; include hands-on coding labs and "
        "a mini-project\n\n"
        "Original: intro to machine learning (Context: Data Science course)\n"
        "Enhanced: introduce supervised vs unsupervised learning, cover key algorithms (linear regression, decision trees, k-NN), "
        "explain train/test splits and evaluation metrics, include hands-on examples with real datasets\n\n"
    )

    if language:
        base_prompt += (
            f"## Language Requirement\nWrite the enhanced prompt in {language}.\n\n"
        )

    base_prompt += (
        "## Output Format\n"
        "Output ONLY the enhanced prompt as plain text. No explanations, headers, quotes, or additional text. "
        "Do NOT wrap the output in quotation marks.\n\n"
        f"## Course Context (use this to guide and ground your enrichment):\n{context_text}\n"
    )

    base_prompt += SYSTEM_PROMPT_INJECTION_GUARD

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
    elif context_type == "assessment":
        # TODO: Revise context fields once the assessment schema is finalized
        return (
            f"Course Title: {additional_context.get('course_title', 'N/A')}, "
            f"Class Title: {additional_context.get('class_title', 'N/A')}, "
            f"Learning Objectives: {additional_context.get('learning_objectives', [])}, "
            f"Key Topics: {additional_context.get('key_topics', [])}"
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
        "assessment": "student assessment or evaluation",
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
        "course_outline", "lesson_plan", "presentation", "assessment"
    ] = "course_outline",
    additional_context: Optional[Dict[str, Any]] = None,
    language: Optional[str] = None,
    user_id: Optional[str] = None,
) -> str:
    """
    Enhance the user prompt with additional context.

    Args:
        message: The main user message/prompt
        context_type: Type of content being generated
            ("course_outline", "lesson_plan", "presentation", or "assessment")
        additional_context: Optional dict with context-specific fields:
            - For course_outline: topic, num_classes
            - For lesson_plan: topic (course_title), class_title, learning_objectives,
              key_topics, activities_projects
            - For presentation: course_title, class_title, learning_objective, key_points
            - For assessment: (TBD)
        language: Optional language for the output (e.g., "English", "Hungarian")
        user_id: Optional user ID. Resolves the per-user API key via api_key_service.

    Returns:
        Enhanced prompt string

    Raises:
        Exception: If enhancement fails
    """
    additional_context = additional_context or {}

    # Pre-screen user input for prompt injection attempts
    if check_prompt_injection(message):
        import logging

        logging.getLogger(__name__).warning(
            "Prompt injection pattern detected in prompt enhancer input"
        )

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
        model_name=LLMConfig.ENHANCER_MODEL,
        purpose="enhancer",
    )
    response = await model.ainvoke(messages)

    enhanced = response.content if hasattr(response, "content") else None

    if not enhanced:
        raise Exception("Failed to enhance prompt")

    return str(enhanced).strip()
