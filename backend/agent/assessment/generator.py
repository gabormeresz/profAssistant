"""
Assessment generator entry point.

This module provides the main async generator function for assessment
generation, handling streaming progress updates and error management.
"""

import logging
import uuid
from typing import Any, Dict, List, AsyncGenerator, Optional, cast

from langchain_core.runnables import RunnableConfig

logger = logging.getLogger(__name__)
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from config import DBConfig, EvaluationConfig
from schemas.assessment import (
    ALLOWED_QUESTION_TYPES,
    ALLOWED_ASSESSMENT_TYPES,
    ALLOWED_DIFFICULTY_LEVELS,
)
from .graph import build_assessment_graph
from .state import AssessmentInput, AssessmentType, DifficultyLevel
from schemas.assessment import Assessment


async def run_assessment_generator(
    message: str,
    course_title: str | None = None,
    class_title: str | None = None,
    key_topics: List[str] | None = None,
    assessment_type: str | None = None,
    difficulty_level: str | None = None,
    question_type_configs: List[dict] | None = None,
    additional_instructions: str | None = None,
    thread_id: str | None = None,
    file_contents: List[Dict[str, str]] | None = None,
    language: str | None = None,
    user_id: str = "",
) -> AsyncGenerator[Dict, None]:
    """
    Run the assessment generator with streaming progress updates.

    Args:
        message: The main user message/prompt.
        course_title: The title of the course (required for first call).
        class_title: Optional title of this class/lesson.
        key_topics: List of key topics to cover (required for first call).
        assessment_type: Type of assessment: quiz, exam, homework, practice.
        difficulty_level: Difficulty: easy, medium, hard, mixed.
        question_type_configs: List of {question_type, count} configs (required for first call).
        additional_instructions: Optional extra instructions.
        thread_id: Optional thread ID for conversation continuity.
        file_contents: Optional list of file contents with filename and content.
        language: Language for the generated content (required for first call).
        user_id: The user's ID for API key resolution.

    Yields:
        Progress updates, thread_id, and final structured data.
    """
    try:
        # Validate required parameters for first call
        is_first_call = thread_id is None
        if is_first_call:
            if course_title is None:
                raise ValueError("course_title is required for the first call")
            if not key_topics:
                raise ValueError("key_topics is required for the first call")
            if question_type_configs is None:
                raise ValueError("question_type_configs is required for the first call")

            # Normalize frontend key "type" → backend key "question_type"
            question_type_configs = [
                {
                    "question_type": cfg.get("question_type") or cfg.get("type", ""),
                    "count": cfg.get("count", 0),
                    "points_each": cfg.get("points_each", 5),
                }
                for cfg in question_type_configs
            ]

            # Validate enum values (defense-in-depth: endpoint also validates)
            at = assessment_type or "quiz"
            if at not in ALLOWED_ASSESSMENT_TYPES:
                raise ValueError(
                    f"Invalid assessment_type '{at}'. "
                    f"Allowed: {', '.join(sorted(ALLOWED_ASSESSMENT_TYPES))}"
                )
            dl = difficulty_level or "mixed"
            if dl not in ALLOWED_DIFFICULTY_LEVELS:
                raise ValueError(
                    f"Invalid difficulty_level '{dl}'. "
                    f"Allowed: {', '.join(sorted(ALLOWED_DIFFICULTY_LEVELS))}"
                )
            for cfg in question_type_configs:
                qt = cfg.get("question_type", "")
                if qt not in ALLOWED_QUESTION_TYPES:
                    raise ValueError(
                        f"Invalid question_type '{qt}'. "
                        f"Allowed: {', '.join(sorted(ALLOWED_QUESTION_TYPES))}"
                    )

            if language is None:
                raise ValueError("language is required for the first call")
            # Generate thread_id BEFORE running the graph so checkpointer can use it
            thread_id = str(uuid.uuid4())

        # Yield thread_id immediately so frontend can track the conversation
        yield {"type": "thread_id", "thread_id": thread_id}

        # Build input state with the thread_id and is_first_call flag
        input_state = cast(
            AssessmentInput,
            {
                "course_title": course_title or "",
                "class_title": class_title,
                "key_topics": key_topics or [],
                "assessment_type": assessment_type or "quiz",
                "difficulty_level": difficulty_level or "mixed",
                "question_type_configs": question_type_configs or [],
                "additional_instructions": additional_instructions,
                "message": message,
                "file_contents": file_contents,
                "language": language or "English",
                "thread_id": thread_id,
                "is_first_call": is_first_call,
                "user_id": user_id,
            },
        )

        # Build and compile graph with checkpointer
        workflow = build_assessment_graph()

        async with AsyncSqliteSaver.from_conn_string(DBConfig.CHECKPOINTS_DB) as memory:
            graph = workflow.compile(checkpointer=memory)

            # Configuration for the graph execution
            config: RunnableConfig = {
                "configurable": {"thread_id": thread_id},
                "recursion_limit": EvaluationConfig.GRAPH_RECURSION_LIMIT,
            }

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

                # Progress: ingesting documents to vector DB (only show when there are files)
                if event_type == "on_chain_start" and event_name == "ingest_documents":
                    if file_contents:
                        yield {
                            "type": "progress",
                            "message_key": "overlay.ingestingDocuments",
                        }

                # Progress: generating assessment (main LLM call)
                elif event_type == "on_chain_start" and event_name == "generate":
                    yield {
                        "type": "progress",
                        "message_key": "overlay.generatingAssessment",
                    }

                # Progress: tool started
                elif event_type == "on_tool_start":
                    tool_name = event.get("name", "unknown tool")
                    yield {
                        "type": "progress",
                        "message_key": "overlay.usingTool",
                        "params": {"toolName": tool_name},
                    }

                # Progress: refining assessment based on evaluation
                elif event_type == "on_chain_start" and event_name == "refine":
                    yield {
                        "type": "progress",
                        "message_key": "overlay.refiningAssessment",
                    }

                # Progress: evaluating assessment
                elif event_type == "on_chain_start" and event_name == "evaluate":
                    yield {
                        "type": "progress",
                        "message_key": "overlay.evaluatingAssessment",
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
                        if isinstance(response, Assessment):
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
        logger.error("Assessment validation error: %s", e)
        yield {"type": "error", "message_key": "errors.generationFailed"}
    except Exception as e:
        logger.error("Assessment generation error: %s", e, exc_info=True)
        yield {"type": "error", "message_key": "errors.generationFailed"}
