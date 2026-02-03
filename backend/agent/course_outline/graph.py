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
    call_model,
    generate_structured_response,
    should_continue,
    tools,
)


def build_course_outline_graph() -> StateGraph:
    """
    Build the course outline generation graph.

    Creates a StateGraph with the following workflow:

    1. initialize -> Initialize/load conversation metadata
    2. build_messages -> Construct the message history
    3. agent -> Call the LLM with tools bound
    4. (conditional) -> Either use tools or respond
    5. tools -> Execute tool calls (loops back to agent)
    6. respond -> Generate final structured output
    7. END

    Returns:
        The constructed (but not compiled) StateGraph.
    """
    workflow = StateGraph(
        CourseOutlineState,
        input_schema=CourseOutlineInput,
        output_schema=CourseOutlineOutput,
    )

    # Add nodes
    workflow.add_node("initialize", initialize_conversation)
    workflow.add_node("build_messages", build_messages)
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", ToolNode(tools))
    workflow.add_node("respond", generate_structured_response)

    # Define the workflow edges
    workflow.set_entry_point("initialize")
    workflow.add_edge("initialize", "build_messages")
    workflow.add_edge("build_messages", "agent")

    # Conditional edge from agent: either use tools or respond
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "respond": "respond",
        },
    )

    # Tool loop: after tools, go back to agent
    workflow.add_edge("tools", "agent")

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


def get_graph_visualization() -> str:
    """
    Get a text representation of the graph structure.

    Useful for debugging and documentation.

    Returns:
        ASCII representation of the graph.
    """
    return """
    Course Outline Generation Graph
    ================================
    
    ┌─────────────┐
    │   START     │
    └──────┬──────┘
           │
           ▼
    ┌─────────────┐
    │ initialize  │  ← Create/load conversation
    └──────┬──────┘
           │
           ▼
    ┌─────────────┐
    │build_messages│  ← Construct prompts
    └──────┬──────┘
           │
           ▼
    ┌─────────────┐
    │   agent     │  ← LLM with tools
    └──────┬──────┘
           │
           ▼
    ┌─────────────┐
    │should_continue│
    └──────┬──────┘
           │
     ┌─────┴─────┐
     │           │
     ▼           ▼
┌─────────┐ ┌─────────┐
│  tools  │ │ respond │
└────┬────┘ └────┬────┘
     │           │
     └───►agent  │
                 ▼
          ┌─────────┐
          │   END   │
          └─────────┘
    """
