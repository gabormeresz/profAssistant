"""
Repository for conversation metadata persistence.

Uses a multi-table schema: base ``conversations`` table joined with
type-specific tables (``course_outlines``, ``lesson_plans``).

All database methods are async, backed by the shared
:class:`DatabaseManager` connection.
"""

import json
import logging
from datetime import datetime
from typing import List, Optional, Union

from schemas.conversation import (
    ConversationType,
    CourseOutlineMetadata,
    LessonPlanMetadata,
    PresentationMetadata,
    AssessmentMetadata,
    CourseOutlineCreate,
    LessonPlanCreate,
    PresentationCreate,
    AssessmentCreate,
)
from services.database import DatabaseManager

logger = logging.getLogger(__name__)


# Whitelists of allowed columns for each table
ALLOWED_COLUMNS = {
    "conversations": {"title", "language", "message_count", "updated_at", "user_id"},
    "course_outlines": {
        "topic",
        "number_of_classes",
        "difficulty_level",
        "target_audience",
        "user_comment",
    },
    "lesson_plans": {
        "course_title",
        "class_number",
        "class_title",
        "learning_objectives",
        "key_topics",
        "activities_projects",
        "user_comment",
    },
    "presentations": {
        "course_title",
        "class_number",
        "class_title",
        "learning_objective",
        "key_points",
        "lesson_breakdown",
        "activities",
        "homework",
        "extra_activities",
        "user_comment",
    },
    "assessments": {
        "course_title",
        "class_title",
        "key_topics",
        "assessment_type",
        "difficulty_level",
        "question_type_configs",
        "user_comment",
    },
}


