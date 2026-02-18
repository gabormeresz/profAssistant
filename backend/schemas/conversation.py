"""
Conversation metadata schemas for tracking saved conversations.
Uses a base table + type-specific tables approach for flexibility.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Union, List
from enum import Enum


class ConversationType(str, Enum):
    """Types of conversations that can be saved."""

    COURSE_OUTLINE = "course_outline"
    LESSON_PLAN = "lesson_plan"
    PRESENTATION = "presentation"
    ASSESSMENT = "assessment"


class ConversationBase(BaseModel):
    """Base metadata shared by all conversation types."""

    thread_id: str = Field(
        ..., description="Unique identifier for the conversation thread"
    )
    user_id: str = Field(..., description="ID of the user who owns this conversation")
    conversation_type: ConversationType = Field(..., description="Type of conversation")
    title: str = Field(..., description="Title or summary of the conversation")
    language: str = Field(
        default="Hungarian", description="Language for generated content"
    )
    created_at: datetime = Field(
        default_factory=datetime.now, description="When the conversation was created"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="When the conversation was last updated",
    )
    message_count: int = Field(
        default=0, description="Number of messages in the conversation"
    )
    uploaded_file_names: List[str] = Field(
        default_factory=list,
        description="Names of files uploaded with the initial request",
    )


class CourseOutlineMetadata(ConversationBase):
    """Metadata specific to course outline conversations."""

    topic: str = Field(..., description="The course topic")
    number_of_classes: int = Field(..., description="Number of classes in the course")
    difficulty_level: Optional[str] = Field(
        None, description="Difficulty level (beginner, intermediate, advanced)"
    )
    target_audience: Optional[str] = Field(
        None, description="Target audience for the course"
    )
    user_comment: Optional[str] = Field(
        None, description="The user's original comment/instruction"
    )


class LessonPlanMetadata(ConversationBase):
    """Metadata specific to lesson plan conversations."""

    course_title: str = Field(..., description="Title of the course")
    class_number: int = Field(
        ..., description="The class number in the course sequence"
    )
    class_title: str = Field(..., description="Title of the class")
    learning_objectives: List[str] = Field(
        default_factory=list, description="List of learning objectives"
    )
    key_topics: List[str] = Field(
        default_factory=list, description="List of key topics covered"
    )
    activities_projects: List[str] = Field(
        default_factory=list, description="List of activities and projects"
    )
    user_comment: Optional[str] = Field(
        None, description="The user's original comment/instruction"
    )


class PresentationMetadata(ConversationBase):
    """Metadata specific to presentation conversations."""

    course_title: str = Field(..., description="Title of the course")
    class_number: Optional[int] = Field(
        None, description="The class number in the course sequence"
    )
    class_title: str = Field(..., description="Title of the class")
    learning_objective: Optional[str] = Field(
        None, description="Main learning goal of this lesson"
    )
    key_points: List[str] = Field(
        default_factory=list, description="Essential concepts or topics covered"
    )
    lesson_breakdown: Optional[str] = Field(
        None, description="Step-by-step flow of the lesson"
    )
    activities: Optional[str] = Field(
        None, description="Hands-on tasks, exercises, or projects"
    )
    homework: Optional[str] = Field(
        None, description="Homework or follow-up work assigned"
    )
    extra_activities: Optional[str] = Field(
        None, description="Optional enrichment or bonus activities"
    )
    user_comment: Optional[str] = Field(
        None, description="The user's original comment/instruction"
    )


class AssessmentMetadata(ConversationBase):
    """Metadata specific to assessment conversations."""

    course_title: str = Field(..., description="Title of the course")
    class_title: Optional[str] = Field(None, description="Title of the class")
    key_topics: List[str] = Field(
        default_factory=list, description="List of key topics covered"
    )
    assessment_type: str = Field(
        default="quiz",
        description="Type of assessment (quiz, exam, homework, practice)",
    )
    difficulty_level: str = Field(
        default="mixed", description="Difficulty level (easy, medium, hard, mixed)"
    )
    question_type_configs: str = Field(
        default="[]",
        description="JSON string of question type configurations [{question_type, count}]",
    )
    user_comment: Optional[str] = Field(
        None, description="The user's original comment/instruction"
    )


# Union type for all conversation metadata types
ConversationMetadata = Union[
    CourseOutlineMetadata, LessonPlanMetadata, PresentationMetadata, AssessmentMetadata
]


class CourseOutlineCreate(BaseModel):
    """Request model for creating a course outline conversation."""

    title: str
    topic: str
    number_of_classes: int
    language: str = "Hungarian"
    difficulty_level: Optional[str] = None
    target_audience: Optional[str] = None
    user_comment: Optional[str] = None
    uploaded_file_names: List[str] = []


class LessonPlanCreate(BaseModel):
    """Request model for creating a lesson plan conversation."""

    title: str
    course_title: str
    class_number: int
    class_title: str
    learning_objectives: List[str]
    key_topics: List[str]
    activities_projects: List[str]
    language: str = "Hungarian"
    user_comment: Optional[str] = None
    uploaded_file_names: List[str] = []


class PresentationCreate(BaseModel):
    """Request model for creating a presentation conversation."""

    title: str
    course_title: str
    class_number: Optional[int] = None
    class_title: str
    learning_objective: Optional[str] = None
    key_points: List[str] = []
    lesson_breakdown: Optional[str] = None
    activities: Optional[str] = None
    homework: Optional[str] = None
    extra_activities: Optional[str] = None
    language: str = "Hungarian"
    user_comment: Optional[str] = None
    uploaded_file_names: List[str] = []


class AssessmentCreate(BaseModel):
    """Request model for creating an assessment conversation."""

    title: str
    course_title: str
    class_title: Optional[str] = None
    key_topics: List[str] = []
    assessment_type: str = "quiz"
    difficulty_level: str = "mixed"
    question_type_configs: str = "[]"  # JSON string
    language: str = "Hungarian"
    user_comment: Optional[str] = None
    uploaded_file_names: List[str] = []


class ConversationList(BaseModel):
    """Response model for listing conversations."""

    conversations: list[
        Union[
            CourseOutlineMetadata,
            LessonPlanMetadata,
            PresentationMetadata,
            AssessmentMetadata,
        ]
    ]
    total: int
