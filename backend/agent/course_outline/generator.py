"""
Course outline generator entry point.

This module provides the main async generator function for course outline
generation, handling streaming progress updates and error management.
"""

import uuid
from typing import Any, Dict, List, AsyncGenerator

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from .graph import build_course_outline_graph
from .state import CourseOutlineInput
from schemas.course_outline import CourseOutline


async def run_course_outline_generator(
    message: str,
    topic: str | None = None,
    number_of_classes: int | None = None,
    thread_id: str | None = None,
    file_contents: List[Dict[str, str]] | None = None,
    language: str | None = None,
) -> AsyncGenerator[Dict, None]:
    """
    Run the course outline generator with streaming progress updates.

    This is the main entry point for course outline generation. It sets up
    the LangGraph workflow, streams events for progress tracking, and yields
    structured results.

    Args:
        message: The main user message/prompt (optional additional context).
        topic: The topic/subject for the course outline (required for first call).
        number_of_classes: Number of classes in the outline (required for first call).
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
            if topic is None:
                raise ValueError("topic is required for the first call")
            if number_of_classes is None:
                raise ValueError("number_of_classes is required for the first call")
            if language is None:
                raise ValueError("language is required for the first call")
            # Generate thread_id BEFORE running the graph so checkpointer can use it
            thread_id = str(uuid.uuid4())

        # Yield thread_id immediately so frontend can track the conversation
        yield {"type": "thread_id", "thread_id": thread_id}

        # Build input state with the thread_id and is_first_call flag
        input_state: CourseOutlineInput = {
            "topic": topic or "",
            "number_of_classes": number_of_classes or 0,
            "message": message,
            "file_contents": file_contents,
            "language": language or "English",
            "thread_id": thread_id,
            "is_first_call": is_first_call,
        }

        # Build and compile graph with checkpointer
        workflow = build_course_outline_graph()

        async with AsyncSqliteSaver.from_conn_string("checkpoints.db") as memory:
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

                # Progress: generating outline (main LLM call)
                if event_type == "on_chain_start" and event_name == "generate":
                    yield {
                        "type": "progress",
                        "message_key": "overlay.generatingCourseOutline",
                    }

                # Progress: tool started
                elif event_type == "on_tool_start":
                    tool_name = event.get("name", "unknown tool")
                    yield {
                        "type": "progress",
                        "message_key": "overlay.usingTool",
                        "params": {"toolName": tool_name},
                    }

                # Progress: tool completed
                elif event_type == "on_tool_end":
                    tool_name = event.get("name", "unknown tool")
                    yield {
                        "type": "progress",
                        "message_key": "overlay.completedTool",
                        "params": {"toolName": tool_name},
                    }

                # Progress: evaluating outline
                elif event_type == "on_chain_start" and event_name == "evaluate":
                    yield {
                        "type": "progress",
                        "message_key": "overlay.evaluatingOutline",
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
                        if isinstance(response, CourseOutline):
                            final_response = response.model_dump()
                        elif isinstance(response, dict):
                            final_response = response

                    if "error" in output and output["error"]:
                        yield {"type": "error", "message": output["error"]}
                        return

            # Yield the final result
            if final_response:
                yield {"type": "complete", "data": final_response}
            else:
                yield {
                    "type": "error",
                    "message": "Could not extract structured output from agent response",
                }

    except ValueError as e:
        yield {"type": "error", "message": str(e)}
    except Exception as e:
        yield {
            "type": "error",
            "message": f"Error while generating course outline: {str(e)}",
        }
