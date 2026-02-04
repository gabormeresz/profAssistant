"""
Node functions for the course outline generation workflow.

This module contains all the node functions used in the LangGraph workflow.
Each function represents a discrete step in the course outline generation process.
"""

from typing import Literal
import uuid

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from config import EvaluationConfig
from schemas.course_outline import CourseOutline
from schemas.evaluation import EvaluationResult
from schemas.conversation import (
    ConversationType,
    CourseOutlineCreate,
    CourseOutlineMetadata,
)
from services.conversation_manager import conversation_manager
from services.rag_pipeline import get_rag_pipeline
from utils.context_builders import build_file_contents_message

from .state import CourseOutlineState
from .prompts import (
    get_system_prompt,
    get_structured_output_prompt,
    get_evaluator_system_prompt,
    get_refinement_prompt,
)
from agent.model import model
from agent.tools import web_search, search_uploaded_documents


# Base tools (always available)
base_tools = [web_search]

# All tools including document search
all_tools = [web_search, search_uploaded_documents]

# For ToolNode - needs all possible tools registered
tools = all_tools

# Model configurations
model_with_structured_output = model.with_structured_output(CourseOutline)
model_with_evaluation_output = model.with_structured_output(EvaluationResult)


def get_model_with_tools(has_documents: bool):
    """Get model with appropriate tools based on whether documents are uploaded."""
    tools_to_use = all_tools if has_documents else base_tools
    return model.bind_tools(tools_to_use)


