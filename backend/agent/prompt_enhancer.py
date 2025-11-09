from openai import AsyncOpenAI
from typing import Optional, Dict, Any, List, Literal
from openai.types.chat import ChatCompletionMessageParam
import dotenv

dotenv.load_dotenv()

client = AsyncOpenAI()

# Constants
SYSTEM_PROMPT = (
    "You are a prompt refiner for educational content.\n"
    "Your task is to rewrite the user’s prompt to make it clearer and more effective.\n\n"
    "CRITICAL RULES:\n"
    "• You will be given extra context (topic, class title, objectives, etc.) only to understand the user’s intent.\n"
    "• You must NOT include or reference any of that context in the output unless it already appears in the user's original prompt.\n"
    "• Do NOT infer, assume, or restate the topic, class title, objectives, key topics, or activities.\n"
    "• Output only the refined prompt. No explanations or additional sentences.\n"
)


MODEL = "gpt-4o-mini"
TEMPERATURE = 0.5
MAX_TOKENS = 250


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
    else:  # course_outline
        return (
            f"Topic: {additional_context.get('topic', 'N/A')}, "
            f"Number of Classes: {additional_context.get('num_classes', 'N/A')}"
        )


def _build_user_message(message: str, context_type: str) -> str:
    """Build the user message for prompt enhancement."""
    content_type = (
        "detailed lesson plan" if context_type == "lesson_plan" else "course outline"
    )
    return (
        f"My initial prompt is: '''{message}'''. "
        f"Please refine it into a clearer and more effective instruction for generating a {content_type}. "
        "Do not include any context details in your output."
    )


def _build_messages(
    message: str, context_type: str, context_text: str
) -> List[ChatCompletionMessageParam]:
    """Build the messages array for the API call."""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "system",
            "content": f"Context for understanding only (do not include in output): {context_text}",
        },
        {"role": "user", "content": _build_user_message(message, context_type)},
    ]


async def prompt_enhancer(
    message: str,
    context_type: Literal["course_outline", "lesson_plan"] = "course_outline",
    additional_context: Optional[Dict[str, Any]] = None,
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

    Returns:
        Enhanced prompt string

    Raises:
        Exception: If enhancement fails
    """
    additional_context = additional_context or {}

    context_text = _build_context_text(context_type, additional_context)
    messages = _build_messages(message, context_type, context_text)

    response = await client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
    )

    enhanced = response.choices[0].message.content

    if not enhanced:
        raise Exception("Failed to enhance prompt")

    return enhanced.strip()
