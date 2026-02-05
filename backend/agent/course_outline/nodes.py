"""
Node functions for the course outline generation workflow.

This module contains all the node functions used in the LangGraph workflow.
Each function represents a discrete step in the course outline generation process.
"""

from typing import Literal, List
import uuid

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.tools import BaseTool

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
from services.mcp_client import mcp_manager

from .state import CourseOutlineState
from .prompts import (
    get_system_prompt,
    get_evaluator_system_prompt,
    get_refinement_prompt,
)
from agent.model import model
from agent.tools import web_search, search_uploaded_documents


# Base tools (always available)
base_tools: List[BaseTool] = [web_search]

# All tools including document search
all_tools: List[BaseTool] = [web_search, search_uploaded_documents]


def get_all_tools(has_documents: bool = False) -> List[BaseTool]:
    """
    Get all available tools including MCP tools.

    Args:
        has_documents: Whether the user has uploaded documents.

    Returns:
        List of tools: base tools + MCP tools, optionally with document search.
    """
    tools = [web_search]

    # Add document search if documents are ingested
    if has_documents:
        tools.append(search_uploaded_documents)

    # Add MCP tools (Wikipedia, etc.)
    mcp_tools = mcp_manager.get_tools()
    tools.extend(mcp_tools)

    return tools


# For ToolNode - needs all possible tools registered (including MCP tools)
def get_tools_for_toolnode() -> List[BaseTool]:
    """Get all tools for ToolNode registration, including MCP tools."""
    return all_tools + mcp_manager.get_tools()


# Model configurations
model_with_structured_output = model.with_structured_output(CourseOutline)
model_with_evaluation_output = model.with_structured_output(EvaluationResult)


def get_model_with_tools(has_documents: bool):
    """Get model with appropriate tools based on whether documents are uploaded."""
    tools_to_use = get_all_tools(has_documents)
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

    For follow-up calls without new files, checks if documents were
    previously ingested for this session.

    Args:
        state: The current workflow state.

    Returns:
        Dict with has_ingested_documents flag.
    """
    file_contents = state.get("file_contents")
    thread_id = state["thread_id"]
    rag = get_rag_pipeline()

    if not file_contents:
        # No new files - check if documents were previously ingested for this session
        try:
            existing_docs = rag.list_documents(session_id=thread_id)
            has_existing = len(existing_docs) > 0
            print(
                f"[DEBUG ingest_documents] No new files for thread {thread_id}, "
                f"existing documents: {len(existing_docs)}"
            )
            return {"has_ingested_documents": has_existing}
        except Exception as e:
            print(f"[ERROR ingest_documents] Failed to check existing documents: {e}")
            return {"has_ingested_documents": False}

    try:
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
            # No valid new content - check for existing documents
            existing_docs = rag.list_documents(session_id=thread_id)
            has_existing = len(existing_docs) > 0
            print(
                f"[DEBUG ingest_documents] No valid content to ingest for thread {thread_id}, "
                f"existing documents: {len(existing_docs)}"
            )
            return {"has_ingested_documents": has_existing}

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

        # Build user message content with clear structure
        topic = state["topic"]
        num_classes = state["number_of_classes"]

        user_content = f"""## Course Outline Request

**Topic:** {topic}
**Number of Classes:** {num_classes}
**Output Language:** {state['language']}

Please generate a complete course outline with exactly {num_classes} classes.

