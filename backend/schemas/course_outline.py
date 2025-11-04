"""
Pydantic schemas for course outlines and class/session metadata.

This module defines the CourseOutline schema used to validate and serialize
a complete course: a course_title and an ordered list of CourseClass items.

The schema includes json_schema_extra example data to aid documentation and
OpenAPI/JSON Schema generation.
"""

from typing import List
from pydantic import BaseModel, Field
from .course_class import CourseClass

class CourseOutline(BaseModel):
    """
    Represents a complete course outline with title and list of classes.
    """
    course_title: str = Field(
        ..., 
        description="The complete title of the course",
        min_length=5,
        max_length=200
    )
    classes: List[CourseClass] = Field(
        ..., 
        description="Ordered list of classes/sessions in the course (typically 5-15 classes)",
        min_length=1,
        max_length=20
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "course_title": "Introduction to Python Programming",
                "classes": [
                    {
                        "class_number": 1,
                        "class_title": "Getting Started with Python",
                        "learning_objectives": [
                            "Set up Python development environment",
                            "Understand Python syntax basics"
                        ],
                        "key_topics": [
                            "Python installation",
                            "IDE setup",
                            "Basic syntax"
                        ],
                        "activities_projects": [
                            "Install Python and IDE",
                            "Write hello world program"
                        ]
                    }
                ]
            }
        }
    }
