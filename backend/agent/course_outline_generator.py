"""
Course outline generator using structured output.
Returns validated Pydantic CourseOutline model with progress updates.
"""

from typing import Dict, List, Optional
from schemas.course_outline import CourseOutline
from schemas.conversation import (
    ConversationType,
    CourseOutlineCreate,
    CourseOutlineMetadata,
)
from langchain.agents import create_agent
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langchain.agents import AgentState
from .tools import web_search
from .model import model
from dataclasses import dataclass
import uuid
from utils.context_builders import build_file_contents_message
from services.conversation_manager import conversation_manager

# Setup tools list
tools = [web_search]


# Define custom state extending AgentState
class CourseOutlineAgentState(AgentState):
    topic: str
    number_of_classes: int
    file_contents: Optional[List[Dict[str, str]]]


# Define context for runtime data
@dataclass
class Context:
    thread_id: str


def build_user_message(
    is_first_call: bool,
    topic: str,
    number_of_classes: int,
    message: str,
    file_contents: List[Dict[str, str]] | None,
) -> Dict[str, str]:
    """Build the user message dictionary."""
    # Prepare messages
    messages = ""

    # On first call (no existing thread_id), add the topic and number of classes
    if is_first_call:
        messages += (
            f"Create a course outline on '{topic}' with {number_of_classes} classes.\n"
        )

    # Add user message if provided
    if message.strip():
        messages += f"{message}\n\n"

    # Add file contents if provided
    if file_contents:
        messages += f"{build_file_contents_message(file_contents)}\n"

    return {"role": "user", "content": messages}


def generate_thread_id(thread_id: str | None) -> str:
    """Generate or return existing thread ID."""
    return thread_id if thread_id else str(uuid.uuid4())


