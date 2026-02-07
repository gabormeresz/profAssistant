"""
Generation API routes: prompt enhancement, course-outline SSE,
and lesson-plan SSE.

All endpoints are mounted under the root prefix in ``main.py``.
"""

import json
import logging
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse, Response, StreamingResponse

from agent.course_outline import run_course_outline_generator
from agent.course_outline.dummy_generator import run_dummy_course_outline_generator
from agent.lesson_plan import run_lesson_plan_generator
from agent.presentation import run_presentation_generator
from agent.prompt_enhancer import prompt_enhancer
from config import DebugConfig
from schemas.presentation import Presentation as PresentationSchema
from services.auth_service import get_current_user
from services.pptx_service import generate_pptx
from utils.api_helpers import resolve_api_key, classify_error
from utils.file_processor import file_processor
from utils.sse import format_sse_event, format_sse_error

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Generation"])


# ============================================================================
# Prompt enhancement
# ============================================================================


@router.post("/enhance-prompt")
async def enhance_prompt(
    message: str = Form(...),
    context_type: str = Form("course_outline"),
    additional_context: Optional[str] = Form(None),
    language: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user),
):
    """
    Enhance the user's prompt to provide better instructions for educational content generation.

    Args:
        message: The user's message/instructions to enhance
        context_type: Type of content being generated ("course_outline" or "lesson_plan")
        additional_context: JSON string with context-specific fields:
            - For course_outline: topic, num_classes
            - For lesson_plan: topic, class_title, learning_objectives, key_topics, activities_projects
        language: Optional language for the output (e.g., "English", "Hungarian")
    """
    try:
        if not message.strip():
            return JSONResponse(
                content={"error": "Message is required"}, status_code=400
            )

        # Resolve per-user API key
        await resolve_api_key(current_user)

        # Validate context_type
        valid_contexts = ["course_outline", "lesson_plan", "presentation"]
        if context_type not in valid_contexts:
            return JSONResponse(
                content={
                    "error": f"Invalid context_type. Must be one of: {', '.join(valid_contexts)}"
                },
                status_code=400,
            )

        # Parse additional_context if provided
        context_dict = None
        if additional_context:
            try:
                context_dict = json.loads(additional_context)
            except json.JSONDecodeError:
                return JSONResponse(
                    content={"error": "Invalid JSON in additional_context"},
                    status_code=400,
                )

        # Cast to Literal type after validation
        from typing import Literal, cast

        validated_context_type = cast(
            Literal["course_outline", "lesson_plan", "presentation"], context_type
        )
        enhanced = await prompt_enhancer(
            message,
            validated_context_type,
            context_dict,
            language,
            user_id=current_user["user_id"],
        )
        return JSONResponse(content={"enhanced_prompt": enhanced})

    except HTTPException:
        raise  # Let FastAPI handle 403/500 from resolve_api_key directly
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


# ============================================================================
# Course outline generation (SSE)
# ============================================================================


async def _course_outline_event_generator(
    message: str,
    topic: Optional[str],
    number_of_classes: Optional[int],
    language: Optional[str],
    thread_id: Optional[str],
    file_contents: List[dict],
    user_id: str,
):
    """
    Generator function that yields Server-Sent Events (SSE) for structured output.
    Yields progress updates and the final structured course outline.

    When DebugConfig.USE_DUMMY_GRAPH is True, uses a fast dummy generator
    that returns hardcoded data (no LLM calls).
    """
    try:
        # Pick the generator based on debug flag
        if DebugConfig.USE_DUMMY_GRAPH:
            generator = run_dummy_course_outline_generator(
                message, topic, number_of_classes, thread_id, file_contents, language
            )
        else:
            generator = run_course_outline_generator(
                message,
                topic,
                number_of_classes,
                thread_id,
                file_contents,
                language,
                user_id=user_id,
            )

        async for event in generator:
            yield format_sse_event(event)
    except Exception as e:
        logger.error(f"Course outline generation error: {e}", exc_info=True)
        yield format_sse_error(classify_error(e))


