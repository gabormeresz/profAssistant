"""
Pydantic schemas for content evaluation.

This module defines the EvaluationResult schema used by evaluator
agents to provide structured feedback on generated educational content
(course outlines, lesson plans, presentations, tests, etc.).
"""

from typing import List, Literal
from pydantic import BaseModel, Field


class Suggestion(BaseModel):
    """
    A single improvement suggestion for the evaluated content.
    """
    text: str = Field(
        ...,
        description="A specific, actionable improvement suggestion",
        min_length=10,
        max_length=100
    )


class EvaluationResult(BaseModel):
    """
    Represents the result of evaluating generated educational content.
    
    The evaluator agent uses this schema to provide structured
    feedback about the quality of generated content across different
    content types (course outlines, lesson plans, presentations, tests).
    """
    verdict: Literal["APPROVED", "NEEDS_REFINEMENT"] = Field(
        ...,
        description="The evaluation verdict: APPROVED if the content meets quality standards, NEEDS_REFINEMENT if improvements are needed"
    )
    reasoning: str = Field(
        ...,
        description="Brief explanation of the assessment and why the verdict was given",
        min_length=10,
        max_length=1000
    )
    suggestions: List[Suggestion] = Field(
        default_factory=list,
        description="List of specific, actionable improvements needed. Empty if approved.",
        max_length=10
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "verdict": "APPROVED",
                    "reasoning": "The content is well-structured, comprehensive, and meets all quality standards for educational material.",
                    "suggestions": []
                },
                {
                    "verdict": "NEEDS_REFINEMENT",
                    "reasoning": "The content lacks clarity in some sections and could benefit from additional detail.",
                    "suggestions": [
                        "Add more specific learning objectives",
                        "Improve the logical flow between sections",
                        "Include more practical examples or activities"
                    ]
                }
            ]
        }
    }