async def run_course_outline_generator(
    message: str,
    topic: str | None = None,
    number_of_classes: int | None = None,
    thread_id: str | None = None,
    file_contents: List[Dict[str, str]] | None = None,
    language: str | None = None,
):
    """
    Run the course outline generator with structured output using CourseOutline schema.
    Uses tools, memory, and shows progress updates including tool usage.
    Returns the complete structured output at the end.

    Args:
        message: The main user message/prompt (optional additional context)
        topic: The topic/subject for the course outline (required for first call, ignored on follow-ups)
        number_of_classes: Number of classes in the course outline (required for first call, ignored on follow-ups)
        thread_id: Optional thread ID for conversation continuity. If None, creates a new one.
        file_contents: Optional list of file contents with filename and content
        language: Language for the generated content (required for first call, ignored on follow-ups)

    Returns:
        Generator that yields progress updates, tool usage, and structured data
    """

    try:
        # Determine if this is the first call
        is_first_call = thread_id is None
        # Use existing thread ID or create a new one
        thread_id = generate_thread_id(thread_id)

        # Yield thread ID first
        yield {"type": "thread_id", "thread_id": thread_id}

        # Save or update conversation metadata
        if is_first_call:
            # Validate required parameters for first call
            if topic is None or number_of_classes is None or language is None:
                raise ValueError(
                    "topic, number_of_classes, and language are required for the first call"
                )

            # Create new conversation metadata
            title = f"{topic[:50]}..." if len(topic) > 50 else topic
            conversation_manager.create_course_outline(
                thread_id=thread_id,
                conversation_type=ConversationType.COURSE_OUTLINE,
                data=CourseOutlineCreate(
                    title=title,
                    topic=topic,
                    number_of_classes=number_of_classes,
                    language=language,
                    user_comment=message if message.strip() else None,
                ),
            )
        else:
            # Update existing conversation (increment message count, update timestamp)
            conversation_manager.increment_message_count(thread_id)
            # Load all parameters from the saved conversation
            conversation = conversation_manager.get_conversation(thread_id)
            if conversation and isinstance(conversation, CourseOutlineMetadata):
                language = conversation.language
                topic = conversation.topic
                number_of_classes = conversation.number_of_classes
            else:
                raise ValueError(
                    f"Conversation not found or invalid type for thread_id: {thread_id}"
                )

        system_prompt = f"""
        You are a helpful educational assistant that generates professional course outlines.
        Always stick to the topic and number of classes the user provided unless the user explicitly asks otherwise. 
        
        If the user provides reference materials (file uploads), use them as contextual inspiration and do not copy them verbatim.
        Stick to the topic and number of classes even if the reference materials suggest otherwise,
        however try to extract and use the content of the reference materials if relevant.
        
        You can use the available tools to gather more information any time.
        
        Generate a structured course outline following the provided schema with detailed information for each class.
        The output language must be {language}.
        All course content (titles, objectives, topics, activities, etc.) should be written in {language},
        but keep all JSON field names in English to conform to the schema.
    """

        # Setup persistent SQLite checkpointer using async context manager
        async with AsyncSqliteSaver.from_conn_string("checkpoints.db") as memory:
            # Create agent with structured output using response_format parameter
            current_agent = create_agent(
                model=model,
                tools=tools,
                state_schema=CourseOutlineAgentState,
                context_schema=Context,
                system_prompt=system_prompt,
                checkpointer=memory,
                response_format=CourseOutline,  # This enables structured output!
            )

            # Build user message
            user_message = build_user_message(
                is_first_call, topic, number_of_classes, message, file_contents
            )

            # Prepare the initial state
            initial_state = {
                "messages": user_message,
                "topic": topic,
                "number_of_classes": number_of_classes,
                "file_contents": file_contents,
            }

            # Create context
            context = Context(thread_id=thread_id)

            # Create config with thread_id for checkpointer
            config = {"configurable": {"thread_id": thread_id}}

            # Yield progress update
            yield {"type": "progress", "message_key": "overlay.generatingCourseOutline"}

            # Track the agent's structured response
            final_result = None

            # Stream events from the agent to show progress and tool usage
            async for event in current_agent.astream_events(
                initial_state,
                context=context,
                config=config,  # type: ignore
                version="v2",
            ):
                kind = event.get("event")

                # Detect tool calls
                if kind == "on_tool_start":
                    tool_name = event.get("name", "unknown tool")
                    yield {
                        "type": "progress",
                        "message_key": "overlay.usingTool",
                        "params": {"toolName": tool_name},
                    }

                # Detect tool results
                if kind == "on_tool_end":
                    tool_name = event.get("name", "unknown tool")
                    yield {
                        "type": "progress",
                        "message_key": "overlay.completedTool",
                        "params": {"toolName": tool_name},
                    }

                # Capture the final structured response from the agent
                if kind == "on_chain_end" and event.get("name") == "LangGraph":
                    output = event.get("data", {}).get("output", {})
                    # When using response_format, the structured response is in the output
                    if "structured_response" in output:
                        structured_response = output["structured_response"]
                        if isinstance(structured_response, CourseOutline):
                            final_result = structured_response.model_dump()
                        elif isinstance(structured_response, dict):
                            final_result = structured_response
                    # Fallback: check messages for structured content
                    elif "messages" in output and output["messages"]:
                        last_message = output["messages"][-1]
                        if hasattr(last_message, "content"):
                            content = last_message.content
                            if isinstance(content, CourseOutline):
                                final_result = content.model_dump()
                            elif isinstance(content, dict):
                                try:
                                    course_outline = CourseOutline(**content)
                                    final_result = course_outline.model_dump()
                                except Exception:
                                    pass

            # If we got a valid result, yield it
            if final_result:
                yield {"type": "complete", "data": final_result}
            else:
                yield {
                    "type": "error",
                    "message": "Could not extract structured output from agent response",
                }

    except Exception as e:
        yield {
            "type": "error",
            "message": f"Error while generating structured content: {str(e)}",
        }
