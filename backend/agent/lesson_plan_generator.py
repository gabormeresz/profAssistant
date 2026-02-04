"""
Lesson plan generator using structured output.
Returns validated Pydantic LessonPlan model with progress updates.
"""

from langchain.agents import create_agent, AgentState
from schemas.lesson_plan import LessonPlan
from schemas.conversation import ConversationType, LessonPlanCreate, LessonPlanMetadata
from typing import Dict, List, Optional
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from .tools import web_search
from .model import model
from dataclasses import dataclass
import uuid
from utils.context_builders import build_file_contents_message
from services.conversation_manager import conversation_manager

# Setup tools list
tools = [web_search]


# Define custom state extending AgentState
class LessonPlannerAgentState(AgentState):
    course_title: str
    class_number: int
    class_title: str
    learning_objectives: List[str]
    key_topics: List[str]
    activities_projects: List[str]
    file_contents: Optional[List[Dict[str, str]]]


# Define context for runtime data
@dataclass
class Context:
    thread_id: str


def build_user_message(
    is_first_call: bool,
    course_title: str,
    class_number: int,
    class_title: str,
    learning_objectives: List[str],
    key_topics: List[str],
    activities_projects: List[str],
    message: str,
    file_contents: List[Dict[str, str]] | None,
) -> Dict[str, str]:
    """Build the user message dictionary."""
    # Prepare messages
    messages = ""

    # On first call (no existing thread_id), add the topic and number of classes
    if is_first_call:
        messages += f"Create a lesson plan for a university course.\n"
        messages += f"Course Title: {course_title}.\n"
        messages += f"Class Number: {class_number}.\n"
        messages += f"Class Title: {class_title}.\n"

        # Only include optional fields if they have content
        if learning_objectives:
            messages += f"Learning objectives: {', '.join(learning_objectives)}.\n"
        if key_topics:
            messages += f"Key topics: {', '.join(key_topics)}.\n"
        if activities_projects:
            messages += f"Activities/Projects: {', '.join(activities_projects)}.\n"

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


async def run_structured_lesson_plan_generator(
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
):
    """
    Run the LangChain model with structured output using LessonPlan schema.
    Shows progress updates and returns the complete structured output at the end.

    Args:
        message: The main user message/prompt (optional additional context)
        course_title: The title of the course (required for first call, ignored on follow-ups)
        class_number: The sequential number of the class (required for first call, ignored on follow-ups)
        class_title: The title of the class (required for first call, ignored on follow-ups)
        learning_objectives: List of learning objectives for the class (required for first call, ignored on follow-ups)
        key_topics: List of key topics for the class (required for first call, ignored on follow-ups)
        activities_projects: List of activities/projects for the class (required for first call, ignored on follow-ups)
        thread_id: Optional thread ID for conversation continuity. If None, creates a new one.
        file_contents: Optional list of file contents with filename and content
        language: Language for the generated content (required for first call, ignored on follow-ups)
    Returns:
        Generator that yields progress updates and structured data
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
            if (
                course_title is None
                or class_number is None
                or class_title is None
                or learning_objectives is None
                or key_topics is None
                or activities_projects is None
                or language is None
            ):
                raise ValueError(
                    "All lesson plan parameters are required for the first call"
                )

            # Create new conversation metadata
            title = f"{class_title[:50]}..." if len(class_title) > 50 else class_title
            conversation_manager.create_lesson_plan(
                thread_id=thread_id,
                conversation_type=ConversationType.LESSON_PLAN,
                data=LessonPlanCreate(
                    title=title,
                    course_title=course_title,
                    class_number=class_number,
                    class_title=class_title,
                    learning_objectives=learning_objectives,
                    key_topics=key_topics,
                    activities_projects=activities_projects,
                    language=language,
                    user_comment=message if message.strip() else None,
                ),
            )
        else:
            # Update existing conversation (increment message count, update timestamp)
            conversation_manager.increment_message_count(thread_id)
            # Load all parameters from the saved conversation
            conversation = conversation_manager.get_conversation(thread_id)
            if conversation and isinstance(conversation, LessonPlanMetadata):
                language = conversation.language
                course_title = conversation.course_title
                class_number = conversation.class_number
                class_title = conversation.class_title
                learning_objectives = conversation.learning_objectives
                key_topics = conversation.key_topics
                activities_projects = conversation.activities_projects
            else:
                raise ValueError(
                    f"Conversation not found or invalid type for thread_id: {thread_id}"
                )

        system_prompt = f"""You are an expert instructional designer specializing in detailed university lesson plans.

