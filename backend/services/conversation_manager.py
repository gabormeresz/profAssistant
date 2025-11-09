"""
Service for managing conversation metadata and persistence.
Uses a multi-table schema: base conversations table + type-specific tables.
"""
import sqlite3
import json
from typing import List, Optional, Union, Dict, Any, Tuple
from datetime import datetime
from schemas.conversation import (
    ConversationType,
    CourseOutlineMetadata,
    LessonPlanMetadata,
    CourseOutlineCreate,
    LessonPlanCreate,
    CourseOutlineUpdate,
    LessonPlanUpdate
)


# Whitelists of allowed columns for each table
ALLOWED_COLUMNS = {
    "conversations": {
        "title",
        "message_count",
        "updated_at"
    },
    "course_outlines": {
        "topic",
        "number_of_classes",
        "difficulty_level",
        "target_audience",
        "user_comment"
    },
    "lesson_plans": {
        "course_title",
        "class_number",
        "class_title",
        "learning_objectives",
        "key_topics",
        "activities_projects",
        "user_comment"
    }
}


def build_safe_update_query(
    table: str,
    updates: Dict[str, Any],
    where_clause: str = "thread_id = ?"
) -> Tuple[str, List[Any]]:
    """
    Build a safe SQL UPDATE query with validated column names.

    Args:
        table: Table name (must be in ALLOWED_COLUMNS)
        updates: Dictionary of column_name: value pairs to update
        where_clause: WHERE clause with placeholders

    Returns:
        Tuple of (query_string, parameter_list)

    Raises:
        ValueError: If table is unknown or column names are not whitelisted
    """
    if table not in ALLOWED_COLUMNS:
        raise ValueError(f"Unknown table: {table}")

    if not updates:
        raise ValueError("No updates provided")

    # Validate all column names against whitelist
    allowed_cols = ALLOWED_COLUMNS[table]
    invalid_cols = set(updates.keys()) - allowed_cols
    if invalid_cols:
        raise ValueError(f"Invalid columns for {table}: {invalid_cols}")

    # Build SET clause with validated columns
    set_clauses = [f"{col} = ?" for col in updates.keys()]
    params = list(updates.values())

    query = f"UPDATE {table} SET {', '.join(set_clauses)} WHERE {where_clause}"

    return query, params


