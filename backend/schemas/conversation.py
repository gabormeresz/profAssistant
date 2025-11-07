"""
Conversation metadata schemas for tracking saved conversations.
Uses a base table + type-specific tables approach for flexibility.
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Union
from enum import Enum


class ConversationType(str, Enum):
    """Types of conversations that can be saved."""
    COURSE_OUTLINE = "course_outline"
    LESSON_PLAN = "lesson_plan"


class ConversationBase(BaseModel):
    """Base metadata shared by all conversation types."""
    thread_id: str = Field(..., description="Unique identifier for the conversation thread")
    conversation_type: ConversationType = Field(..., description="Type of conversation")
    title: str = Field(..., description="Title or summary of the conversation")
    created_at: datetime = Field(default_factory=datetime.now, description="When the conversation was created")
    updated_at: datetime = Field(default_factory=datetime.now, description="When the conversation was last updated")
    message_count: int = Field(default=0, description="Number of messages in the conversation")


class CourseOutlineMetadata(ConversationBase):
    """Metadata specific to course outline conversations."""
    topic: str = Field(..., description="The course topic")
    number_of_classes: int = Field(..., description="Number of classes in the course")
    difficulty_level: Optional[str] = Field(None, description="Difficulty level (beginner, intermediate, advanced)")
    target_audience: Optional[str] = Field(None, description="Target audience for the course")


class LessonPlanMetadata(ConversationBase):
    """Metadata specific to lesson plan conversations."""
    lesson_title: str = Field(..., description="Title of the lesson")
    subject: str = Field(..., description="Subject area")
    grade_level: Optional[str] = Field(None, description="Grade level or educational level")
    duration_minutes: Optional[int] = Field(None, description="Planned lesson duration in minutes")
    learning_objectives: Optional[str] = Field(None, description="Key learning objectives")


# Union type for all conversation metadata types
ConversationMetadata = Union[CourseOutlineMetadata, LessonPlanMetadata]


# Union type for all conversation metadata types
ConversationMetadata = Union[CourseOutlineMetadata, LessonPlanMetadata]


class CourseOutlineCreate(BaseModel):
    """Request model for creating a course outline conversation."""
    title: str
    topic: str
    number_of_classes: int
    difficulty_level: Optional[str] = None
    target_audience: Optional[str] = None


class LessonPlanCreate(BaseModel):
    """Request model for creating a lesson plan conversation."""
    title: str
    lesson_title: str
    subject: str
    grade_level: Optional[str] = None
    duration_minutes: Optional[int] = None
    learning_objectives: Optional[str] = None


class CourseOutlineUpdate(BaseModel):
    """Request model for updating course outline metadata."""
    title: Optional[str] = None
    topic: Optional[str] = None
    number_of_classes: Optional[int] = None
    difficulty_level: Optional[str] = None
    target_audience: Optional[str] = None


class LessonPlanUpdate(BaseModel):
    """Request model for updating lesson plan metadata."""
    title: Optional[str] = None
    lesson_title: Optional[str] = None
    subject: Optional[str] = None
    grade_level: Optional[str] = None
    duration_minutes: Optional[int] = None
    learning_objectives: Optional[str] = None


class ConversationList(BaseModel):
    """Response model for listing conversations."""
    conversations: list[Union[CourseOutlineMetadata, LessonPlanMetadata]]
    total: int

