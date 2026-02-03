"""
Node functions for the course outline generation workflow.

This module contains all the node functions used in the LangGraph workflow.
Each function represents a discrete step in the course outline generation process.
"""

from typing import Literal
import uuid

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from schemas.course_outline import CourseOutline
from schemas.evaluation import EvaluationResult
from schemas.conversation import (
    ConversationType,
    CourseOutlineCreate,
    CourseOutlineMetadata,
)
from services.conversation_manager import conversation_manager
from utils.context_builders import build_file_contents_message

from .state import CourseOutlineState
from .prompts import (
    get_system_prompt,
    get_structured_output_prompt,
    get_evaluator_system_prompt,
    get_refinement_prompt,
)
from agent.model import model
from agent.tools import web_search


# Setup tools
tools = [web_search]

# Model configurations
model_with_tools = model.bind_tools(tools)
model_with_structured_output = model.with_structured_output(CourseOutline)
model_with_evaluation_output = model.with_structured_output(EvaluationResult)


def initialize_conversation(state: CourseOutlineState) -> dict:
    """
    Initialize or load conversation metadata.

    For first calls, creates a new conversation record.
    For follow-ups, increments the message count and loads existing metadata.

    Args:
        state: The current workflow state.

    Returns:
        Updated state with thread_id and is_first_call flag.
    """
    thread_id = state["thread_id"]
    is_first_call = state.get("is_first_call", True)

    if is_first_call:
        # Create new conversation record
        topic = state["topic"]
        title = f"{topic[:50]}..." if len(topic) > 50 else topic

        conversation_manager.create_course_outline(
            thread_id=thread_id,
            conversation_type=ConversationType.COURSE_OUTLINE,
            data=CourseOutlineCreate(
                title=title,
                topic=state["topic"],
                number_of_classes=state["number_of_classes"],
                language=state["language"],
                user_comment=(
                    state.get("message") if state.get("message", "").strip() else None
                ),
            ),
        )
    else:
        # Update existing conversation
        conversation_manager.increment_message_count(thread_id)

        # Load parameters from saved conversation for follow-ups
        conversation = conversation_manager.get_conversation(thread_id)
        if conversation and isinstance(conversation, CourseOutlineMetadata):
            return {
                "thread_id": thread_id,
                "is_first_call": is_first_call,
                "language": conversation.language,
                "topic": conversation.topic,
                "number_of_classes": conversation.number_of_classes,
            }

    return {
        "thread_id": thread_id,
        "is_first_call": is_first_call,
    }


def build_messages(state: CourseOutlineState) -> dict:
    """
    Build the initial messages for the agent.

    Constructs the system message and user message based on the current state.
    Handles first calls differently from follow-up messages.

    Args:
        state: The current workflow state.

    Returns:
        Updated state with messages list.
    """
    messages = []

    # Add system message
    system_prompt = get_system_prompt(state["language"])
    messages.append(SystemMessage(content=system_prompt))

    # Build user message content
    user_content_parts = []

    if state.get("is_first_call", True):
        user_content_parts.append(
            f"Create a course outline on '{state['topic']}' "
            f"with {state['number_of_classes']} classes."
        )

    user_message = state.get("message", "")
    if user_message.strip():
        user_content_parts.append(user_message)

    file_contents = state.get("file_contents")
    if file_contents:
        user_content_parts.append(build_file_contents_message(file_contents))

    if user_content_parts:
        messages.append(HumanMessage(content="\n\n".join(user_content_parts)))

    return {"messages": messages}


def generate_outline(state: CourseOutlineState) -> dict:
    """
    Generate or refine the course outline using the LLM.

    This node invokes the model and allows it to make tool calls
    if it needs additional information. The response is stored in
    agent_response (not messages) to allow for clean JSON formatting later.

    If evaluation feedback is present, it incorporates the feedback
    to refine the previous response.

    Args:
        state: The current workflow state.

    Returns:
        Updated state with the model's response in agent_response.
        If tools are called, also updates messages for tool execution.
    """
    messages = list(state["messages"])

    # Check if we have evaluation feedback for refinement
    evaluation_feedback = state.get("evaluation_feedback")
    if evaluation_feedback:
        # Get the previous response content for context
        agent_response = state.get("agent_response")
        original_content = ""
        if agent_response and hasattr(agent_response, "content"):
            original_content = str(agent_response.content)

        language = state.get("language", "English")
        refinement_prompt = get_refinement_prompt(
            original_content, evaluation_feedback, language
        )
        messages.append(HumanMessage(content=refinement_prompt))

    response = model_with_tools.invoke(messages)

    # If there are tool calls, we need to add to messages for the ToolNode
    if hasattr(response, "tool_calls") and response.tool_calls:
        return {"messages": [response], "agent_response": response}

    # Otherwise, just store in agent_response (don't pollute messages with raw response)
    return {"agent_response": response}


