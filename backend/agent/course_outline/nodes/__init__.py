"""
Node functions for the course outline generation workflow.

This package contains all node functions used in the LangGraph workflow,
organized by responsibility (one node per file).
"""

from .initialize_conversation import initialize_conversation
from .ingest_documents import ingest_documents
from .build_messages import build_messages
from .generate_outline import generate_outline
from .refine_outline import refine_outline
from .evaluation import evaluate_outline
from .routing import route_after_generate, route_after_refine, route_after_evaluate
from .response import generate_structured_response

__all__ = [
    # Initialization
    "initialize_conversation",
    "ingest_documents",
    # Message building
    "build_messages",
    # Generation
    "generate_outline",
    "refine_outline",
    # Evaluation
    "evaluate_outline",
    # Routing
    "route_after_generate",
    "route_after_refine",
    "route_after_evaluate",
    # Response
    "generate_structured_response",
]
