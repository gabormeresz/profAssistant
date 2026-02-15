"""
Presentation generator entry point.

This module provides the main async generator function for presentation
generation, handling streaming progress updates and error management.
"""

import logging
import uuid
from typing import Any, Dict, List, Optional, AsyncGenerator

from langchain_core.runnables import RunnableConfig

logger = logging.getLogger(__name__)
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from config import DBConfig, EvaluationConfig
from .graph import build_presentation_graph
from .state import PresentationInput
from schemas.presentation import Presentation


async def run_presentation_generator(
    message: str,
    course_title: str | None = None,
    class_number: int | None = None,
    class_title: str | None = None,
    learning_objective: str | None = None,
    key_points: List[str] | None = None,
    lesson_breakdown: str | None = None,
    activities: str | None = None,
    homework: str | None = None,
    extra_activities: str | None = None,
    thread_id: str | None = None,
    file_contents: List[Dict[str, str]] | None = None,
    language: str | None = None,
    user_id: str = "",
) -> AsyncGenerator[Dict, None]:
    """
    Run the presentation generator with streaming progress updates.

    This is the main entry point for presentation generation. It sets up
    the LangGraph workflow, streams events for progress tracking, and yields
    structured results.

    Args:
        message: The main user message/prompt (optional additional context).
        course_title: The title of the course (required for first call).
        class_number: The class number in the course (required for first call).
        class_title: The title of this class/lesson (required for first call).
        learning_objective: Main learning goal (optional).
        key_points: List of essential concepts (optional).
        lesson_breakdown: Text description of lesson flow (optional).
        activities: Text description of activities (optional).
        homework: Homework assignment text (optional).
        extra_activities: Extension activities text (optional).
        thread_id: Optional thread ID for conversation continuity.
        file_contents: Optional list of file contents with filename and content.
        language: Language for the generated content (required for first call).
        user_id: The user's ID for API key resolution.

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
            if language is None:
                raise ValueError("language is required for the first call")
            thread_id = str(uuid.uuid4())

        # Yield thread_id immediately so frontend can track the conversation
        yield {"type": "thread_id", "thread_id": thread_id}

        # Build input state
        input_state: PresentationInput = {
            "course_title": course_title or "",
            "class_number": class_number or 0,
            "class_title": class_title or "",
            "learning_objective": learning_objective,
            "key_points": key_points or [],
            "lesson_breakdown": lesson_breakdown,
            "activities": activities,
            "homework": homework,
            "extra_activities": extra_activities,
            "message": message,
            "file_contents": file_contents,
            "language": language or "English",
            "thread_id": thread_id,
            "is_first_call": is_first_call,
            "user_id": user_id,
        }

        # Build and compile graph with checkpointer
        workflow = build_presentation_graph()

        async with AsyncSqliteSaver.from_conn_string(DBConfig.CHECKPOINTS_DB) as memory:
            graph = workflow.compile(checkpointer=memory)

            config: RunnableConfig = {
                "configurable": {"thread_id": thread_id},
                "recursion_limit": EvaluationConfig.GRAPH_RECURSION_LIMIT,
            }

            final_response = None

            yield {
                "type": "progress",
                "message_key": "overlay.initializingConversation",
            }

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

                # Progress: generating presentation (main LLM call)
                elif event_type == "on_chain_start" and event_name == "generate":
                    yield {
                        "type": "progress",
                        "message_key": "overlay.generatingPresentation",
                    }

                # Progress: tool started
                elif event_type == "on_tool_start":
                    tool_name = event.get("name", "unknown tool")
                    yield {
                        "type": "progress",
                        "message_key": "overlay.usingTool",
                        "params": {"toolName": tool_name},
                    }

                # Progress: refining presentation based on evaluation
                elif event_type == "on_chain_start" and event_name == "refine":
                    yield {
                        "type": "progress",
                        "message_key": "overlay.refiningPresentation",
                    }

                # Progress: evaluating presentation
                elif event_type == "on_chain_start" and event_name == "evaluate":
                    yield {
                        "type": "progress",
                        "message_key": "overlay.evaluatingPresentation",
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
                        if isinstance(response, Presentation):
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

            if final_response:
                yield {"type": "complete", "data": final_response}
            else:
                yield {
                    "type": "error",
                    "message_key": "errors.generationFailed",
                }

    except ValueError as e:
        logger.error("Presentation validation error: %s", e)
        yield {"type": "error", "message_key": "errors.generationFailed"}
    except Exception as e:
        logger.error("Presentation generation error: %s", e, exc_info=True)
        yield {"type": "error", "message_key": "errors.generationFailed"}
