"""
Graph construction for the presentation generation workflow.

This module defines the LangGraph StateGraph structure with nodes,
edges, and conditional routing for the presentation generation process.
"""

from functools import partial

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from agent.base.nodes import (
    ingest_documents,
    generate_content,
    refine_content,
    route_after_generate,
    route_after_refine,
    route_after_evaluate,
)
from agent.tool_config import get_tools_for_toolnode
from config import DBConfig

from .state import PresentationState, PresentationInput, PresentationOutput
from .nodes import (
    initialize_conversation,
    build_messages,
    evaluate_presentation,
    generate_structured_response,
)
from .prompts import get_refinement_prompt


def build_presentation_graph() -> StateGraph:
    """
    Build the presentation generation graph.

    Creates a StateGraph with the following workflow:

    1. initialize -> Initialize/load conversation metadata
    2. ingest_documents -> Process uploaded documents into vector DB
    3. build_messages -> Construct the message history
    4. generate -> Call the LLM with tools bound (initial generation)
    5. (conditional) -> Either use tools or go to evaluation
    6. tools -> Execute tool calls (loops back to generate)
    7. evaluate -> Evaluator agent scores quality (0.0-1.0)
    8. (conditional) -> Either refine or respond based on:
       - Score >= 0.8 -> respond (approved)
       - Score plateau detected -> respond (best effort)
       - Max retries reached -> respond
       - Otherwise -> refine
    9. refine -> Generate improved version using evaluation history
    10. (back to evaluate for re-scoring)
    11. respond -> Generate final structured output
    12. END

    Returns:
        The constructed (but not compiled) StateGraph.
    """
    workflow = StateGraph(
        PresentationState,
        input_schema=PresentationInput,
        output_schema=PresentationOutput,
    )

    # Create tool node instance with all tools including MCP tools
    all_tools = get_tools_for_toolnode()
    tool_node = ToolNode(all_tools)

    # Add nodes
    workflow.add_node("initialize", initialize_conversation)
    workflow.add_node("ingest_documents", ingest_documents)
    workflow.add_node("build_messages", build_messages)
    workflow.add_node("generate", generate_content)
    workflow.add_node("tools", tool_node)
    workflow.add_node("evaluate", evaluate_presentation)
    workflow.add_node(
        "refine",
        partial(refine_content, get_refinement_prompt=get_refinement_prompt),
    )
    workflow.add_node("tools_refine", tool_node)
    workflow.add_node("respond", generate_structured_response)

    # Define the workflow edges
    workflow.set_entry_point("initialize")
    workflow.add_edge("initialize", "ingest_documents")
    workflow.add_edge("ingest_documents", "build_messages")
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
    workflow = build_presentation_graph()
    memory = await AsyncSqliteSaver.from_conn_string(
        DBConfig.CHECKPOINTS_DB
    ).__aenter__()
    return workflow.compile(checkpointer=memory)
