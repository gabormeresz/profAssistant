"""
Pydantic schema for a single class/session within a course.

This module defines the CourseClass model used to validate and serialize
metadata for one class in a course sequence. It enforces constraints such as:
- class_number: sequential index starting from 1 (int, ge=1)
- class_title: descriptive title for the session (str, 3-200 chars)
- learning_objectives: 2-5 specific, measurable objectives (List[str])
- key_topics: 3-7 main topics or concepts covered (List[str])
- activities_projects: 1-5 hands-on activities, exercises, or projects (List[str])

The schema includes json_schema_extra example data to aid documentation and
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