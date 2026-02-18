"""
Generation API routes: prompt enhancement, course-outline SSE,
and lesson-plan SSE.

All endpoints are mounted under the root prefix in ``main.py``.
"""

import asyncio
import json
import logging
import time
from typing import AsyncIterator, List, Optional

from fastapi import (
    APIRouter,
    Body,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    UploadFile,
)
from fastapi.responses import JSONResponse, Response, StreamingResponse

from agent.course_outline import run_course_outline_generator
from agent.course_outline.dummy_generator import run_dummy_course_outline_generator
from agent.lesson_plan import run_lesson_plan_generator
from agent.presentation import run_presentation_generator
from agent.assessment import run_assessment_generator
from agent.prompt_enhancer import prompt_enhancer
from config import DebugConfig
from schemas.presentation import Presentation as PresentationSchema
from services.auth_service import get_current_user
from services.pptx_service import generate_pptx
from utils.api_helpers import resolve_api_key, classify_error, validate_thread_ownership
from rate_limit import limiter
from utils.file_processor import file_processor
from utils.sse import format_sse_event, format_sse_error

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Generation"])

# ---------------------------------------------------------------------------
# Per-user concurrent generation limiter
# ---------------------------------------------------------------------------
# Tracks active SSE generation streams per user to prevent a single user from
# spawning many parallel generations (each costing 7+ LLM calls).
# Timestamps are stored instead of a plain counter so that slots auto-expire
# after MAX_GENERATION_DURATION_SECONDS — this guards against a stuck counter
# if a generator hangs and its ``finally`` block never executes.

_active_generations: dict[str, list[float]] = {}
_active_generations_lock = asyncio.Lock()
MAX_CONCURRENT_GENERATIONS = 2
MAX_GENERATION_DURATION_SECONDS = 600  # 10 min auto-expiry


async def _acquire_generation_slot(user_id: str) -> None:
    """Reserve a generation slot or raise HTTP 429."""
    async with _active_generations_lock:
        now = time.monotonic()
        # Evict expired entries so a stuck counter never blocks a user forever
        _active_generations[user_id] = [
            t
            for t in _active_generations.get(user_id, [])
            if now - t < MAX_GENERATION_DURATION_SECONDS
        ]
        if len(_active_generations[user_id]) >= MAX_CONCURRENT_GENERATIONS:
            raise HTTPException(
                status_code=429,
                detail="Too many concurrent generation requests",
            )
        _active_generations[user_id].append(now)


async def _release_generation_slot(user_id: str, start_time: float) -> None:
    """Release the exact slot identified by *start_time*."""
    async with _active_generations_lock:
        slots = _active_generations.get(user_id, [])
        try:
            slots.remove(start_time)
        except ValueError:
            pass  # already expired / removed


async def _guarded_sse_stream(
    user_id: str,
    inner: AsyncIterator[str],
) -> AsyncIterator[str]:
    """Wrap an SSE event generator with concurrency tracking."""
    await _acquire_generation_slot(user_id)
    start_time = _active_generations[user_id][-1]
    try:
        async for event in inner:
            yield event
    finally:
        await _release_generation_slot(user_id, start_time)


# ============================================================================
# Prompt enhancement
# ============================================================================


