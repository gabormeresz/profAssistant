from typing import Optional, List, Callable, Annotated
from langchain.tools import tool
from langchain_core.tools import StructuredTool, InjectedToolArg
from langchain_core.runnables import RunnableConfig
from dotenv import load_dotenv
from langchain_community.utilities import GoogleSerperAPIWrapper

from services.rag_pipeline import get_rag_pipeline

load_dotenv()

# Setup tools using the new @tool decorator
serper = GoogleSerperAPIWrapper()


@tool
def web_search(query: str) -> str:
    """Useful for when you need more information from an online search."""
    return serper.run(query)


@tool
def search_uploaded_documents(
    query: str,
    n_results: int = 5,
    config: Annotated[RunnableConfig, InjectedToolArg] = None,
) -> str:
    """
    Search through uploaded documents for relevant information.

    Use this tool when you need to find specific information from documents
    that the user has uploaded. The search uses semantic similarity to find
    the most relevant content.

    Args:
        query: The search query describing what information you need
        n_results: Number of results to return (default: 5)

    Returns:
        Relevant document excerpts with source information
    """
    # Extract thread_id from config (injected by LangGraph)
    session_id = None
    if config:
        session_id = config.get("configurable", {}).get("thread_id")

    rag = get_rag_pipeline()
    results = rag.query(query, n_results=n_results, session_id=session_id)

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
