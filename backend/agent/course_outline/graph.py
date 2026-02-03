"""
Graph construction for the course outline generation workflow.

This module defines the LangGraph StateGraph structure with nodes,
edges, and conditional routing for the course outline generation process.
"""

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from .state import CourseOutlineState, CourseOutlineInput, CourseOutlineOutput
from .nodes import (
    initialize_conversation,
    build_messages,
    generate_outline,
    refine_outline,
    generate_structured_response,
    route_after_generate,
    route_after_refine,
    evaluate_outline,
    route_after_evaluate,
    tools,
)


def build_course_outline_graph() -> StateGraph:
    """
    Build the course outline generation graph.

    Creates a StateGraph with the following workflow:

    1. initialize -> Initialize/load conversation metadata
    2. build_messages -> Construct the message history
    3. generate -> Call the LLM with tools bound (initial generation)
    4. (conditional) -> Either use tools or go to evaluation
    5. tools -> Execute tool calls (loops back to generate)
    6. evaluate -> Evaluator agent scores quality (0.0-1.0)
    7. (conditional) -> Either refine or respond based on:
       - Score >= 0.8 -> respond (approved)
       - Score plateau detected -> respond (best effort)
       - Max retries reached -> respond
       - Otherwise -> refine
    8. refine -> Generate improved version using evaluation history
    9. (back to evaluate for re-scoring)
    10. respond -> Generate final structured output
    11. END

    The evaluate-refine loop runs a maximum of 3 times or until:
    - Score reaches 0.8 (approval threshold)
    - Score stops improving (plateau detection)

    Returns:
        The constructed (but not compiled) StateGraph.
    """
    workflow = StateGraph(
        CourseOutlineState,
        input_schema=CourseOutlineInput,
        output_schema=CourseOutlineOutput,
    )

    # Create tool node instance (reused for both generate and refine)
    tool_node = ToolNode(tools)

    # Add nodes
    workflow.add_node("initialize", initialize_conversation)
    workflow.add_node("build_messages", build_messages)
    workflow.add_node("generate", generate_outline)
    workflow.add_node("tools", tool_node)
    workflow.add_node("evaluate", evaluate_outline)
    workflow.add_node("refine", refine_outline)
    workflow.add_node("tools_refine", tool_node)  # Same ToolNode, different graph entry
    workflow.add_node("respond", generate_structured_response)

    # Define the workflow edges
    workflow.set_entry_point("initialize")
    workflow.add_edge("initialize", "build_messages")
    workflow.add_edge("build_messages", "generate")

    # Conditional edge from generate: either use tools or go to evaluation
    workflow.add_conditional_edges(
        "generate",
        route_after_generate,
        {
            "tools": "tools",
            "evaluate": "evaluate",
        },
    )

    # Tool loop: after tools, go back to generate
    workflow.add_edge("tools", "generate")

    # Conditional edge from evaluate: either refine or respond
    workflow.add_conditional_edges(
        "evaluate",
        route_after_evaluate,
        {
            "refine": "refine",
            "respond": "respond",
        },
    )

    # Conditional edge from refine: either use tools or go to evaluation
    workflow.add_conditional_edges(
        "refine",
        route_after_refine,
        {
            "tools_refine": "tools_refine",
            "evaluate": "evaluate",
        },
    )

    # Tool loop for refine: after tools_refine, go back to refine
    workflow.add_edge("tools_refine", "refine")

    # Final response ends the graph
    workflow.add_edge("respond", END)

    return workflow


async def create_compiled_graph(thread_id: str | None = None):
    """
    Create and compile the graph with a checkpointer.

    Args:
        thread_id: Optional thread ID for conversation continuity.

    Returns:
        A context manager that yields the compiled graph.
    """
    workflow = build_course_outline_graph()
    memory = await AsyncSqliteSaver.from_conn_string("checkpoints.db").__aenter__()
    return workflow.compile(checkpointer=memory), memory
