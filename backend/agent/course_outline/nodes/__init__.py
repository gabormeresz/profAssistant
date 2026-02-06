"""
Domain-specific node functions for the course outline generation workflow.

Shared nodes (ingest_documents, routing, generate, refine) are in agent.base.nodes.
"""

from .initialize_conversation import initialize_conversation
from .build_messages import build_messages
from .evaluation import evaluate_outline
from .response import generate_structured_response

__all__ = [
    "initialize_conversation",
    "build_messages",
    "evaluate_outline",
    "generate_structured_response",
]