def generate_structured_response(state: CourseOutlineState) -> dict:
    """
    Generate the final structured course outline.

    Uses the agent_response from the conversation to produce
    a properly structured CourseOutline response. Adds a clean JSON
    message to the checkpoint for frontend compatibility.

    Args:
        state: The current workflow state.

    Returns:
        Updated state with final_response and clean AI message.
    """
    try:
        # Get the agent's response content
        agent_response = state.get("agent_response")
        if not agent_response:
            return {"error": "No agent response available for generating output"}

        # Extract content from the agent response
        context_content = ""
        if hasattr(agent_response, "content") and agent_response.content:
            context_content = str(agent_response.content)
        else:
            context_content = str(agent_response)

        if not context_content:
            return {"error": "No context available for generating response"}

        # Generate structured output
        prompt = get_structured_output_prompt(context_content, state["language"])
        response = model_with_structured_output.invoke([HumanMessage(content=prompt)])

        # Ensure we have a CourseOutline object
        if not isinstance(response, CourseOutline):
            return {
                "error": "Failed to generate structured output: unexpected response type"
            }

        # Convert the structured response to clean JSON for checkpoint storage
        # This ensures the frontend can parse it without markdown code fences
        clean_json = response.model_dump_json()
        clean_ai_message = AIMessage(content=clean_json)

        # Add the clean JSON as the AI message to the checkpoint
        return {"final_response": response, "messages": [clean_ai_message]}

    except Exception as e:
        return {"error": f"Failed to generate structured output: {str(e)}"}


def route_after_generate(state: CourseOutlineState) -> Literal["tools", "evaluate"]:
    """
    Route the workflow after generation.

    Checks if the generator wants to use tools or if it's ready to be evaluated.

    Args:
        state: The current workflow state.

    Returns:
        "tools" if tools should be called, "evaluate" otherwise.
    """
    # Check the agent_response for tool calls
    agent_response = state.get("agent_response")

    if not agent_response:
        return "evaluate"

    # Check if the model wants to use tools (only AIMessage has tool_calls)
    if isinstance(agent_response, AIMessage) and agent_response.tool_calls:
        return "tools"

    return "evaluate"


MAX_EVALUATION_RETRIES = 3


def evaluate_outline(state: CourseOutlineState) -> dict:
    """
    Evaluate the generated course outline for quality.

    This node acts as an evaluator agent that assesses the quality of
    the generated content and decides whether it needs refinement.
    Uses structured output for reliable parsing of evaluation results.

    Args:
        state: The current workflow state.

    Returns:
        Updated state with evaluation_count and potentially evaluation_feedback.
    """
    # Get current evaluation count (default to 0 if not set)
    current_count = state.get("evaluation_count", 0)

    # If we've already done MAX_EVALUATION_RETRIES, skip evaluation
    if current_count >= MAX_EVALUATION_RETRIES:
        return {
            "evaluation_count": current_count,
            "evaluation_feedback": None,
        }

    # Get the agent's response to evaluate
    agent_response = state.get("agent_response")
    if not agent_response:
        return {
            "evaluation_count": current_count + 1,
            "evaluation_feedback": None,
        }

    # Extract content from the agent response
    content_to_evaluate = ""
    if hasattr(agent_response, "content") and agent_response.content:
        content_to_evaluate = str(agent_response.content)
    else:
        content_to_evaluate = str(agent_response)

    # Build evaluation messages
    language = state.get("language", "English")
    evaluation_messages = [
        SystemMessage(content=get_evaluator_system_prompt(language)),
        HumanMessage(
            content=f"Please evaluate the following course outline:\n\n{content_to_evaluate}"
        ),
    ]

    try:
        # Call the evaluator model with structured output
        evaluation_result = model_with_evaluation_output.invoke(evaluation_messages)

        # Ensure we have an EvaluationResult object
        if not isinstance(evaluation_result, EvaluationResult):
            return {
                "evaluation_count": current_count + 1,
                "evaluation_feedback": None,
            }

        if evaluation_result.verdict == "APPROVED":
            return {
                "evaluation_count": current_count + 1,
                "evaluation_feedback": None,
            }
        else:
            # Compile feedback for refinement
            feedback = f"Evaluation Result: {evaluation_result.reasoning}\n\nSuggestions for improvement:\n"
            for i, suggestion in enumerate(evaluation_result.suggestions, 1):
                feedback += f"{i}. {suggestion.text}\n"

            return {
                "evaluation_count": current_count + 1,
                "evaluation_feedback": feedback,
            }

    except Exception:
        # If evaluation fails, assume it's approved to avoid infinite loops
        return {
            "evaluation_count": current_count + 1,
            "evaluation_feedback": None,
        }


def route_after_evaluate(state: CourseOutlineState) -> Literal["generate", "respond"]:
    """
    Route the workflow after evaluation.

    Args:
        state: The current workflow state.

    Returns:
        "generate" if the evaluator provided feedback (for refinement), "respond" otherwise.
    """
    evaluation_feedback = state.get("evaluation_feedback")
    evaluation_count = state.get("evaluation_count", 0)

    # If we have feedback and haven't exceeded max retries, go back to generator for refinement
    if evaluation_feedback and evaluation_count < MAX_EVALUATION_RETRIES:
        return "generate"

    return "respond"
