"""
Pydantic schemas for content evaluation.

This module defines the EvaluationResult schema used by evaluator
agents to provide structured feedback on generated educational content
(course outlines, lesson plans, presentations, tests, etc.).
"""

from typing import List, Literal
from pydantic import BaseModel, Field


class ScoreBreakdown(BaseModel):
    """
    Detailed scoring breakdown for different quality dimensions.
    Each score is from 0.0 to 1.0.
    """

    learning_objectives: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Score for clarity and measurability of learning objectives",
    )
    content_coverage: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Score for comprehensiveness and logical topic coverage",
    )
    progression: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Score for logical flow from basic to advanced concepts",
    )
    activities: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Score for engagement and alignment of activities with objectives",
    )
    completeness: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Score for sufficient detail in each class/section",
    )


class Suggestion(BaseModel):
    """
    A single improvement suggestion for the evaluated content.
    """

    dimension: Literal[
        "learning_objectives",
        "content_coverage",
        "progression",
        "activities",
        "completeness",
    ] = Field(
        ...,
        description="The dimension this suggestion addresses",
    )
    text: str = Field(
        ...,
        description="A specific, actionable improvement suggestion",
        min_length=10,
        max_length=200,
    )


class EvaluationResult(BaseModel):
    """
    Represents the result of evaluating generated educational content.

    The evaluator agent uses this schema to provide structured
    feedback about the quality of generated content across different
    content types (course outlines, lesson plans, presentations, tests).
    """

    score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall quality score from 0.0 (poor) to 1.0 (excellent). Score >= 0.8 is considered approved.",
    )
    score_breakdown: ScoreBreakdown = Field(
        ...,
        description="Detailed scores for each quality dimension",
    )
    verdict: Literal["APPROVED", "NEEDS_REFINEMENT"] = Field(
        ...,
        description="The evaluation verdict: APPROVED if score >= 0.8, NEEDS_REFINEMENT otherwise",
    )
    reasoning: str = Field(
        ...,
        description="Brief explanation of the assessment and why the verdict was given",
        min_length=10,
        max_length=1000,
    )
    suggestions: List[Suggestion] = Field(
        default_factory=list,
        description="List of specific, actionable improvements for lowest-scoring dimensions. Empty if approved.",
        max_length=5,
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "score": 0.85,
                    "score_breakdown": {
                        "learning_objectives": 0.9,
                        "content_coverage": 0.85,
                        "progression": 0.8,
                        "activities": 0.85,
                        "completeness": 0.85,
                    },
                    "verdict": "APPROVED",
                    "reasoning": "The content is well-structured, comprehensive, and meets all quality standards for educational material.",
                    "suggestions": [],
                },
                {
                    "score": 0.65,
                    "score_breakdown": {
                        "learning_objectives": 0.5,
                        "content_coverage": 0.7,
                        "progression": 0.75,
                        "activities": 0.6,
                        "completeness": 0.7,
                    },
                    "verdict": "NEEDS_REFINEMENT",
                    "reasoning": "The content lacks clarity in learning objectives and activities need improvement.",
                    "suggestions": [
                        {
                            "dimension": "learning_objectives",
                            "text": "Add more specific, measurable learning objectives using action verbs",
                        },
                        {
                            "dimension": "activities",
                            "text": "Include more interactive activities aligned with learning objectives",
                        },
                    ],
                },
            ]
        }
    }