Requirements:
- Each class must have clear, measurable learning objectives (using Bloom's taxonomy verbs)
- Topics should progress logically from foundational to advanced
- Include specific, varied activities for each class
- Ensure comprehensive coverage of the topic"""

        user_message = state.get("message") or ""
        if user_message.strip():
            user_content += (
                f"\n\n**Additional Instructions from User:**\n{user_message}"
            )

        messages.append(HumanMessage(content=user_content))

        return {"messages": messages}
    else:
        # For follow-ups, preserve existing messages and only append new user message
        # The existing messages are loaded from checkpoint automatically
        new_messages = []

        # Check if new documents were uploaded with this follow-up
        has_ingested_documents = state.get("has_ingested_documents", False)
        file_contents = state.get("file_contents")
        has_new_documents = has_ingested_documents and file_contents

        user_message = state.get("message") or ""
        if user_message.strip() or has_new_documents:
            # Build the follow-up content
            follow_up_content = "## Follow-up Request\n\n"

            # Add document search instruction if new documents were uploaded
            if has_new_documents:
                follow_up_content += """**IMPORTANT: New documents have been uploaded with this request.**

You MUST use the `search_uploaded_documents` tool before responding to search through these new reference materials. Query with 2-3 different searches to extract relevant information, then incorporate the findings into your response.

"""

            if user_message.strip():
                follow_up_content += user_message
            else:
                follow_up_content += "Please incorporate the information from the newly uploaded documents into your response."

            new_messages.append(HumanMessage(content=follow_up_content))

        # DEBUG: Log what we're returning
        print(f"[DEBUG build_messages] returning {len(new_messages)} new messages")
        print(f"[DEBUG build_messages] has_new_documents={has_new_documents}")
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

        # Generate structured output - the schema enforces the structure,
        # so we just need to pass the content for parsing
        response = model_with_structured_output.invoke(
            [HumanMessage(content=context_content)]
        )

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

    # Build evaluation messages with clear context
    language = state.get("language", "English")
    topic = state.get("topic", "Unknown")
    num_classes = state.get("number_of_classes", 0)

    evaluation_request = f"""## Course Outline Evaluation Request

**Expected Topic:** {topic}
**Expected Number of Classes:** {num_classes}

Please evaluate the following course outline against the rubric.
Score each dimension independently, then provide the overall weighted score.

---

## Course Outline to Evaluate

{content_to_evaluate}

---

Provide your evaluation with:
1. Score for each dimension (0.0-1.0)
2. Overall weighted score
3. Verdict (APPROVED if ≥ 0.8, NEEDS_REFINEMENT otherwise)
4. Brief reasoning
5. 1-3 specific, actionable suggestions if NEEDS_REFINEMENT"""

    evaluation_messages = [
        SystemMessage(content=get_evaluator_system_prompt(language)),
        HumanMessage(content=evaluation_request),
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
        print("[DEBUG route_after_evaluate] No evaluation history, going to respond")
        return "respond"

    # Check if score meets approval threshold
    if current_score >= EvaluationConfig.APPROVAL_THRESHOLD:
        print(
            f"[DEBUG route_after_evaluate] Score {current_score:.2f} >= {EvaluationConfig.APPROVAL_THRESHOLD}, APPROVED"
        )
        return "respond"

    # Check if we've exceeded max retries
    if evaluation_count >= EvaluationConfig.MAX_RETRIES:
        print(
            f"[DEBUG route_after_evaluate] Max retries ({EvaluationConfig.MAX_RETRIES}) reached, going to respond"
        )
        return "respond"

    # Check for plateau - if we have at least 2 evaluations, compare scores
    if len(evaluation_history) >= 2:
        previous_score = evaluation_history[-2].score
        improvement = current_score - previous_score

        if improvement < EvaluationConfig.MIN_IMPROVEMENT_THRESHOLD:
            print(
                f"[DEBUG route_after_evaluate] Plateau detected: improvement {improvement:.3f} < {EvaluationConfig.MIN_IMPROVEMENT_THRESHOLD}"
            )
            return "respond"

        print(
            f"[DEBUG route_after_evaluate] Score improved by {improvement:.3f}, continuing refinement"
        )

    print(
        f"[DEBUG route_after_evaluate] Score {current_score:.2f} < {EvaluationConfig.APPROVAL_THRESHOLD}, going to refine"
    )
    return "refine"
