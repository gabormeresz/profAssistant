"""
Course outline schema definitions using Pydantic models.
This module defines the data structures for course outlines including
classes, learning objectives, key topics, and activities.
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
        max_length=5
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "class_number": 1,
                "class_title": "Introduction to Programming Concepts",
                "learning_objectives": [
                    "Understand basic programming concepts",
                    "Learn about variables and data types"
                ],
                "key_topics": [
                    "Variables and data types",
                    "Basic syntax",
                    "Hello World program"
                ],
                "activities_projects": [
                    "Write your first program",
                    "Variable declaration exercises"
                ]
            }
        }
    }


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
