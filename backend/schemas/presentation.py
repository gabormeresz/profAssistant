"""
Pydantic schemas for presentations.

This module defines the Presentation and Slide schemas used to validate
and serialize a complete educational presentation: a course title, lesson
title, class number, and an ordered sequence of slides.

The schema includes json_schema_extra example data to aid documentation and
OpenAPI/JSON Schema generation.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class Slide(BaseModel):
    """
    Represents a single slide in the presentation.
    """

    slide_number: int = Field(..., description="Sequential number of the slide", ge=1)
    title: str = Field(..., description="The heading of the slide")
    bullet_points: List[str] = Field(
        ...,
        description="Bullet points for the slide (1-6 items)",
        min_length=1,
        max_length=6,
    )
    speaker_notes: Optional[str] = Field(
        None, description="Detailed explanation for the instructor"
    )
    visual_suggestion: Optional[str] = Field(
        None, description="Description of a recommended image or chart"
    )


class Presentation(BaseModel):
    """
    Complete presentation structure for an educational lesson.
    """

    course_title: str = Field(
        ..., description="Title of the subject/course", min_length=5, max_length=200
    )
    lesson_title: str = Field(
        ..., description="Title of the specific lesson", min_length=5, max_length=200
    )
    class_number: Optional[int] = Field(
        None, description="Class number from the course outline (optional)", ge=1
    )
    slides: List[Slide] = Field(
        ...,
        description="Ordered sequence of slides (5-15 slides)",
        min_length=5,
        max_length=15,
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "course_title": "Introduction to Python Programming",
                "lesson_title": "Variables and Data Types",
                "class_number": 2,  # optional
                "slides": [
                    {
                        "slide_number": 1,
                        "title": "Welcome & Recap",
                        "bullet_points": [
                            "Review of previous lesson",
                            "Today's agenda: variables, types, and assignments",
                        ],
                        "speaker_notes": "Briefly recap what students learned in the first class.",
                        "visual_suggestion": None,
                    },
                    {
                        "slide_number": 2,
                        "title": "What Are Variables?",
                        "bullet_points": [
                            "A variable is a named container for data",
                            "Created with the assignment operator =",
                            "Variable names should be descriptive",
                        ],
                        "speaker_notes": "Use a box analogy: a variable is like a labeled box that holds a value.",
                        "visual_suggestion": "Diagram showing labeled boxes with values inside",
                    },
                ],
            }
        }
    }