@router.post("/enhance-prompt")
@limiter.limit("10/minute")
async def enhance_prompt(
    request: Request,
    message: str = Form(..., max_length=5000),
    context_type: str = Form("course_outline", max_length=50),
    additional_context: Optional[str] = Form(None, max_length=10000),
    language: Optional[str] = Form(None, max_length=50),
    current_user: dict = Depends(get_current_user),
):
    """
    Enhance the user's prompt to provide better instructions for educational content generation.

    Args:
        message: The user's message/instructions to enhance
        context_type: Type of content being generated
            ("course_outline", "lesson_plan", "presentation", or "assessment")
        additional_context: JSON string with context-specific fields:
            - For course_outline: topic, num_classes
            - For lesson_plan: topic, class_title, learning_objectives, key_topics, activities_projects
            - For presentation: course_title, class_title, learning_objective, key_points
            - For assessment: (TBD)
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
        valid_contexts = ["course_outline", "lesson_plan", "presentation", "assessment"]
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
            Literal["course_outline", "lesson_plan", "presentation", "assessment"],
            context_type,
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
        logger.error("Prompt enhancement failed: %s", e, exc_info=True)
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)


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
@limiter.limit("10/minute")
async def generate_course_outline(
    request: Request,
    message: str = Form("", max_length=5000),
    topic: Optional[str] = Form(None, max_length=500),
    number_of_classes: Optional[int] = Form(None),
    language: Optional[str] = Form(None, max_length=50),
    thread_id: Optional[str] = Form(None, max_length=100),
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

    # Validate thread ownership for follow-up requests (fail-fast before streaming)
    await validate_thread_ownership(thread_id, current_user)

    # Validate that the user has an API key (fail-fast before streaming)
    await resolve_api_key(current_user)

    user_id = current_user["user_id"]

    return StreamingResponse(
        _guarded_sse_stream(
            user_id,
            _course_outline_event_generator(
                message,
                topic,
                number_of_classes,
                language,
                thread_id,
                file_contents,
                user_id=user_id,
            ),
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
@limiter.limit("10/minute")
async def generate_lesson_plan(
    request: Request,
    message: str = Form("", max_length=5000),
    course_title: Optional[str] = Form(None, max_length=500),
    class_number: Optional[int] = Form(None),
    class_title: Optional[str] = Form(None, max_length=500),
    learning_objectives: Optional[str] = Form(None, max_length=5000),  # JSON string
    key_topics: Optional[str] = Form(None, max_length=5000),  # JSON string
    activities_projects: Optional[str] = Form(None, max_length=5000),  # JSON string
    language: Optional[str] = Form(None, max_length=50),
    thread_id: Optional[str] = Form(None, max_length=100),
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
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in form fields")

    file_contents = []

    if files:
        file_contents += await file_processor(files)

    # Validate thread ownership for follow-up requests (fail-fast before streaming)
    await validate_thread_ownership(thread_id, current_user)

    # Validate that the user has an API key (fail-fast before streaming)
    await resolve_api_key(current_user)

    user_id = current_user["user_id"]

    return StreamingResponse(
        _guarded_sse_stream(
            user_id,
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
                user_id=user_id,
            ),
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
@limiter.limit("10/minute")
async def generate_presentation(
    request: Request,
    message: str = Form("", max_length=5000),
    course_title: Optional[str] = Form(None, max_length=500),
    class_number: Optional[int] = Form(None),
    class_title: Optional[str] = Form(None, max_length=500),
    learning_objective: Optional[str] = Form(None, max_length=2000),
    key_points: Optional[str] = Form(None, max_length=5000),  # JSON string
    lesson_breakdown: Optional[str] = Form(None, max_length=5000),
    activities: Optional[str] = Form(None, max_length=5000),
    homework: Optional[str] = Form(None, max_length=5000),
    extra_activities: Optional[str] = Form(None, max_length=5000),
    language: Optional[str] = Form(None, max_length=50),
    thread_id: Optional[str] = Form(None, max_length=100),
    files: Optional[List[UploadFile]] = File(None),
    current_user: dict = Depends(get_current_user),
):
    """
    Handle presentation generation with structured output and optional file uploads.
    Returns a streaming SSE response with progress updates and structured data.

    For initial requests: course_title, class_title, and language are required. class_number is optional.
    For follow-up requests (with thread_id): only message and files are needed.
    """
    try:
        key_points_list = json.loads(key_points) if key_points else None
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in key_points")

    file_contents = []

    if files:
        file_contents += await file_processor(files)

    # Validate thread ownership for follow-up requests (fail-fast before streaming)
    await validate_thread_ownership(thread_id, current_user)

    # Validate that the user has an API key (fail-fast before streaming)
    await resolve_api_key(current_user)

    user_id = current_user["user_id"]

    return StreamingResponse(
        _guarded_sse_stream(
            user_id,
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
                user_id=user_id,
            ),
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ============================================================================
# Assessment generation (SSE)
# ============================================================================


async def _assessment_event_generator(
    message: str,
    course_title: Optional[str],
    class_title: Optional[str],
    key_topics: Optional[List[str]],
    assessment_type: Optional[str],
    difficulty_level: Optional[str],
    question_type_configs: Optional[List[dict]],
    additional_instructions: Optional[str],
    language: Optional[str],
    thread_id: Optional[str],
    file_contents: List[dict],
    user_id: str,
):
    """
    Generator function that yields Server-Sent Events (SSE) for assessment generation.
    Yields progress updates and the final structured assessment.
    """
    try:
        async for event in run_assessment_generator(
            message,
            course_title,
            class_title,
            key_topics,
            assessment_type,
            difficulty_level,
            question_type_configs,
            additional_instructions,
            thread_id,
            file_contents,
            language,
            user_id=user_id,
        ):
            yield format_sse_event(event)
    except Exception as e:
        logger.error(f"Assessment generation error: {e}", exc_info=True)
        yield format_sse_error(classify_error(e))


@router.post("/assessment-generator")
@limiter.limit("10/minute")
async def generate_assessment(
    request: Request,
    message: str = Form("", max_length=5000),
    course_title: Optional[str] = Form(None, max_length=500),
    class_title: Optional[str] = Form(None, max_length=500),
    key_topics: Optional[str] = Form(None, max_length=5000),  # JSON string
    assessment_type: Optional[str] = Form(None, max_length=50),
    difficulty_level: Optional[str] = Form(None, max_length=50),
    question_type_configs: Optional[str] = Form(None, max_length=5000),  # JSON string
    additional_instructions: Optional[str] = Form(None, max_length=5000),
    language: Optional[str] = Form(None, max_length=50),
    thread_id: Optional[str] = Form(None, max_length=100),
    files: Optional[List[UploadFile]] = File(None),
    current_user: dict = Depends(get_current_user),
):
    """
    Handle assessment generation with structured output and optional file uploads.
    Returns a streaming SSE response with progress updates and structured data.

    For initial requests: course_title, key_topics, assessment_type, and language are required.
    For follow-up requests (with thread_id): only message and files are needed.
    """
    try:
        key_topics_list = json.loads(key_topics) if key_topics else None
        question_type_configs_list = (
            json.loads(question_type_configs) if question_type_configs else None
        )
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in form fields")

    # Validate assessment_type and difficulty_level against allowed enums
    if assessment_type is not None:
        from schemas.assessment import validate_assessment_type

        try:
            validate_assessment_type(assessment_type)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    if difficulty_level is not None:
        from schemas.assessment import validate_difficulty_level

        try:
            validate_difficulty_level(difficulty_level)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    # Validate question_type_configs with Pydantic schema
    if question_type_configs_list is not None:
        from schemas.assessment import validate_question_type_configs

        try:
            question_type_configs_list = validate_question_type_configs(
                question_type_configs_list
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    file_contents = []

    if files:
        file_contents += await file_processor(files)

    # Validate thread ownership for follow-up requests (fail-fast before streaming)
    await validate_thread_ownership(thread_id, current_user)

    # Validate that the user has an API key (fail-fast before streaming)
    await resolve_api_key(current_user)

    user_id = current_user["user_id"]

    return StreamingResponse(
        _guarded_sse_stream(
            user_id,
            _assessment_event_generator(
                message,
                course_title,
                class_title,
                key_topics_list,
                assessment_type,
                difficulty_level,
                question_type_configs_list,
                additional_instructions,
                language,
                thread_id,
                file_contents,
                user_id=user_id,
            ),
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
    language: str = Query(default="en"),
    current_user: dict = Depends(get_current_user),
):
    """
    Accept a Presentation JSON payload and return a .pptx file.
    """
    try:
        pptx_bytes = generate_pptx(presentation, language=language)

        safe_title = (
            presentation.lesson_title.replace(" ", "_").replace("/", "-").lower()[:60]
        )
        class_num_part = f"_class_{presentation.class_number}" if presentation.class_number is not None else ""
        filename = f"presentation{class_num_part}_{safe_title}.pptx"

        # Use ASCII-safe fallback + RFC 5987 filename* for Unicode support
        from urllib.parse import quote

        ascii_fallback = f"presentation{class_num_part}.pptx"
        encoded_filename = quote(filename)
        content_disposition = (
            f'attachment; filename="{ascii_fallback}"; '
            f"filename*=UTF-8''{encoded_filename}"
        )

        return Response(
            content=pptx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            headers={"Content-Disposition": content_disposition},
        )
    except Exception as e:
        logger.error("PPTX export error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate PPTX")
