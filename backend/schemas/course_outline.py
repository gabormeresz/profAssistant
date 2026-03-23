"""
Pydantic schemas for course outlines and class/session metadata.

This module defines the CourseOutline and CourseClass schemas used to validate
and serialize a complete course: a course_title and an ordered list of
CourseClass items.

CourseClass enforces constraints such as:
- class_number: sequential index starting from 1 (int, ge=1)
- class_title: descriptive title for the session (str, 3-200 chars)
- learning_objectives: 2-5 specific, measurable objectives (List[str])
- key_topics: 3-7 main topics or concepts covered (List[str])
- activities_projects: 1-5 hands-on activities, exercises, or projects (List[str])

The schemas include json_schema_extra example data to aid documentation and
OpenAPI/JSON Schema generation.
"""

from typing import List
from pydantic import BaseModel, Field


class CourseClass(BaseModel):
    """
    Represents a single class or session within a course.
    """
    class_number: int = Field(
        ..., 
        description="The sequential number of the class (starting from 1)",
        ge=1
    )
    class_title: str = Field(
        ..., 
        description="A clear, descriptive title for the class/session",
        min_length=3,
        max_length=200
    )
    learning_objectives: List[str] = Field(
        ..., 
        description="Specific, measurable learning goals for this class (2-5 objectives)",
        min_length=2,
        max_length=5
    )
    key_topics: List[str] = Field(
        ..., 
        description="Main topics and concepts covered in this class (3-7 topics)",
        min_length=3,
        max_length=7
    )
    activities_projects: List[str] = Field(
        ..., 
        description="Hands-on activities, exercises, or projects for this class (1-5 activities)",
        min_length=1,
        max_length=3
    )


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
                            "Set up a Python development environment and run scripts from the command line",
                            "Distinguish between Python's core data types (int, float, str, bool) and apply type conversion"
                        ],
                        "key_topics": [
                            "Installing Python and configuring a local development environment",
                            "Variables, naming conventions, and dynamic typing",
                            "Core data types: int, float, str, bool and their conversions"
                        ],
                        "activities_projects": [
                            "Write a short script that reads user input, converts types, and prints formatted output"
                        ]
                    }
                ]
            }
        }
    }
