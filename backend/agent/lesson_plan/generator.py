"""
Lesson plan generator entry point.

This module provides the main async generator function for lesson plan
generation, handling streaming progress updates and error management.
"""

import logging
import uuid
from typing import Any, Dict, List, AsyncGenerator

from langchain_core.runnables import RunnableConfig

logger = logging.getLogger(__name__)
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from config import DBConfig
from .graph import build_lesson_plan_graph
from .state import LessonPlanInput
from schemas.lesson_plan import LessonPlan


async def run_lesson_plan_generator(
    message: str,
    course_title: str | None = None,
    class_number: int | None = None,
    class_title: str | None = None,
    learning_objectives: List[str] | None = None,
    key_topics: List[str] | None = None,
    activities_projects: List[str] | None = None,
    thread_id: str | None = None,
    file_contents: List[Dict[str, str]] | None = None,
    language: str | None = None,
    user_id: str = "",
) -> AsyncGenerator[Dict, None]:
    """
    Run the lesson plan generator with streaming progress updates.

    This is the main entry point for lesson plan generation. It sets up
    the LangGraph workflow, streams events for progress tracking, and yields
    structured results.

    Args:
        message: The main user message/prompt (optional additional context).
        course_title: The title of the course (required for first call).
        class_number: The class number in the course (required for first call).
        class_title: The title of this class/lesson (required for first call).
        learning_objectives: List of learning objectives (required for first call).
        key_topics: List of key topics to cover (required for first call).
        activities_projects: List of activities/projects (required for first call).
        thread_id: Optional thread ID for conversation continuity.
        file_contents: Optional list of file contents with filename and content.
        language: Language for the generated content (required for first call).

    Yields:
        Progress updates, thread_id, and final structured data:
        - {"type": "thread_id", "thread_id": str}
        - {"type": "progress", "message_key": str, "params": dict}
        - {"type": "complete", "data": dict}
        - {"type": "error", "message": str}
    """
    try:
        # Validate required parameters for first call
        is_first_call = thread_id is None
        if is_first_call:
            if course_title is None:
                raise ValueError("course_title is required for the first call")
            if class_number is None:
                raise ValueError("class_number is required for the first call")
            if class_title is None:
                raise ValueError("class_title is required for the first call")
            if learning_objectives is None:
                raise ValueError("learning_objectives is required for the first call")
            if key_topics is None:
                raise ValueError("key_topics is required for the first call")
            if activities_projects is None:
                raise ValueError("activities_projects is required for the first call")
            if language is None:
                raise ValueError("language is required for the first call")
            # Generate thread_id BEFORE running the graph so checkpointer can use it
            thread_id = str(uuid.uuid4())

        # Yield thread_id immediately so frontend can track the conversation
        yield {"type": "thread_id", "thread_id": thread_id}

        # Build input state with the thread_id and is_first_call flag
        input_state: LessonPlanInput = {
            "course_title": course_title or "",
            "class_number": class_number or 0,
            "class_title": class_title or "",
            "learning_objectives": learning_objectives or [],
            "key_topics": key_topics or [],
            "activities_projects": activities_projects or [],
            "message": message,
            "file_contents": file_contents,
            "language": language or "English",
            "thread_id": thread_id,
            "is_first_call": is_first_call,
            "user_id": user_id,
        }

        # Build and compile graph with checkpointer
        workflow = build_lesson_plan_graph()

        async with AsyncSqliteSaver.from_conn_string(DBConfig.CHECKPOINTS_DB) as memory:
            graph = workflow.compile(checkpointer=memory)

            # Configuration for the graph execution - use the actual thread_id
            config: RunnableConfig = {"configurable": {"thread_id": thread_id}}

            # Track output for final response
            final_response = None

            # Yield initial progress
            yield {
                "type": "progress",
                "message_key": "overlay.initializingConversation",
            }

            # Stream events for progress updates
            async for event in graph.astream_events(
                input_state,
                config=config,
                version="v2",
            ):
                event_type = event.get("event")
                event_name = event.get("name", "")

                # Progress: ingesting documents to vector DB
                if event_type == "on_chain_start" and event_name == "ingest_documents":
                    yield {
                        "type": "progress",
                        "message_key": "overlay.ingestingDocuments",
                    }

                # Progress: generating lesson plan (main LLM call)
                elif event_type == "on_chain_start" and event_name == "generate":
                    yield {
                        "type": "progress",
                        "message_key": "overlay.generatingLessonPlan",
                    }

                # Progress: tool started
                elif event_type == "on_tool_start":
                    tool_name = event.get("name", "unknown tool")
                    yield {
                        "type": "progress",
                        "message_key": "overlay.usingTool",
                        "params": {"toolName": tool_name},
                    }

                # Progress: refining lesson plan based on evaluation
                elif event_type == "on_chain_start" and event_name == "refine":
                    yield {
                        "type": "progress",
                        "message_key": "overlay.refiningLessonPlan",
                    }

                # Progress: evaluating lesson plan
                elif event_type == "on_chain_start" and event_name == "evaluate":
                    yield {
                        "type": "progress",
                        "message_key": "overlay.evaluatingLessonPlan",
                    }

                # Progress: generating structured response
                elif event_type == "on_chain_start" and event_name == "respond":
                    yield {
                        "type": "progress",
                        "message_key": "overlay.structuringResponse",
                    }

                # Capture final output
                elif event_type == "on_chain_end" and event_name == "LangGraph":
                    output = event.get("data", {}).get("output", {})

                    if "final_response" in output and output["final_response"]:
                        response = output["final_response"]
                        if isinstance(response, LessonPlan):
                            final_response = response.model_dump()
                        elif isinstance(response, dict):
                            final_response = response

                    if "error" in output and output["error"]:
                        logger.error("Graph returned error: %s", output["error"])
                        yield {
                            "type": "error",
                            "message_key": "errors.generationFailed",
                        }
                        return

            # Yield the final result
            if final_response:
                yield {"type": "complete", "data": final_response}
            else:
                yield {
                    "type": "error",
                    "message_key": "errors.generationFailed",
                }

    except ValueError as e:
        logger.error("Lesson plan validation error: %s", e)
        yield {"type": "error", "message_key": "errors.generationFailed"}
    except Exception as e:
        logger.error("Lesson plan generation error: %s", e, exc_info=True)
        yield {"type": "error", "message_key": "errors.generationFailed"}
