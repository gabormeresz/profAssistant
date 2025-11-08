"""
Service for managing conversation metadata and persistence.
Uses a multi-table schema: base conversations table + type-specific tables.
"""
import sqlite3
import json
from typing import List, Optional, Union
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
            # Update base table
            base_updates = []
            base_params = []
            
            if data.title is not None:
                base_updates.append("title = ?")
                base_params.append(data.title)
            
            if increment_message_count:
                base_updates.append("message_count = message_count + 1")
            
            base_updates.append("updated_at = ?")
            base_params.append(datetime.now().isoformat())
            base_params.append(thread_id)
            
            if base_updates:
                cursor.execute(f"""
                    UPDATE conversations
                    SET {', '.join(base_updates)}
                    WHERE thread_id = ?
                """, base_params)
            
            # Update course_outlines table
            outline_updates = []
            outline_params = []
            
            if data.topic is not None:
                outline_updates.append("topic = ?")
                outline_params.append(data.topic)
            
            if data.number_of_classes is not None:
                outline_updates.append("number_of_classes = ?")
                outline_params.append(data.number_of_classes)
            
            if data.difficulty_level is not None:
                outline_updates.append("difficulty_level = ?")
                outline_params.append(data.difficulty_level)
            
            if data.target_audience is not None:
                outline_updates.append("target_audience = ?")
                outline_params.append(data.target_audience)
            
            if outline_updates:
                outline_params.append(thread_id)
                cursor.execute(f"""
                    UPDATE course_outlines
                    SET {', '.join(outline_updates)}
                    WHERE thread_id = ?
                """, outline_params)
            
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
            # Update base table
            base_updates = []
            base_params = []
            
            if data.title is not None:
                base_updates.append("title = ?")
                base_params.append(data.title)
            
            if increment_message_count:
                base_updates.append("message_count = message_count + 1")
            
            base_updates.append("updated_at = ?")
            base_params.append(datetime.now().isoformat())
            base_params.append(thread_id)
            
            if base_updates:
                cursor.execute(f"""
                    UPDATE conversations
                    SET {', '.join(base_updates)}
                    WHERE thread_id = ?
                """, base_params)
            
            # Update lesson_plans table
            lesson_updates = []
            lesson_params = []

            if data.course_title is not None:
                lesson_updates.append("course_title = ?")
                lesson_params.append(data.course_title)

            if data.class_number is not None:
                lesson_updates.append("class_number = ?")
                lesson_params.append(data.class_number)

            if data.class_title is not None:
                lesson_updates.append("class_title = ?")
                lesson_params.append(data.class_title)

            if data.learning_objectives is not None:
                lesson_updates.append("learning_objectives = ?")
                lesson_params.append(json.dumps(data.learning_objectives))

            if data.key_topics is not None:
                lesson_updates.append("key_topics = ?")
                lesson_params.append(json.dumps(data.key_topics))

            if data.activities_projects is not None:
                lesson_updates.append("activities_projects = ?")
                lesson_params.append(json.dumps(data.activities_projects))

            if lesson_updates:
                lesson_params.append(thread_id)
                cursor.execute(f"""
                    UPDATE lesson_plans
                    SET {', '.join(lesson_updates)}
                    WHERE thread_id = ?
                """, lesson_params)
            
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
