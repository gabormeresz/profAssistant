"""
Pydantic schemas for lesson plans metadata.

This module provides models to represent a complete lesson: LessonPlan,
LessonSection, and ActivityPlan. Each model captures structured information
about a class/session (e.g., class number and title, learning objectives,
an ordered lesson breakdown, activities, and homework). 

The schema includes json_schema_extra example data to aid documentation and
OpenAPI/JSON Schema generation.
"""


from typing import List
from pydantic import BaseModel, Field

class LessonSection(BaseModel):
    """
    Represents a structured part of the lesson (e.g., Opening, Instruction, Practice).
    """
    section_title: str = Field(..., description="Name of this part of the lesson")
    description: str = Field(..., description="What happens during this section")


class ActivityPlan(BaseModel):
    """
    Detailed plan for a hands-on activity or exercise.
    """
    name: str = Field(..., description="Name or title of the activity")
    objective: str = Field(..., description="Purpose or learning goal of this activity")
    instructions: str = Field(..., description="Step-by-step instructions for students")


class LessonPlan(BaseModel):
    """
    Detailed instructional plan expanding on a CourseClass.
    """
    class_number: int = Field(..., description="Class number from the course outline", ge=1)
    class_title: str = Field(..., description="Title of the lesson")
    
    learning_objective: str = Field(..., description="Main learning goal of this lesson")
    
    key_points: List[str] = Field(
        ..., 
        description="Essential concepts or topics covered (2–10 items)",
        min_length=2,
        max_length=10
    )

    lesson_breakdown: List[LessonSection] = Field(
        ...,
        description="Step-by-step flow of the lesson (e.g., Opening, Teaching, Practice, Summary)",
        min_length=2,
        max_length=10
    )

    activities: List[ActivityPlan] = Field(
        default_factory=list,
        description="Hands-on tasks, exercises, or projects students will do",
        min_length=1,
        max_length=5
    )

    homework: str = Field(
        ...,
        description="Homework or follow-up work assigned to students"
    )

    extra_activities: str = Field(
        ...,
        description="Optional enrichment or bonus activities for early finishers or advanced learners"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "class_number": 1,
                "class_title": "Introduction to Python",
                "learning_objective": "Students will be able to write a simple Python script and explain its parts.",
                "key_points": [
                    "What programming is",
                    "Variables and data types",
                    "Basic input and output in Python"
                ],
                "lesson_breakdown": [
                    {
                        "section_title": "Opening",
                        "description": "Ask: 'What can programming solve?' Show a simple demo program."
                    },
                    {
                        "section_title": "New Material",
                        "description": "Explain variables, input(), output, and show a live coding example."
                    },
                    {
                        "section_title": "Guided Practice",
                        "description": "Students follow along to write a script that prints their name."
                    },
                    {
                        "section_title": "Closing",
                        "description": "Quick recap of key concepts and address student questions."
                    }
                ],
                "activities": [
                    {
                        "name": "Hello World Exercise",
                        "objective": "Introduce basic Python syntax",
                        "instructions": "Open IDE → Write print('Hello, World!') → Run the script"
                    }
                ],
                "homework": "Write a script that asks for your name and age, then prints a personalized greeting.",
                "extra_activities": "Optional: Students explore creating a simple number guessing game."
            }
        }
    }