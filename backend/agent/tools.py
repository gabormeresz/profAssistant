from typing import Optional, List, Callable, Annotated, Any
from langchain.tools import tool
from langchain_core.tools import StructuredTool
from langgraph.prebuilt import InjectedState
from dotenv import load_dotenv

from services.rag_pipeline import get_rag_pipeline

load_dotenv()


@tool
async def search_uploaded_documents(
    query: str,
    n_results: int = 5,
    state: Annotated[Optional[dict[str, Any]], InjectedState] = None,
) -> str:
    """
    Search through the user's uploaded documents for relevant content.

    Use this tool when the user has uploaded reference materials and you need to:
    - Find specific concepts, definitions, or explanations from their documents
    - Identify the structure or organization used in their materials
    - Extract examples, exercises, or activities from uploaded content
    - Understand the user's preferred terminology or approach

    IMPORTANT: Make multiple searches with different queries to thoroughly
    explore the documents. Use natural language queries relevant to your topic.

    Example queries (mix broad and specific based on your needs):
    Broad (for course structure):
    - "main topics and themes covered"
    - "introduction and foundational concepts of ..."
    - "progression from beginner to advanced"

    Specific (for detailed content):
    - "photosynthesis light reactions process"
    - "market equilibrium price determination"
    - "Renaissance art characteristics and techniques"

    Args:
        query: A natural language search query. Be specific and descriptive.
               Write queries as if you're asking a question or describing what you need.
        n_results: Number of results to return (default: 5, max recommended: 10)

    Returns:
        Relevant excerpts from the uploaded documents with source information.
        Returns "No relevant information found" if nothing matches.
    """
    # Extract thread_id from state (injected by LangGraph ToolNode)
    session_id = None
    if state:
        session_id = state.get("thread_id")
    print(f"[Tool] State thread_id: {session_id}")

    rag = get_rag_pipeline()
    results = await rag.query(query, n_results=n_results, session_id=session_id)

    if not results:
        return "No relevant information found in the uploaded documents."

    # Format results for the agent
    formatted_chunks = []
    for i, result in enumerate(results, 1):
        source = result["metadata"].get("filename", "Unknown")
        similarity = result.get("similarity_score", 0)
        content = result["content"]
        formatted_chunks.append(
            f"[{i}] Source: {source} (relevance: {similarity:.2f})\n{content}"
        )

    return "\n\n---\n\n".join(formatted_chunks)
