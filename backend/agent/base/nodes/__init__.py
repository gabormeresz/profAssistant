"""
Shared node functions used across all generation workflows.

These nodes contain logic that is identical regardless of the content
type being generated (course outline, lesson plan, etc.).
Domain-specific nodes remain in each module's own nodes/ package.
"""

from .helpers import extract_content
from .ingest_documents import ingest_documents
from .routing import route_after_generate, route_after_refine, route_after_evaluate
from .generate import generate_content
from .refine import refine_content

__all__ = [
    "extract_content",
    "ingest_documents",
    "route_after_generate",
    "route_after_refine",
    "route_after_evaluate",
    "generate_content",
    "refine_content",
]