@router.post("/course-outline-generator")
async def generate_course_outline(
    message: str = Form(""),
    topic: Optional[str] = Form(None),
    number_of_classes: Optional[int] = Form(None),
    language: Optional[str] = Form(None),
    thread_id: Optional[str] = Form(None),
    files: Optional[List[UploadFile]] = File(None),
    current_user: dict = Depends(get_current_user),
):
    """
    Handle course outline generation with structured output and optional file uploads.
    Returns a streaming SSE response with progress updates and structured data.

    For initial requests: topic, number_of_classes, and language are required.
    For follow-up requests (with thread_id): only message and files are needed.
    """
    file_contents = []

    if files:
        file_contents += await file_processor(files)

    # Validate that the user has an API key (fail-fast before streaming)
    await resolve_api_key(current_user)

    return StreamingResponse(
        _course_outline_event_generator(
            message,
            topic,
            number_of_classes,
            language,
            thread_id,
            file_contents,
            user_id=current_user["user_id"],
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ============================================================================
# Lesson plan generation (SSE)
# ============================================================================


async def _lesson_plan_event_generator(
    message: str,
    course_title: Optional[str],
    class_number: Optional[int],
    class_title: Optional[str],
    learning_objectives: Optional[List[str]],
    key_topics: Optional[List[str]],
    activities_projects: Optional[List[str]],
    language: Optional[str],
    thread_id: Optional[str],
    file_contents: List[dict],
    user_id: str,
):
    """
    Generator function that yields Server-Sent Events (SSE) for lesson plan generation.
    Yields progress updates and the final structured lesson plan.
    """
    try:
        async for event in run_lesson_plan_generator(
            message,
            course_title,
            class_number,
            class_title,
            learning_objectives,
            key_topics,
            activities_projects,
            thread_id,
            file_contents,
            language,
            user_id=user_id,
        ):
            yield format_sse_event(event)
    except Exception as e:
        logger.error(f"Lesson plan generation error: {e}", exc_info=True)
        yield format_sse_error(classify_error(e))


@router.post("/lesson-plan-generator")
async def generate_lesson_plan(
    message: str = Form(""),
    course_title: Optional[str] = Form(None),
    class_number: Optional[int] = Form(None),
    class_title: Optional[str] = Form(None),
    learning_objectives: Optional[str] = Form(None),  # JSON string
    key_topics: Optional[str] = Form(None),  # JSON string
    activities_projects: Optional[str] = Form(None),  # JSON string
    language: Optional[str] = Form(None),
    thread_id: Optional[str] = Form(None),
    files: Optional[List[UploadFile]] = File(None),
    current_user: dict = Depends(get_current_user),
):
    """
    Handle lesson plan generation with structured output and optional file uploads.
    Returns a streaming SSE response with progress updates and structured data.

    For initial requests: all lesson plan parameters are required.
    For follow-up requests (with thread_id): only message and files are needed.
    """
    try:
        learning_objectives_list = (
            json.loads(learning_objectives) if learning_objectives else None
        )
        key_topics_list = json.loads(key_topics) if key_topics else None
        activities_projects_list = (
            json.loads(activities_projects) if activities_projects else None
        )
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid JSON in form fields: {str(e)}"
        )

    file_contents = []

    if files:
        file_contents += await file_processor(files)

    # Validate that the user has an API key (fail-fast before streaming)
    await resolve_api_key(current_user)

    return StreamingResponse(
        _lesson_plan_event_generator(
            message,
            course_title,
            class_number,
            class_title,
            learning_objectives_list,
            key_topics_list,
            activities_projects_list,
            language,
            thread_id,
            file_contents,
            user_id=current_user["user_id"],
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ============================================================================
# Presentation generation (SSE)
# ============================================================================


async def _presentation_event_generator(
    message: str,
    course_title: Optional[str],
    class_number: Optional[int],
    class_title: Optional[str],
    learning_objective: Optional[str],
    key_points: Optional[List[str]],
    lesson_breakdown: Optional[str],
    activities: Optional[str],
    homework: Optional[str],
    extra_activities: Optional[str],
    language: Optional[str],
    thread_id: Optional[str],
    file_contents: List[dict],
    user_id: str,
):
    """
    Generator function that yields Server-Sent Events (SSE) for presentation generation.
    Yields progress updates and the final structured presentation.
    """
    try:
        async for event in run_presentation_generator(
            message,
            course_title,
            class_number,
            class_title,
            learning_objective,
            key_points,
            lesson_breakdown,
            activities,
            homework,
            extra_activities,
            thread_id,
            file_contents,
            language,
            user_id=user_id,
        ):
            yield format_sse_event(event)
    except Exception as e:
        logger.error(f"Presentation generation error: {e}", exc_info=True)
        yield format_sse_error(classify_error(e))


@router.post("/presentation-generator")
async def generate_presentation(
    message: str = Form(""),
    course_title: Optional[str] = Form(None),
    class_number: Optional[int] = Form(None),
    class_title: Optional[str] = Form(None),
    learning_objective: Optional[str] = Form(None),
    key_points: Optional[str] = Form(None),  # JSON string
    lesson_breakdown: Optional[str] = Form(None),
    activities: Optional[str] = Form(None),
    homework: Optional[str] = Form(None),
    extra_activities: Optional[str] = Form(None),
    language: Optional[str] = Form(None),
    thread_id: Optional[str] = Form(None),
    files: Optional[List[UploadFile]] = File(None),
    current_user: dict = Depends(get_current_user),
):
    """
    Handle presentation generation with structured output and optional file uploads.
    Returns a streaming SSE response with progress updates and structured data.

    For initial requests: course_title, class_number, class_title, and language are required.
    For follow-up requests (with thread_id): only message and files are needed.
    """
    try:
        key_points_list = json.loads(key_points) if key_points else None
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid JSON in key_points: {str(e)}"
        )

    file_contents = []

    if files:
        file_contents += await file_processor(files)

    # Validate that the user has an API key (fail-fast before streaming)
    await resolve_api_key(current_user)

    return StreamingResponse(
        _presentation_event_generator(
            message,
            course_title,
            class_number,
            class_title,
            learning_objective,
            key_points_list,
            lesson_breakdown,
            activities,
            homework,
            extra_activities,
            language,
            thread_id,
            file_contents,
            user_id=current_user["user_id"],
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ============================================================================
# Presentation export to PPTX
# ============================================================================


@router.post("/export-presentation-pptx")
async def export_presentation_pptx(
    presentation: PresentationSchema = Body(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Accept a Presentation JSON payload and return a .pptx file.
    """
    try:
        pptx_bytes = generate_pptx(presentation)

        safe_title = (
            presentation.lesson_title.replace(" ", "_").replace("/", "-").lower()[:60]
        )
        filename = f"presentation_class_{presentation.class_number}_{safe_title}.pptx"

        return Response(
            content=pptx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as e:
        logger.error(f"PPTX export error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to generate PPTX: {str(e)}"
        )