class ConversationRepository:
    """Manages conversation metadata storage and retrieval using multi-table schema."""

    def __init__(self, db: DatabaseManager):
        self._db = db

    @property
    def conn(self):
        return self._db.conn

    # =========================================================================
    # Create
    # =========================================================================

    async def create_course_outline(
        self,
        thread_id: str,
        user_id: str,
        conversation_type: ConversationType,
        data: CourseOutlineCreate,
    ) -> CourseOutlineMetadata:
        """Create a new course outline conversation."""
        now = datetime.now().isoformat()
        conn = self.conn
        uploaded_file_names_json = json.dumps(data.uploaded_file_names)

        # Insert into base table
        await conn.execute(
            """
            INSERT INTO conversations 
            (thread_id, user_id, conversation_type, title, language, created_at, updated_at, message_count, uploaded_file_names)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                thread_id,
                user_id,
                conversation_type.value,
                data.title,
                data.language,
                now,
                now,
                0,
                uploaded_file_names_json,
            ),
        )

        # Insert into course_outlines table
        await conn.execute(
            """
            INSERT INTO course_outlines
            (thread_id, topic, number_of_classes, difficulty_level, target_audience, user_comment)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                thread_id,
                data.topic,
                data.number_of_classes,
                data.difficulty_level,
                data.target_audience,
                data.user_comment,
            ),
        )

        await conn.commit()

        return CourseOutlineMetadata(
            thread_id=thread_id,
            user_id=user_id,
            conversation_type=conversation_type,
            title=data.title,
            language=data.language,
            topic=data.topic,
            number_of_classes=data.number_of_classes,
            difficulty_level=data.difficulty_level,
            target_audience=data.target_audience,
            user_comment=data.user_comment,
            uploaded_file_names=data.uploaded_file_names,
            created_at=datetime.fromisoformat(now),
            updated_at=datetime.fromisoformat(now),
            message_count=0,
        )

    async def create_lesson_plan(
        self,
        thread_id: str,
        user_id: str,
        conversation_type: ConversationType,
        data: LessonPlanCreate,
    ) -> LessonPlanMetadata:
        """Create a new lesson plan conversation."""
        now = datetime.now().isoformat()
        conn = self.conn
        uploaded_file_names_json = json.dumps(data.uploaded_file_names)

        # Insert into base table
        await conn.execute(
            """
            INSERT INTO conversations 
            (thread_id, user_id, conversation_type, title, language, created_at, updated_at, message_count, uploaded_file_names)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                thread_id,
                user_id,
                conversation_type.value,
                data.title,
                data.language,
                now,
                now,
                0,
                uploaded_file_names_json,
            ),
        )

        # Serialize lists to JSON strings for storage
        learning_objectives_json = json.dumps(data.learning_objectives)
        key_topics_json = json.dumps(data.key_topics)
        activities_projects_json = json.dumps(data.activities_projects)

        # Insert into lesson_plans table
        await conn.execute(
            """
            INSERT INTO lesson_plans
            (thread_id, course_title, class_number, class_title, learning_objectives, key_topics, activities_projects, user_comment)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                thread_id,
                data.course_title,
                data.class_number,
                data.class_title,
                learning_objectives_json,
                key_topics_json,
                activities_projects_json,
                data.user_comment,
            ),
        )

        await conn.commit()

        return LessonPlanMetadata(
            thread_id=thread_id,
            user_id=user_id,
            conversation_type=ConversationType.LESSON_PLAN,
            title=data.title,
            language=data.language,
            course_title=data.course_title,
            class_number=data.class_number,
            class_title=data.class_title,
            learning_objectives=data.learning_objectives,
            key_topics=data.key_topics,
            activities_projects=data.activities_projects,
            user_comment=data.user_comment,
            uploaded_file_names=data.uploaded_file_names,
            created_at=datetime.fromisoformat(now),
            updated_at=datetime.fromisoformat(now),
            message_count=0,
        )

    async def create_presentation(
        self,
        thread_id: str,
        user_id: str,
        conversation_type: ConversationType,
        data: PresentationCreate,
    ) -> PresentationMetadata:
        """Create a new presentation conversation."""
        now = datetime.now().isoformat()
        conn = self.conn
        uploaded_file_names_json = json.dumps(data.uploaded_file_names)

        # Insert into base table
        await conn.execute(
            """
            INSERT INTO conversations 
            (thread_id, user_id, conversation_type, title, language, created_at, updated_at, message_count, uploaded_file_names)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                thread_id,
                user_id,
                conversation_type.value,
                data.title,
                data.language,
                now,
                now,
                0,
                uploaded_file_names_json,
            ),
        )

        # Serialize list to JSON string for storage
        key_points_json = json.dumps(data.key_points)

        # Insert into presentations table
        await conn.execute(
            """
            INSERT INTO presentations
            (thread_id, course_title, class_number, class_title, learning_objective,
             key_points, lesson_breakdown, activities, homework, extra_activities, user_comment)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                thread_id,
                data.course_title,
                data.class_number,
                data.class_title,
                data.learning_objective,
                key_points_json,
                data.lesson_breakdown,
                data.activities,
                data.homework,
                data.extra_activities,
                data.user_comment,
            ),
        )

        await conn.commit()

        return PresentationMetadata(
            thread_id=thread_id,
            user_id=user_id,
            conversation_type=ConversationType.PRESENTATION,
            title=data.title,
            language=data.language,
            course_title=data.course_title,
            class_number=data.class_number,
            class_title=data.class_title,
            learning_objective=data.learning_objective,
            key_points=data.key_points,
            lesson_breakdown=data.lesson_breakdown,
            activities=data.activities,
            homework=data.homework,
            extra_activities=data.extra_activities,
            user_comment=data.user_comment,
            uploaded_file_names=data.uploaded_file_names,
            created_at=datetime.fromisoformat(now),
            updated_at=datetime.fromisoformat(now),
            message_count=0,
        )

    async def create_assessment(
        self,
        thread_id: str,
        user_id: str,
        conversation_type: ConversationType,
        data: AssessmentCreate,
    ) -> AssessmentMetadata:
        """Create a new assessment conversation."""
        now = datetime.now().isoformat()
        conn = self.conn
        uploaded_file_names_json = json.dumps(data.uploaded_file_names)

        # Insert into base table
        await conn.execute(
            """
            INSERT INTO conversations
            (thread_id, user_id, conversation_type, title, language, created_at, updated_at, message_count, uploaded_file_names)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                thread_id,
                user_id,
                conversation_type.value,
                data.title,
                data.language,
                now,
                now,
                0,
                uploaded_file_names_json,
            ),
        )

        # Serialize lists to JSON strings for storage
        key_topics_json = json.dumps(data.key_topics)

        # Insert into assessments table
        await conn.execute(
            """
            INSERT INTO assessments
            (thread_id, course_title, class_title,
             key_topics, assessment_type, difficulty_level, question_type_configs, user_comment)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                thread_id,
                data.course_title,
                data.class_title,
                key_topics_json,
                data.assessment_type,
                data.difficulty_level,
                data.question_type_configs,
                data.user_comment,
            ),
        )

        await conn.commit()

        return AssessmentMetadata(
            thread_id=thread_id,
            user_id=user_id,
            conversation_type=ConversationType.ASSESSMENT,
            title=data.title,
            language=data.language,
            course_title=data.course_title,
            class_title=data.class_title,
            key_topics=data.key_topics,
            assessment_type=data.assessment_type,
            difficulty_level=data.difficulty_level,
            question_type_configs=data.question_type_configs,
            user_comment=data.user_comment,
            uploaded_file_names=data.uploaded_file_names,
            created_at=datetime.fromisoformat(now),
            updated_at=datetime.fromisoformat(now),
            message_count=0,
        )

    # =========================================================================
    # Read
    # =========================================================================

    async def get_conversation(self, thread_id: str) -> Optional[
        Union[
            CourseOutlineMetadata,
            LessonPlanMetadata,
            PresentationMetadata,
            AssessmentMetadata,
        ]
    ]:
        """Get a conversation by thread_id with type-specific data."""
        conn = self.conn

        # Get base conversation data
        cursor = await conn.execute(
            """
            SELECT thread_id, user_id, conversation_type, title, language, created_at, updated_at, message_count, uploaded_file_names
            FROM conversations
            WHERE thread_id = ?
        """,
            (thread_id,),
        )

        row = await cursor.fetchone()

        if not row:
            return None

        (
            thread_id,
            user_id,
            conv_type,
            title,
            language,
            created_at,
            updated_at,
            message_count,
            uploaded_file_names_raw,
        ) = row
        conversation_type = ConversationType(conv_type)
        uploaded_file_names = (
            json.loads(uploaded_file_names_raw) if uploaded_file_names_raw else []
        )

        # Get type-specific data
        if conversation_type == ConversationType.COURSE_OUTLINE:
            cursor = await conn.execute(
                """
                SELECT topic, number_of_classes, difficulty_level, target_audience, user_comment
                FROM course_outlines
                WHERE thread_id = ?
            """,
                (thread_id,),
            )

            outline_row = await cursor.fetchone()
            if not outline_row:
                return None

            return CourseOutlineMetadata(
                thread_id=thread_id,
                user_id=user_id,
                conversation_type=conversation_type,
                title=title,
                language=language or "Hungarian",
                topic=outline_row[0],
                number_of_classes=outline_row[1],
                difficulty_level=outline_row[2],
                target_audience=outline_row[3],
                user_comment=outline_row[4],
                uploaded_file_names=uploaded_file_names,
                created_at=datetime.fromisoformat(created_at),
                updated_at=datetime.fromisoformat(updated_at),
                message_count=message_count,
            )

        elif conversation_type == ConversationType.LESSON_PLAN:
            cursor = await conn.execute(
                """
                SELECT course_title, class_number, class_title, learning_objectives, key_topics, activities_projects, user_comment
                FROM lesson_plans
                WHERE thread_id = ?
            """,
                (thread_id,),
            )

            lesson_row = await cursor.fetchone()
            if not lesson_row:
                return None

            # Deserialize JSON strings back to lists
            learning_objectives = json.loads(lesson_row[3]) if lesson_row[3] else []
            key_topics = json.loads(lesson_row[4]) if lesson_row[4] else []
            activities_projects = json.loads(lesson_row[5]) if lesson_row[5] else []

            return LessonPlanMetadata(
                thread_id=thread_id,
                user_id=user_id,
                conversation_type=conversation_type,
                title=title,
                language=language or "Hungarian",
                course_title=lesson_row[0],
                class_number=lesson_row[1],
                class_title=lesson_row[2],
                learning_objectives=learning_objectives,
                key_topics=key_topics,
                activities_projects=activities_projects,
                user_comment=lesson_row[6],
                uploaded_file_names=uploaded_file_names,
                created_at=datetime.fromisoformat(created_at),
                updated_at=datetime.fromisoformat(updated_at),
                message_count=message_count,
            )

        elif conversation_type == ConversationType.PRESENTATION:
            cursor = await conn.execute(
                """
                SELECT course_title, class_number, class_title, learning_objective,
                       key_points, lesson_breakdown, activities, homework, extra_activities, user_comment
                FROM presentations
                WHERE thread_id = ?
            """,
                (thread_id,),
            )

            pres_row = await cursor.fetchone()
            if not pres_row:
                return None

            key_points = json.loads(pres_row[4]) if pres_row[4] else []

            return PresentationMetadata(
                thread_id=thread_id,
                user_id=user_id,
                conversation_type=conversation_type,
                title=title,
                language=language or "Hungarian",
                course_title=pres_row[0],
                class_number=pres_row[1],
                class_title=pres_row[2],
                learning_objective=pres_row[3],
                key_points=key_points,
                lesson_breakdown=pres_row[5],
                activities=pres_row[6],
                homework=pres_row[7],
                extra_activities=pres_row[8],
                user_comment=pres_row[9],
                uploaded_file_names=uploaded_file_names,
                created_at=datetime.fromisoformat(created_at),
                updated_at=datetime.fromisoformat(updated_at),
                message_count=message_count,
            )

        elif conversation_type == ConversationType.ASSESSMENT:
            cursor = await conn.execute(
                """
                SELECT course_title, class_title,
                       key_topics, assessment_type, difficulty_level, question_type_configs, user_comment
                FROM assessments
                WHERE thread_id = ?
            """,
                (thread_id,),
            )

            assess_row = await cursor.fetchone()
            if not assess_row:
                return None

            key_topics = json.loads(assess_row[2]) if assess_row[2] else []

            return AssessmentMetadata(
                thread_id=thread_id,
                user_id=user_id,
                conversation_type=conversation_type,
                title=title,
                language=language or "Hungarian",
                course_title=assess_row[0],
                class_title=assess_row[1],
                key_topics=key_topics,
                assessment_type=assess_row[3],
                difficulty_level=assess_row[4],
                question_type_configs=assess_row[5] or "",
                user_comment=assess_row[6],
                uploaded_file_names=uploaded_file_names,
                created_at=datetime.fromisoformat(created_at),
                updated_at=datetime.fromisoformat(updated_at),
                message_count=message_count,
            )

        return None

    async def list_conversations(
        self,
        user_id: Optional[str] = None,
        conversation_type: Optional[ConversationType] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[
        Union[
            CourseOutlineMetadata,
            LessonPlanMetadata,
            PresentationMetadata,
            AssessmentMetadata,
        ]
    ]:
        """List conversations with type-specific data."""
        conn = self.conn

        # Build query based on filters
        conditions = []
        params: list = []

        if user_id:
            conditions.append("user_id = ?")
            params.append(user_id)
        if conversation_type:
            conditions.append("conversation_type = ?")
            params.append(conversation_type.value)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        cursor = await conn.execute(
            f"""
            SELECT thread_id, user_id, conversation_type, title, language, created_at, updated_at, message_count, uploaded_file_names
            FROM conversations
            {where_clause}
            ORDER BY updated_at DESC
            LIMIT ? OFFSET ?
        """,
            (*params, limit, offset),
        )

        rows = await cursor.fetchall()
        conversations = []

        for row in rows:
            (
                thread_id,
                row_user_id,
                conv_type,
                title,
                language,
                created_at,
                updated_at,
                message_count,
                uploaded_file_names_raw,
            ) = row
            ct = ConversationType(conv_type)
            uploaded_file_names = (
                json.loads(uploaded_file_names_raw) if uploaded_file_names_raw else []
            )

            # Fetch type-specific data
            if ct == ConversationType.COURSE_OUTLINE:
                cursor2 = await conn.execute(
                    """
                    SELECT topic, number_of_classes, difficulty_level, target_audience, user_comment
                    FROM course_outlines
                    WHERE thread_id = ?
                """,
                    (thread_id,),
                )

                outline_row = await cursor2.fetchone()
                if outline_row:
                    conversations.append(
                        CourseOutlineMetadata(
                            thread_id=thread_id,
                            user_id=row_user_id,
                            conversation_type=ct,
                            title=title,
                            language=language or "Hungarian",
                            topic=outline_row[0],
                            number_of_classes=outline_row[1],
                            difficulty_level=outline_row[2],
                            target_audience=outline_row[3],
                            user_comment=outline_row[4],
                            uploaded_file_names=uploaded_file_names,
                            created_at=datetime.fromisoformat(created_at),
                            updated_at=datetime.fromisoformat(updated_at),
                            message_count=message_count,
                        )
                    )

            elif ct == ConversationType.LESSON_PLAN:
                cursor2 = await conn.execute(
                    """
                    SELECT course_title, class_number, class_title, learning_objectives, key_topics, activities_projects, user_comment
                    FROM lesson_plans
                    WHERE thread_id = ?
                """,
                    (thread_id,),
                )

                lesson_row = await cursor2.fetchone()
                if lesson_row:
                    # Deserialize JSON strings back to lists
                    learning_objectives = (
                        json.loads(lesson_row[3]) if lesson_row[3] else []
                    )
                    key_topics = json.loads(lesson_row[4]) if lesson_row[4] else []
                    activities_projects = (
                        json.loads(lesson_row[5]) if lesson_row[5] else []
                    )

                    conversations.append(
                        LessonPlanMetadata(
                            thread_id=thread_id,
                            user_id=row_user_id,
                            conversation_type=ct,
                            title=title,
                            language=language or "Hungarian",
                            course_title=lesson_row[0],
                            class_number=lesson_row[1],
                            class_title=lesson_row[2],
                            learning_objectives=learning_objectives,
                            key_topics=key_topics,
                            activities_projects=activities_projects,
                            user_comment=lesson_row[6],
                            uploaded_file_names=uploaded_file_names,
                            created_at=datetime.fromisoformat(created_at),
                            updated_at=datetime.fromisoformat(updated_at),
                            message_count=message_count,
                        )
                    )

            elif ct == ConversationType.PRESENTATION:
                cursor2 = await conn.execute(
                    """
                    SELECT course_title, class_number, class_title, learning_objective,
                           key_points, lesson_breakdown, activities, homework, extra_activities, user_comment
                    FROM presentations
                    WHERE thread_id = ?
                """,
                    (thread_id,),
                )

                pres_row = await cursor2.fetchone()
                if pres_row:
                    key_points = json.loads(pres_row[4]) if pres_row[4] else []

                    conversations.append(
                        PresentationMetadata(
                            thread_id=thread_id,
                            user_id=row_user_id,
                            conversation_type=ct,
                            title=title,
                            language=language or "Hungarian",
                            course_title=pres_row[0],
                            class_number=pres_row[1],
                            class_title=pres_row[2],
                            learning_objective=pres_row[3],
                            key_points=key_points,
                            lesson_breakdown=pres_row[5],
                            activities=pres_row[6],
                            homework=pres_row[7],
                            extra_activities=pres_row[8],
                            user_comment=pres_row[9],
                            uploaded_file_names=uploaded_file_names,
                            created_at=datetime.fromisoformat(created_at),
                            updated_at=datetime.fromisoformat(updated_at),
                            message_count=message_count,
                        )
                    )

            elif ct == ConversationType.ASSESSMENT:
                cursor2 = await conn.execute(
                    """
                    SELECT course_title, class_title,
                           key_topics, assessment_type, difficulty_level, question_type_configs, user_comment
                    FROM assessments
                    WHERE thread_id = ?
                """,
                    (thread_id,),
                )

                assess_row = await cursor2.fetchone()
                if assess_row:
                    key_topics = json.loads(assess_row[2]) if assess_row[2] else []

                    conversations.append(
                        AssessmentMetadata(
                            thread_id=thread_id,
                            user_id=row_user_id,
                            conversation_type=ct,
                            title=title,
                            language=language or "Hungarian",
                            course_title=assess_row[0],
                            class_title=assess_row[1],
                            key_topics=key_topics,
                            assessment_type=assess_row[3],
                            difficulty_level=assess_row[4],
                            question_type_configs=assess_row[5] or "",
                            user_comment=assess_row[6],
                            uploaded_file_names=uploaded_file_names,
                            created_at=datetime.fromisoformat(created_at),
                            updated_at=datetime.fromisoformat(updated_at),
                            message_count=message_count,
                        )
                    )

        return conversations

    # =========================================================================
    # Update / Delete / Count
    # =========================================================================

    async def increment_message_count(self, thread_id: str) -> bool:
        """Increment message count and update timestamp for any conversation type."""
        conn = self.conn

        cursor = await conn.execute(
            """
            UPDATE conversations
            SET message_count = message_count + 1,
                updated_at = ?
            WHERE thread_id = ?
        """,
            (datetime.now().isoformat(), thread_id),
        )

        updated = cursor.rowcount > 0
        await conn.commit()
        return updated

    async def delete_conversation(self, thread_id: str) -> bool:
        """Delete a conversation (cascades to type-specific tables)."""
        conn = self.conn

        cursor = await conn.execute(
            "DELETE FROM conversations WHERE thread_id = ?", (thread_id,)
        )
        deleted = cursor.rowcount > 0
        await conn.commit()
        return deleted

    async def count_conversations(
        self,
        user_id: Optional[str] = None,
        conversation_type: Optional[ConversationType] = None,
    ) -> int:
        """Count total conversations, optionally filtered by user and/or type."""
        conn = self.conn

        conditions = []
        params: list = []

        if user_id:
            conditions.append("user_id = ?")
            params.append(user_id)
        if conversation_type:
            conditions.append("conversation_type = ?")
            params.append(conversation_type.value)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        cursor = await conn.execute(
            f"SELECT COUNT(*) FROM conversations {where_clause}",
            tuple(params),
        )

        row = await cursor.fetchone()
        return row[0] if row else 0


# ---------------------------------------------------------------------------
#  Global instance — wired to the shared ``db`` from database.py
# ---------------------------------------------------------------------------
from services.database import db

conversation_manager = ConversationRepository(db)