def initialize_conversation(state: CourseOutlineState) -> dict:
    """
    Initialize or load conversation metadata.

    For first calls, creates a new conversation record.
    For follow-ups, increments the message count, loads existing metadata,
    and resets evaluation state for a fresh evaluation cycle.

    Args:
        state: The current workflow state.

    Returns:
        Updated state with thread_id, is_first_call flag, and reset evaluation state.
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
                    state.get("message")
                    if (state.get("message") or "").strip()
                    else None
                ),
            ),
        )
        return {
            "thread_id": thread_id,
            "is_first_call": is_first_call,
            "evaluation_count": 0,
            "evaluation_history": [],
            "current_score": None,
        }
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
                # Reset evaluation state for fresh evaluation cycle
                "evaluation_count": 0,
                "evaluation_history": [],
                "current_score": None,
            }

        # Fallback if conversation not found
        return {
            "thread_id": thread_id,
            "is_first_call": is_first_call,
            "evaluation_count": 0,
            "evaluation_history": [],
            "current_score": None,
        }


def ingest_documents(state: CourseOutlineState) -> dict:
    """
    Ingest uploaded documents into the vector database.

    This node processes any uploaded file contents and stores them
    in ChromaDB for later retrieval during generation. The thread_id
    is used as session_id to scope queries to the current conversation.

    Args:
        state: The current workflow state.

    Returns:
        Dict with has_uploaded_documents flag.
    """
    file_contents = state.get("file_contents")
    thread_id = state["thread_id"]

    if not file_contents:
        print(f"[DEBUG ingest_documents] No files to ingest for thread {thread_id}")
        return {"has_ingested_documents": False}

    try:
        rag = get_rag_pipeline()

        # Prepare documents for ingestion
        documents = [
            {"content": f["content"], "filename": f["filename"]}
            for f in file_contents
            if f.get("content", "").strip()
        ]

        if documents:
            results = rag.ingest_documents(
                documents=documents,
                session_id=thread_id,
            )
            print(
                f"[DEBUG ingest_documents] Ingested {len(results)} documents "
                f"({sum(r.chunk_count for r in results)} chunks) for thread {thread_id}"
            )
            return {"has_ingested_documents": True}
        else:
            print(
                f"[DEBUG ingest_documents] No valid content to ingest for thread {thread_id}"
            )
            return {"has_ingested_documents": False}

    except Exception as e:
        print(f"[ERROR ingest_documents] Failed to ingest documents: {e}")
        # Don't fail the workflow, just log the error
        return {"has_ingested_documents": False}


def build_messages(state: CourseOutlineState) -> dict:
    """
    Build messages for the agent.

    For first calls: Creates fresh system message and user prompt.
    For follow-ups: Preserves existing messages and appends new user message.

    The messages from previous runs are automatically loaded from the
    checkpoint by LangGraph when using a checkpointer.

    Args:
        state: The current workflow state.

    Returns:
        Updated state with messages list.
    """
    is_first_call = state.get("is_first_call", True)
    user_message = state.get("message", "")

    # DEBUG: Log what we're working with
    print(
        f"[DEBUG build_messages] is_first_call={is_first_call}, user_message='{user_message[:50] if user_message else ''}'"
    )
    print(
        f"[DEBUG build_messages] existing messages count: {len(state.get('messages', []))}"
    )

    if is_first_call:
        # For first call, create fresh messages
        messages = []

        # Add system message with document search instruction if documents are ingested
        has_ingested_documents = state.get("has_ingested_documents", False)
        system_prompt = get_system_prompt(state["language"], has_ingested_documents)
        messages.append(SystemMessage(content=system_prompt))

        # Build user message content
        user_content_parts = []
        user_content_parts.append(
            f"Create a course outline on '{state['topic']}' "
            f"with {state['number_of_classes']} classes."
        )

        user_message = state.get("message") or ""
        if user_message.strip():
            user_content_parts.append(user_message)

        file_contents = state.get("file_contents")
        if file_contents:
            user_content_parts.append(build_file_contents_message(file_contents))

        if user_content_parts:
            messages.append(HumanMessage(content="\n\n".join(user_content_parts)))

        return {"messages": messages}
    else:
        # For follow-ups, preserve existing messages and only append new user message
        # The existing messages are loaded from checkpoint automatically
        new_messages = []

        # Build new user message content
        user_content_parts = []

        user_message = state.get("message") or ""
        if user_message.strip():
            user_content_parts.append(user_message)

        file_contents = state.get("file_contents")
        if file_contents:
            user_content_parts.append(build_file_contents_message(file_contents))

        # Only add if there's actual new content
        if user_content_parts:
            new_messages.append(HumanMessage(content="\n\n".join(user_content_parts)))

        # DEBUG: Log what we're returning
        print(f"[DEBUG build_messages] returning {len(new_messages)} new messages")
        if new_messages:
            print(
                f"[DEBUG build_messages] new message content: {new_messages[0].content[:100]}"
            )

        # Return new messages to be appended (MessagesState will handle accumulation)
        return {"messages": new_messages}


def generate_outline(state: CourseOutlineState) -> dict:
    """
    Generate the initial course outline using the LLM.

    This node invokes the model and allows it to make tool calls
    if it needs additional information. The response is stored in
    agent_response (not messages) to allow for clean JSON formatting later.

    This node is only for initial generation. Refinement is handled
    by a separate refine_outline node.

    Args:
        state: The current workflow state.

    Returns:
        Updated state with the model's response in agent_response.
        If tools are called, also updates messages for tool execution.
    """
    messages = list(state["messages"])

    # Get model with appropriate tools based on whether documents are ingested
    has_documents = state.get("has_ingested_documents", False)
    model_with_tools = get_model_with_tools(has_documents)

    response = model_with_tools.invoke(messages)

    # If there are tool calls, we need to add to messages for the ToolNode
    if hasattr(response, "tool_calls") and response.tool_calls:
        return {"messages": [response], "agent_response": response}

    # Otherwise, just store in agent_response (don't pollute messages with raw response)
    return {"agent_response": response}


def refine_outline(state: CourseOutlineState) -> dict:
    """
    Refine the course outline based on evaluation feedback.

    This node takes the evaluation history and uses it to generate
    an improved version of the course outline, focusing on the
    lowest-scoring dimensions.

    Args:
        state: The current workflow state.

    Returns:
        Updated state with the refined response in agent_response.
    """
    messages = list(state["messages"])

    # Get the previous response content for context
    agent_response = state.get("agent_response")
    original_content = ""
    if agent_response and hasattr(agent_response, "content"):
        original_content = str(agent_response.content)

    # Get evaluation history for context
    evaluation_history = state.get("evaluation_history", [])
    language = state.get("language", "English")

    refinement_prompt = get_refinement_prompt(
        original_content, evaluation_history, language
    )
    refinement_message = HumanMessage(content=refinement_prompt)
    messages.append(refinement_message)

    # Get model with appropriate tools based on whether documents are ingested
    has_documents = state.get("has_ingested_documents", False)
    model_with_tools = get_model_with_tools(has_documents)

    response = model_with_tools.invoke(messages)

    # If there are tool calls, we need to add both the refinement prompt and response to messages
    if hasattr(response, "tool_calls") and response.tool_calls:
        return {"messages": [refinement_message, response], "agent_response": response}

    # Otherwise, just store in agent_response (don't pollute messages with prompts)
    return {"agent_response": response}


def route_after_refine(
    state: CourseOutlineState,
) -> Literal["tools_refine", "evaluate"]:
    """
    Route the workflow after refinement.

    Checks if the refiner wants to use tools or if it's ready to be evaluated.

    Args:
        state: The current workflow state.

    Returns:
        "tools_refine" if tools should be called, "evaluate" otherwise.
    """
    agent_response = state.get("agent_response")

    if not agent_response:
        return "evaluate"

    # Check if the model wants to use tools
    if isinstance(agent_response, AIMessage) and agent_response.tool_calls:
        return "tools_refine"

    return "evaluate"


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


def evaluate_outline(state: CourseOutlineState) -> dict:
    """
    Evaluate the generated course outline for quality using scoring.

    This node acts as an evaluator agent that assesses the quality of
    the generated content across multiple dimensions and provides
    a numeric score. Uses structured output for reliable parsing.

    Note: Since evaluation_history doesn't use operator.add, we manually
    accumulate by getting existing history and appending to it.

    Args:
        state: The current workflow state.

    Returns:
        Updated state with evaluation_count, evaluation_history, and current_score.
    """
    # Get current evaluation count (default to 0 if not set)
    current_count = state.get("evaluation_count", 0)
    # Get existing evaluation history (already reset by initialize_conversation for follow-ups)
    existing_history = state.get("evaluation_history", []) or []

    # If we've already done max retries, skip evaluation
    if current_count >= EvaluationConfig.MAX_RETRIES:
        return {
            "evaluation_count": current_count,
        }

    # Get the agent's response to evaluate
    agent_response = state.get("agent_response")
    if not agent_response:
        return {
            "evaluation_count": current_count + 1,
            "current_score": 0.0,
            "evaluation_history": existing_history,
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
                "current_score": 0.0,
                "evaluation_history": existing_history,
            }

        # Add to evaluation history (manually accumulate) and update current score
        updated_history = existing_history + [evaluation_result]
        return {
            "evaluation_count": current_count + 1,
            "evaluation_history": updated_history,
            "current_score": evaluation_result.score,
        }

    except Exception:
        # If evaluation fails, return low score but still increment count
        # Don't add to history since we don't have a valid evaluation
        return {
            "evaluation_count": current_count + 1,
            "current_score": 0.0,
            "evaluation_history": existing_history,
        }


def route_after_evaluate(state: CourseOutlineState) -> Literal["refine", "respond"]:
    """
    Route the workflow after evaluation with plateau detection.

    Decides whether to refine based on:
    1. Score threshold (>= 0.8 means approved)
    2. Max retries reached
    3. Score plateau (not improving significantly)
    4. Empty evaluation history (evaluation failed)

    Args:
        state: The current workflow state.

    Returns:
        "refine" if more refinement needed, "respond" otherwise.
    """
    evaluation_count = state.get("evaluation_count", 0)
    current_score = state.get("current_score") or 0.0
    evaluation_history = state.get("evaluation_history", [])

    # If evaluation history is empty (evaluation failed), go to respond
    # We can't refine without evaluation feedback
    if not evaluation_history:
        return "respond"

    # Check if score meets approval threshold
    if current_score >= EvaluationConfig.APPROVAL_THRESHOLD:
        return "respond"

    # Check if we've exceeded max retries
    if evaluation_count >= EvaluationConfig.MAX_RETRIES:
        return "respond"

    return "refine"