class ConversationManager:
    """Manages conversation metadata storage and retrieval using multi-table schema."""
    
    def __init__(self, db_path: str = "conversations.db"):
        """Initialize the conversation manager with a database connection."""
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize the database schema with base and type-specific tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Base conversations table - common fields for all types
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                thread_id TEXT PRIMARY KEY,
                conversation_type TEXT NOT NULL,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                message_count INTEGER DEFAULT 0
            )
        """)
        
        # Course outline specific table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS course_outlines (
                thread_id TEXT PRIMARY KEY,
                topic TEXT NOT NULL,
                number_of_classes INTEGER NOT NULL,
                difficulty_level TEXT,
                target_audience TEXT,
                user_comment TEXT,
                FOREIGN KEY (thread_id) REFERENCES conversations (thread_id) ON DELETE CASCADE
            )
        """)
        
        # Lesson plan specific table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lesson_plans (
                thread_id TEXT PRIMARY KEY,
                course_title TEXT NOT NULL,
                class_number INTEGER NOT NULL,
                class_title TEXT NOT NULL,
                learning_objectives TEXT,
                key_topics TEXT,
                activities_projects TEXT,
                user_comment TEXT,
                FOREIGN KEY (thread_id) REFERENCES conversations (thread_id) ON DELETE CASCADE
            )
        """)
        
        conn.commit()
        conn.close()
    
    def create_course_outline(
        self,
        thread_id: str,
        conversation_type: ConversationType,
        data: CourseOutlineCreate
    ) -> CourseOutlineMetadata:
        """Create a new course outline conversation."""
        now = datetime.now().isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Insert into base table
            cursor.execute("""
                INSERT INTO conversations 
                (thread_id, conversation_type, title, created_at, updated_at, message_count)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (thread_id, conversation_type.value, data.title, now, now, 0))
            
            # Insert into course_outlines table
            cursor.execute("""
                INSERT INTO course_outlines
                (thread_id, topic, number_of_classes, difficulty_level, target_audience, user_comment)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (thread_id, data.topic, data.number_of_classes, data.difficulty_level, data.target_audience, data.user_comment))
            
            conn.commit()
            
            return CourseOutlineMetadata(
                thread_id=thread_id,
                conversation_type=conversation_type,
                title=data.title,
                topic=data.topic,
                number_of_classes=data.number_of_classes,
                difficulty_level=data.difficulty_level,
                target_audience=data.target_audience,
                user_comment=data.user_comment,
                created_at=datetime.fromisoformat(now),
                updated_at=datetime.fromisoformat(now),
                message_count=0
            )
        finally:
            conn.close()
    
    def create_lesson_plan(
        self,
        thread_id: str,
        conversation_type: ConversationType,
        data: LessonPlanCreate
    ) -> LessonPlanMetadata:
        """Create a new lesson plan conversation."""
        now = datetime.now().isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Insert into base table
            cursor.execute("""
                INSERT INTO conversations 
                (thread_id, conversation_type, title, created_at, updated_at, message_count)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (thread_id, conversation_type.value, data.title, now, now, 0))
            
            # Serialize lists to JSON strings for storage
            learning_objectives_json = json.dumps(data.learning_objectives)
            key_topics_json = json.dumps(data.key_topics)
            activities_projects_json = json.dumps(data.activities_projects)
            
            # Insert into lesson_plans table
            cursor.execute("""
                INSERT INTO lesson_plans
                (thread_id, course_title, class_number, class_title, learning_objectives, key_topics, activities_projects, user_comment)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (thread_id, data.course_title, data.class_number, data.class_title, 
                  learning_objectives_json, key_topics_json, activities_projects_json, data.user_comment))
            
            conn.commit()
            
            return LessonPlanMetadata(
                thread_id=thread_id,
                conversation_type=ConversationType.LESSON_PLAN,
                title=data.title,
                course_title=data.course_title,
                class_number=data.class_number,
                class_title=data.class_title,
                learning_objectives=data.learning_objectives,
                key_topics=data.key_topics,
                activities_projects=data.activities_projects,
                user_comment=data.user_comment,
                created_at=datetime.fromisoformat(now),
                updated_at=datetime.fromisoformat(now),
                message_count=0
            )
        finally:
            conn.close()
    
    def get_conversation(
        self, 
        thread_id: str
    ) -> Optional[Union[CourseOutlineMetadata, LessonPlanMetadata]]:
        """Get a conversation by thread_id with type-specific data."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get base conversation data
            cursor.execute("""
                SELECT thread_id, conversation_type, title, created_at, updated_at, message_count
                FROM conversations
                WHERE thread_id = ?
            """, (thread_id,))
            
            row = cursor.fetchone()
            
            if not row:
                return None
            
            thread_id, conv_type, title, created_at, updated_at, message_count = row
            conversation_type = ConversationType(conv_type)
            
            # Get type-specific data
            if conversation_type == ConversationType.COURSE_OUTLINE:
                cursor.execute("""
                    SELECT topic, number_of_classes, difficulty_level, target_audience, user_comment
                    FROM course_outlines
                    WHERE thread_id = ?
                """, (thread_id,))
                
                outline_row = cursor.fetchone()
                if not outline_row:
                    return None
                
                return CourseOutlineMetadata(
                    thread_id=thread_id,
                    conversation_type=conversation_type,
                    title=title,
                    topic=outline_row[0],
                    number_of_classes=outline_row[1],
                    difficulty_level=outline_row[2],
                    target_audience=outline_row[3],
                    user_comment=outline_row[4],
                    created_at=datetime.fromisoformat(created_at),
                    updated_at=datetime.fromisoformat(updated_at),
                    message_count=message_count
                )
            
            elif conversation_type == ConversationType.LESSON_PLAN:
                cursor.execute("""
                    SELECT course_title, class_number, class_title, learning_objectives, key_topics, activities_projects, user_comment
                    FROM lesson_plans
                    WHERE thread_id = ?
                """, (thread_id,))
                
                lesson_row = cursor.fetchone()
                if not lesson_row:
                    return None
                
                # Deserialize JSON strings back to lists
                learning_objectives = json.loads(lesson_row[3]) if lesson_row[3] else []
                key_topics = json.loads(lesson_row[4]) if lesson_row[4] else []
                activities_projects = json.loads(lesson_row[5]) if lesson_row[5] else []
                
                return LessonPlanMetadata(
                    thread_id=thread_id,
                    conversation_type=conversation_type,
                    title=title,
                    course_title=lesson_row[0],
                    class_number=lesson_row[1],
                    class_title=lesson_row[2],
                    learning_objectives=learning_objectives,
                    key_topics=key_topics,
                    activities_projects=activities_projects,
                    user_comment=lesson_row[6],
                    created_at=datetime.fromisoformat(created_at),
                    updated_at=datetime.fromisoformat(updated_at),
                    message_count=message_count
                )
            
            return None
        finally:
            conn.close()
    
    def list_conversations(
        self,
        conversation_type: Optional[ConversationType] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Union[CourseOutlineMetadata, LessonPlanMetadata]]:
        """List all conversations with type-specific data, optionally filtered by type."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Build query based on filter
            if conversation_type:
                cursor.execute("""
                    SELECT thread_id, conversation_type, title, created_at, updated_at, message_count
                    FROM conversations
                    WHERE conversation_type = ?
                    ORDER BY updated_at DESC
                    LIMIT ? OFFSET ?
                """, (conversation_type.value, limit, offset))
            else:
                cursor.execute("""
                    SELECT thread_id, conversation_type, title, created_at, updated_at, message_count
                    FROM conversations
                    ORDER BY updated_at DESC
                    LIMIT ? OFFSET ?
                """, (limit, offset))
            
            rows = cursor.fetchall()
            conversations = []
            
            for row in rows:
                thread_id, conv_type, title, created_at, updated_at, message_count = row
                ct = ConversationType(conv_type)
                
                # Fetch type-specific data
                if ct == ConversationType.COURSE_OUTLINE:
                    cursor.execute("""
                        SELECT topic, number_of_classes, difficulty_level, target_audience, user_comment
                        FROM course_outlines
                        WHERE thread_id = ?
                    """, (thread_id,))
                    
                    outline_row = cursor.fetchone()
                    if outline_row:
                        conversations.append(CourseOutlineMetadata(
                            thread_id=thread_id,
                            conversation_type=ct,
                            title=title,
                            topic=outline_row[0],
                            number_of_classes=outline_row[1],
                            difficulty_level=outline_row[2],
                            target_audience=outline_row[3],
                            user_comment=outline_row[4],
                            created_at=datetime.fromisoformat(created_at),
                            updated_at=datetime.fromisoformat(updated_at),
                            message_count=message_count
                        ))
                
                elif ct == ConversationType.LESSON_PLAN:
                    cursor.execute("""
                        SELECT course_title, class_number, class_title, learning_objectives, key_topics, activities_projects, user_comment
                        FROM lesson_plans
                        WHERE thread_id = ?
                    """, (thread_id,))
                    
                    lesson_row = cursor.fetchone()
                    if lesson_row:
                        # Deserialize JSON strings back to lists
                        learning_objectives = json.loads(lesson_row[3]) if lesson_row[3] else []
                        key_topics = json.loads(lesson_row[4]) if lesson_row[4] else []
                        activities_projects = json.loads(lesson_row[5]) if lesson_row[5] else []
                        
                        conversations.append(LessonPlanMetadata(
                            thread_id=thread_id,
                            conversation_type=ct,
                            title=title,
                            course_title=lesson_row[0],
                            class_number=lesson_row[1],
                            class_title=lesson_row[2],
                            learning_objectives=learning_objectives,
                            key_topics=key_topics,
                            activities_projects=activities_projects,
                            user_comment=lesson_row[6],
                            created_at=datetime.fromisoformat(created_at),
                            updated_at=datetime.fromisoformat(updated_at),
                            message_count=message_count
                        ))
            
            return conversations
        finally:
            conn.close()
    
    def update_course_outline(
        self,
        thread_id: str,
        data: CourseOutlineUpdate,
        increment_message_count: bool = False
    ) -> Optional[Union[CourseOutlineMetadata, LessonPlanMetadata]]:
        """Update course outline metadata."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Prepare base table updates
            base_updates = {}

            if data.title is not None:
                base_updates["title"] = data.title

            # Always update timestamp
            base_updates["updated_at"] = datetime.now().isoformat()

            # Handle message count - special case for increment
            if increment_message_count:
                # For increment, we need to use a special SQL expression
                cursor.execute(
                    "UPDATE conversations SET message_count = message_count + 1, updated_at = ? WHERE thread_id = ?",
                    (base_updates["updated_at"], thread_id)
                )
                # Remove updated_at from dict since we already handled it
                if "title" in base_updates:
                    del base_updates["updated_at"]
                else:
                    base_updates.clear()

            # Update remaining base fields if any
            if base_updates:
                query, params = build_safe_update_query("conversations", base_updates)
                params.append(thread_id)
                cursor.execute(query, params)

            # Prepare course_outlines table updates
            outline_updates = {}

            if data.topic is not None:
                outline_updates["topic"] = data.topic

            if data.number_of_classes is not None:
                outline_updates["number_of_classes"] = data.number_of_classes

            if data.difficulty_level is not None:
                outline_updates["difficulty_level"] = data.difficulty_level

            if data.target_audience is not None:
                outline_updates["target_audience"] = data.target_audience

            if data.user_comment is not None:
                outline_updates["user_comment"] = data.user_comment

            # Update course_outlines if we have changes
            if outline_updates:
                query, params = build_safe_update_query("course_outlines", outline_updates)
                params.append(thread_id)
                cursor.execute(query, params)

            conn.commit()
            return self.get_conversation(thread_id)
        finally:
            conn.close()
    
    def update_lesson_plan(
        self,
        thread_id: str,
        data: LessonPlanUpdate,
        increment_message_count: bool = False
    ) -> Optional[Union[CourseOutlineMetadata, LessonPlanMetadata]]:
        """Update lesson plan metadata."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Prepare base table updates
            base_updates = {}

            if data.title is not None:
                base_updates["title"] = data.title

            # Always update timestamp
            base_updates["updated_at"] = datetime.now().isoformat()

            # Handle message count - special case for increment
            if increment_message_count:
                # For increment, we need to use a special SQL expression
                cursor.execute(
                    "UPDATE conversations SET message_count = message_count + 1, updated_at = ? WHERE thread_id = ?",
                    (base_updates["updated_at"], thread_id)
                )
                # Remove updated_at from dict since we already handled it
                if "title" in base_updates:
                    del base_updates["updated_at"]
                else:
                    base_updates.clear()

            # Update remaining base fields if any
            if base_updates:
                query, params = build_safe_update_query("conversations", base_updates)
                params.append(thread_id)
                cursor.execute(query, params)

            # Prepare lesson_plans table updates
            lesson_updates = {}

            if data.course_title is not None:
                lesson_updates["course_title"] = data.course_title

            if data.class_number is not None:
                lesson_updates["class_number"] = data.class_number

            if data.class_title is not None:
                lesson_updates["class_title"] = data.class_title

            if data.learning_objectives is not None:
                lesson_updates["learning_objectives"] = json.dumps(data.learning_objectives)

            if data.key_topics is not None:
                lesson_updates["key_topics"] = json.dumps(data.key_topics)

            if data.activities_projects is not None:
                lesson_updates["activities_projects"] = json.dumps(data.activities_projects)

            if data.user_comment is not None:
                lesson_updates["user_comment"] = data.user_comment

            # Update lesson_plans if we have changes
            if lesson_updates:
                query, params = build_safe_update_query("lesson_plans", lesson_updates)
                params.append(thread_id)
                cursor.execute(query, params)

            conn.commit()
            return self.get_conversation(thread_id)
        finally:
            conn.close()
    
    def increment_message_count(self, thread_id: str) -> bool:
        """Increment message count and update timestamp for any conversation type."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE conversations
                SET message_count = message_count + 1,
                    updated_at = ?
                WHERE thread_id = ?
            """, (datetime.now().isoformat(), thread_id))
            
            updated = cursor.rowcount > 0
            conn.commit()
            return updated
        finally:
            conn.close()
    
    def delete_conversation(self, thread_id: str) -> bool:
        """Delete a conversation (cascades to type-specific tables)."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM conversations WHERE thread_id = ?", (thread_id,))
            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted
        finally:
            conn.close()
    
    def count_conversations(self, conversation_type: Optional[ConversationType] = None) -> int:
        """Count total conversations, optionally filtered by type."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            if conversation_type:
                cursor.execute(
                    "SELECT COUNT(*) FROM conversations WHERE conversation_type = ?",
                    (conversation_type.value,)
                )
            else:
                cursor.execute("SELECT COUNT(*) FROM conversations")
            
            count = cursor.fetchone()[0]
            return count
        finally:
            conn.close()


# Global conversation manager instance
conversation_manager = ConversationManager()
