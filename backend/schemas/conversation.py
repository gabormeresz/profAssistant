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


class ConversationBase(BaseModel):
    """Base metadata shared by all conversation types."""

    thread_id: str = Field(
        ..., description="Unique identifier for the conversation thread"
    )
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


# Union type for all conversation metadata types
ConversationMetadata = Union[CourseOutlineMetadata, LessonPlanMetadata]


class CourseOutlineCreate(BaseModel):
    """Request model for creating a course outline conversation."""

    title: str
    topic: str
    number_of_classes: int
    language: str = "Hungarian"
    difficulty_level: Optional[str] = None
    target_audience: Optional[str] = None
    user_comment: Optional[str] = None


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


class CourseOutlineUpdate(BaseModel):
    """Request model for updating course outline metadata."""

    title: Optional[str] = None
    topic: Optional[str] = None
    number_of_classes: Optional[int] = None
    language: Optional[str] = None
    difficulty_level: Optional[str] = None
    target_audience: Optional[str] = None
    user_comment: Optional[str] = None


class LessonPlanUpdate(BaseModel):
    """Request model for updating lesson plan metadata."""

    title: Optional[str] = None
    course_title: Optional[str] = None
    class_number: Optional[int] = None
    class_title: Optional[str] = None
    learning_objectives: Optional[List[str]] = None
    key_topics: Optional[List[str]] = None
    activities_projects: Optional[List[str]] = None
    language: Optional[str] = None
    user_comment: Optional[str] = None


class ConversationList(BaseModel):
    """Response model for listing conversations."""

    conversations: list[Union[CourseOutlineMetadata, LessonPlanMetadata]]
    total: int