## Your Expertise
- Lesson pacing and time management for class sessions
- Active learning techniques and student engagement
- Formative assessment design
- Differentiated instruction strategies

## Lesson Plan Requirements

### 1. Time Allocation
- Break down the lesson into timed segments (introduction, activities, wrap-up)
- Ensure realistic timing - don't overcrowd the session
- Include buffer time for questions and transitions
- Standard class: 50-90 minutes depending on institution

### 2. Learning Activities
Design activities that:
- Directly support the provided learning objectives
- Include a mix of: direct instruction, guided practice, independent work
- Incorporate active learning: discussions, problem-solving, hands-on work
- Build on each other within the lesson

### 3. Assessment Integration
Include formative assessment:
- Check for understanding throughout (not just at the end)
- Quick polls, exit tickets, or practice problems
- Opportunities for immediate feedback

### 4. Materials & Resources
Specify:
- Required materials for instructor and students
- Technology needs (if any)
- Handouts, slides, or supplementary resources

### 5. Differentiation
When appropriate, suggest:
- Extensions for advanced students
- Support strategies for struggling students
- Alternative approaches for different learning styles

## Input Context
You will receive:
- Course title and class number (position in the course sequence)
- Class title and topic
- Learning objectives to achieve
- Key topics to cover
- Suggested activities/projects

Use these as your foundation and expand with detailed implementation guidance.

## Output Specifications
- **Language**: All content in {language}
- **JSON Fields**: Keep field names in English for schema compliance
- **Detail Level**: Specific enough for any instructor to execute without additional preparation

Generate a comprehensive, ready-to-use lesson plan."""

        # Setup persistent SQLite checkpointer using async context manager
        async with AsyncSqliteSaver.from_conn_string("checkpoints.db") as memory:

            # Create a new agent instance with the dynamic system prompt and memory
            current_agent = create_agent(
                model=model,
                tools=tools,
                state_schema=LessonPlannerAgentState,
                context_schema=Context,
                system_prompt=system_prompt,
                checkpointer=memory,
                response_format=LessonPlan,  # This enables structured output!
            )

            # Build user message
            user_message = build_user_message(
                is_first_call,
                course_title,
                class_number,
                class_title,
                learning_objectives,
                key_topics,
                activities_projects,
                message,
                file_contents,
            )

            # Prepare the initial state
            initial_state = {
                "messages": user_message,
                "course_title": course_title,
                "class_number": class_number,
                "class_title": class_title,
                "learning_objectives": learning_objectives,
                "key_topics": key_topics,
                "activities_projects": activities_projects,
                "file_contents": file_contents,
            }

            # Create context
            context = Context(thread_id=thread_id)

            # Create config with thread_id for checkpointer
            config = {"configurable": {"thread_id": thread_id}}

            # Yield progress update
            yield {"type": "progress", "message_key": "overlay.generatingLessonPlan"}

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
                        if isinstance(structured_response, LessonPlan):
                            final_result = structured_response.model_dump()
                        elif isinstance(structured_response, dict):
                            final_result = structured_response
                    # Fallback: check messages for structured content
                    elif "messages" in output and output["messages"]:
                        last_message = output["messages"][-1]
                        if hasattr(last_message, "content"):
                            content = last_message.content
                            if isinstance(content, LessonPlan):
                                final_result = content.model_dump()
                            elif isinstance(content, dict):
                                try:
                                    course_outline = LessonPlan(**content)
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
