"""
Service for managing conversation metadata and persistence.
Uses a multi-table schema: base conversations table + type-specific tables.
Includes user management, sessions, and settings.
"""

import sqlite3
import json
import uuid
import logging
from typing import List, Optional, Union
from datetime import datetime
from passlib.hash import bcrypt
from cryptography.fernet import Fernet
from schemas.conversation import (
    ConversationType,
    CourseOutlineMetadata,
    LessonPlanMetadata,
    CourseOutlineCreate,
    LessonPlanCreate,
)
from config import AuthConfig, LLMConfig

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
}


class ConversationManager:
    """Manages conversation metadata storage and retrieval using multi-table schema."""

    def __init__(self, db_path: str = "conversations.db"):
        """Initialize the conversation manager with a database connection."""
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize the database schema with all tables and seed admin user."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON;")

        # ── Users table ──
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                is_active INTEGER DEFAULT 1,
                is_email_verified INTEGER DEFAULT 0,
                email_verification_token TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users (email)")

        # ── User sessions table (refresh tokens) ──
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS user_sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                refresh_token_hash TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
            )
        """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_sessions_user_expires ON user_sessions (user_id, expires_at)"
        )

        # ── User settings table (1:1 with users) ──
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id TEXT PRIMARY KEY,
                openai_api_key_encrypted TEXT,
                preferred_model TEXT DEFAULT 'gpt-4o-mini',
                updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
            )
        """
        )

        # ── Base conversations table ──
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                thread_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                conversation_type TEXT NOT NULL,
                title TEXT NOT NULL,
                language TEXT DEFAULT 'Hungarian',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                message_count INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
            )
        """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations (user_id)"
        )

        # ── Course outline specific table ──
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS course_outlines (
                thread_id TEXT PRIMARY KEY,
                topic TEXT NOT NULL,
                number_of_classes INTEGER NOT NULL,
                difficulty_level TEXT,
                target_audience TEXT,
                user_comment TEXT,
                FOREIGN KEY (thread_id) REFERENCES conversations (thread_id) ON DELETE CASCADE
            )
        """
        )

        # ── Lesson plan specific table ──
        cursor.execute(
            """
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
        """
        )

        conn.commit()

        # ── Seed admin user ──
        self._seed_admin(conn)

        conn.close()

    def _seed_admin(self, conn: sqlite3.Connection):
        """Create the admin user from env vars if it doesn't already exist."""
        admin_email = AuthConfig.ADMIN_EMAIL
        admin_password = AuthConfig.ADMIN_PASSWORD

        if not admin_email or not admin_password:
            logger.warning(
                "ADMIN_EMAIL or ADMIN_PASSWORD not set — skipping admin seed"
            )
            return

        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE email = ?", (admin_email,))
        if cursor.fetchone():
            return  # Admin already exists

        now = datetime.now().isoformat()
        admin_id = str(uuid.uuid4())
        password_hash = bcrypt.hash(admin_password)

        cursor.execute(
            """
            INSERT INTO users (user_id, email, password_hash, role, is_active, is_email_verified, created_at, updated_at)
            VALUES (?, ?, ?, 'admin', 1, 1, ?, ?)
        """,
            (admin_id, admin_email, password_hash, now, now),
        )

        # Auto-create settings row for admin (NULL api key — uses server-side key)
        cursor.execute(
            """
            INSERT INTO user_settings (user_id, openai_api_key_encrypted, preferred_model, updated_at)
            VALUES (?, NULL, ?, ?)
        """,
            (admin_id, LLMConfig.DEFAULT_MODEL, now),
        )

        conn.commit()
        logger.info(f"Admin user seeded: {admin_email}")

    def create_course_outline(
        self,
        thread_id: str,
        user_id: str,
        conversation_type: ConversationType,
        data: CourseOutlineCreate,
    ) -> CourseOutlineMetadata:
        """Create a new course outline conversation."""
        now = datetime.now().isoformat()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Insert into base table
            cursor.execute(
                """
                INSERT INTO conversations 
                (thread_id, user_id, conversation_type, title, language, created_at, updated_at, message_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
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
                ),
            )

            # Insert into course_outlines table
            cursor.execute(
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

            conn.commit()

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
                created_at=datetime.fromisoformat(now),
                updated_at=datetime.fromisoformat(now),
                message_count=0,
            )
        finally:
            conn.close()

    def create_lesson_plan(
        self,
        thread_id: str,
        user_id: str,
        conversation_type: ConversationType,
        data: LessonPlanCreate,
    ) -> LessonPlanMetadata:
        """Create a new lesson plan conversation."""
        now = datetime.now().isoformat()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Insert into base table
            cursor.execute(
                """
                INSERT INTO conversations 
                (thread_id, user_id, conversation_type, title, language, created_at, updated_at, message_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
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
                ),
            )

            # Serialize lists to JSON strings for storage
            learning_objectives_json = json.dumps(data.learning_objectives)
            key_topics_json = json.dumps(data.key_topics)
            activities_projects_json = json.dumps(data.activities_projects)

            # Insert into lesson_plans table
            cursor.execute(
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

            conn.commit()

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
                created_at=datetime.fromisoformat(now),
                updated_at=datetime.fromisoformat(now),
                message_count=0,
            )
        finally:
            conn.close()

    def get_conversation(
        self, thread_id: str
    ) -> Optional[Union[CourseOutlineMetadata, LessonPlanMetadata]]:
        """Get a conversation by thread_id with type-specific data."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Get base conversation data
            cursor.execute(
                """
                SELECT thread_id, user_id, conversation_type, title, language, created_at, updated_at, message_count
                FROM conversations
                WHERE thread_id = ?
            """,
                (thread_id,),
            )

            row = cursor.fetchone()

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
            ) = row
            conversation_type = ConversationType(conv_type)

            # Get type-specific data
            if conversation_type == ConversationType.COURSE_OUTLINE:
                cursor.execute(
                    """
                    SELECT topic, number_of_classes, difficulty_level, target_audience, user_comment
                    FROM course_outlines
                    WHERE thread_id = ?
                """,
                    (thread_id,),
                )

                outline_row = cursor.fetchone()
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
                    created_at=datetime.fromisoformat(created_at),
                    updated_at=datetime.fromisoformat(updated_at),
                    message_count=message_count,
                )

            elif conversation_type == ConversationType.LESSON_PLAN:
                cursor.execute(
                    """
                    SELECT course_title, class_number, class_title, learning_objectives, key_topics, activities_projects, user_comment
                    FROM lesson_plans
                    WHERE thread_id = ?
                """,
                    (thread_id,),
                )

                lesson_row = cursor.fetchone()
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
                    created_at=datetime.fromisoformat(created_at),
                    updated_at=datetime.fromisoformat(updated_at),
                    message_count=message_count,
                )

            return None
        finally:
            conn.close()

    def list_conversations(
        self,
        user_id: Optional[str] = None,
        conversation_type: Optional[ConversationType] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Union[CourseOutlineMetadata, LessonPlanMetadata]]:
        """List conversations with type-specific data.

        Args:
            user_id: Filter by user. None returns all (for admin use).
            conversation_type: Filter by type.
            limit: Max results.
            offset: Pagination offset.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
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

            cursor.execute(
                f"""
                SELECT thread_id, user_id, conversation_type, title, language, created_at, updated_at, message_count
                FROM conversations
                {where_clause}
                ORDER BY updated_at DESC
                LIMIT ? OFFSET ?
            """,
                (*params, limit, offset),
            )

            rows = cursor.fetchall()
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
                ) = row
                ct = ConversationType(conv_type)

                # Fetch type-specific data
                if ct == ConversationType.COURSE_OUTLINE:
                    cursor.execute(
                        """
                        SELECT topic, number_of_classes, difficulty_level, target_audience, user_comment
                        FROM course_outlines
                        WHERE thread_id = ?
                    """,
                        (thread_id,),
                    )

                    outline_row = cursor.fetchone()
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
                                created_at=datetime.fromisoformat(created_at),
                                updated_at=datetime.fromisoformat(updated_at),
                                message_count=message_count,
                            )
                        )

                elif ct == ConversationType.LESSON_PLAN:
                    cursor.execute(
                        """
                        SELECT course_title, class_number, class_title, learning_objectives, key_topics, activities_projects, user_comment
                        FROM lesson_plans
                        WHERE thread_id = ?
                    """,
                        (thread_id,),
                    )

                    lesson_row = cursor.fetchone()
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
                                created_at=datetime.fromisoformat(created_at),
                                updated_at=datetime.fromisoformat(updated_at),
                                message_count=message_count,
                            )
                        )

            return conversations
        finally:
            conn.close()

    def increment_message_count(self, thread_id: str) -> bool:
        """Increment message count and update timestamp for any conversation type."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                UPDATE conversations
                SET message_count = message_count + 1,
                    updated_at = ?
                WHERE thread_id = ?
            """,
                (datetime.now().isoformat(), thread_id),
            )

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
            cursor.execute(
                "DELETE FROM conversations WHERE thread_id = ?", (thread_id,)
            )
            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted
        finally:
            conn.close()

    def count_conversations(
        self,
        user_id: Optional[str] = None,
        conversation_type: Optional[ConversationType] = None,
    ) -> int:
        """Count total conversations, optionally filtered by user and/or type."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            conditions = []
            params: list = []

            if user_id:
                conditions.append("user_id = ?")
                params.append(user_id)
            if conversation_type:
                conditions.append("conversation_type = ?")
                params.append(conversation_type.value)

            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

            cursor.execute(
                f"SELECT COUNT(*) FROM conversations {where_clause}",
                tuple(params),
            )

            count = cursor.fetchone()[0]
            return count
        finally:
            conn.close()

    # =========================================================================
    # User Management
    # =========================================================================

    def create_user(self, email: str, password: str) -> Optional[dict]:
        """Create a new user with hashed password and default settings.

        Returns user dict on success, None if email already exists.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            now = datetime.now().isoformat()
            user_id = str(uuid.uuid4())
            password_hash = bcrypt.hash(password)

            cursor.execute(
                """
                INSERT INTO users (user_id, email, password_hash, role, is_active, is_email_verified, created_at, updated_at)
                VALUES (?, ?, ?, 'user', 1, 0, ?, ?)
            """,
                (user_id, email, password_hash, now, now),
            )

            # Auto-create settings row with NULL api key (user is blocked until they provide one)
            cursor.execute(
                """
                INSERT INTO user_settings (user_id, openai_api_key_encrypted, preferred_model, updated_at)
                VALUES (?, NULL, ?, ?)
            """,
                (user_id, LLMConfig.DEFAULT_MODEL, now),
            )

            conn.commit()
            return {
                "user_id": user_id,
                "email": email,
                "role": "user",
                "is_active": True,
                "is_email_verified": False,
                "created_at": now,
                "updated_at": now,
            }
        except sqlite3.IntegrityError:
            return None  # Email already exists
        finally:
            conn.close()

    def get_user_by_email(self, email: str) -> Optional[dict]:
        """Get a user by email address."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT user_id, email, password_hash, role, is_active, is_email_verified, created_at, updated_at
                FROM users WHERE email = ?
            """,
                (email,),
            )
            row = cursor.fetchone()
            if not row:
                return None

            return {
                "user_id": row[0],
                "email": row[1],
                "password_hash": row[2],
                "role": row[3],
                "is_active": bool(row[4]),
                "is_email_verified": bool(row[5]),
                "created_at": row[6],
                "updated_at": row[7],
            }
        finally:
            conn.close()

    def get_user_by_id(self, user_id: str) -> Optional[dict]:
        """Get a user by user_id."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT user_id, email, password_hash, role, is_active, is_email_verified, created_at, updated_at
                FROM users WHERE user_id = ?
            """,
                (user_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None

            return {
                "user_id": row[0],
                "email": row[1],
                "password_hash": row[2],
                "role": row[3],
                "is_active": bool(row[4]),
                "is_email_verified": bool(row[5]),
                "created_at": row[6],
                "updated_at": row[7],
            }
        finally:
            conn.close()

    def verify_password(self, plain_password: str, password_hash: str) -> bool:
        """Verify a password against a bcrypt hash."""
        return bcrypt.verify(plain_password, password_hash)

    # =========================================================================
    # Session Management (Refresh Tokens)
    # =========================================================================

    def create_session(
        self, user_id: str, refresh_token_hash: str, expires_at: str
    ) -> str:
        """Create a new session with a hashed refresh token. Returns session_id."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            session_id = str(uuid.uuid4())
            now = datetime.now().isoformat()

            cursor.execute(
                """
                INSERT INTO user_sessions (session_id, user_id, refresh_token_hash, expires_at, created_at)
                VALUES (?, ?, ?, ?, ?)
            """,
                (session_id, user_id, refresh_token_hash, expires_at, now),
            )
            conn.commit()
            return session_id
        finally:
            conn.close()

    def get_session(self, session_id: str) -> Optional[dict]:
        """Get a session by session_id."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT session_id, user_id, refresh_token_hash, expires_at, created_at
                FROM user_sessions WHERE session_id = ?
            """,
                (session_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return {
                "session_id": row[0],
                "user_id": row[1],
                "refresh_token_hash": row[2],
                "expires_at": row[3],
                "created_at": row[4],
            }
        finally:
            conn.close()

    def get_session_by_refresh_hash(self, refresh_token_hash: str) -> Optional[dict]:
        """Look up a session by the SHA-256 hash of its refresh token."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT session_id, user_id, refresh_token_hash, expires_at, created_at
                FROM user_sessions WHERE refresh_token_hash = ?
            """,
                (refresh_token_hash,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return {
                "session_id": row[0],
                "user_id": row[1],
                "refresh_token_hash": row[2],
                "expires_at": row[3],
                "created_at": row[4],
            }
        finally:
            conn.close()

    def delete_session(self, session_id: str) -> bool:
        """Delete a session (logout)."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                "DELETE FROM user_sessions WHERE session_id = ?", (session_id,)
            )
            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted
        finally:
            conn.close()

    def delete_user_sessions(self, user_id: str) -> int:
        """Delete all sessions for a user (e.g., on password change). Returns count deleted."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM user_sessions WHERE user_id = ?", (user_id,))
            count = cursor.rowcount
            conn.commit()
            return count
        finally:
            conn.close()

    def cleanup_expired_sessions(self) -> int:
        """Remove expired sessions. Returns count deleted."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            now = datetime.now().isoformat()
            cursor.execute("DELETE FROM user_sessions WHERE expires_at < ?", (now,))
            count = cursor.rowcount
            conn.commit()
            return count
        finally:
            conn.close()

    # =========================================================================
    # User Settings (API Keys & Model Preferences)
    # =========================================================================

    def _get_fernet(self) -> Fernet:
        """Get Fernet cipher using the server-side ENCRYPTION_KEY."""
        key = AuthConfig.ENCRYPTION_KEY
        if not key:
            raise ValueError("ENCRYPTION_KEY not set in environment")
        return Fernet(key.encode())

    def get_user_settings(self, user_id: str) -> Optional[dict]:
        """Get user settings. Returns dict with has_api_key (bool), preferred_model, updated_at."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT openai_api_key_encrypted, preferred_model, updated_at
                FROM user_settings WHERE user_id = ?
            """,
                (user_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return {
                "has_api_key": row[0] is not None,
                "preferred_model": row[1],
                "updated_at": row[2],
            }
        finally:
            conn.close()

    def update_user_settings(
        self,
        user_id: str,
        openai_api_key: Optional[str] = None,
        preferred_model: Optional[str] = None,
    ) -> bool:
        """Update user settings. Encrypts API key before storing."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            now = datetime.now().isoformat()
            updates = ["updated_at = ?"]
            params: list = [now]

            if openai_api_key is not None:
                fernet = self._get_fernet()
                encrypted = fernet.encrypt(openai_api_key.encode()).decode()
                updates.append("openai_api_key_encrypted = ?")
                params.append(encrypted)

            if preferred_model is not None:
                updates.append("preferred_model = ?")
                params.append(preferred_model)

            params.append(user_id)

            cursor.execute(
                f"UPDATE user_settings SET {', '.join(updates)} WHERE user_id = ?",
                tuple(params),
            )
            updated = cursor.rowcount > 0
            conn.commit()
            return updated
        finally:
            conn.close()

    def get_decrypted_api_key(self, user_id: str) -> Optional[str]:
        """Get the decrypted OpenAI API key for a user. Returns None if not set."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                "SELECT openai_api_key_encrypted FROM user_settings WHERE user_id = ?",
                (user_id,),
            )
            row = cursor.fetchone()
            if not row or not row[0]:
                return None

            fernet = self._get_fernet()
            return fernet.decrypt(row[0].encode()).decode()
        finally:
            conn.close()

    def user_has_api_key(self, user_id: str) -> bool:
        """Check if a user has provided an API key."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                "SELECT openai_api_key_encrypted FROM user_settings WHERE user_id = ?",
                (user_id,),
            )
            row = cursor.fetchone()
            return row is not None and row[0] is not None
        finally:
            conn.close()

    # =========================================================================
    # Email Verification
    # =========================================================================

    def set_email_verification_token(self, user_id: str, token: str) -> bool:
        """Store an email verification token for a user."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                UPDATE users SET email_verification_token = ?, updated_at = ?
                WHERE user_id = ?
            """,
                (token, datetime.now().isoformat(), user_id),
            )
            updated = cursor.rowcount > 0
            conn.commit()
            return updated
        finally:
            conn.close()

    def verify_email(self, token: str) -> bool:
        """Verify a user's email using the one-time token. Returns True on success."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                "SELECT user_id FROM users WHERE email_verification_token = ?",
                (token,),
            )
            row = cursor.fetchone()
            if not row:
                return False

            cursor.execute(
                """
                UPDATE users
                SET is_email_verified = 1, email_verification_token = NULL, updated_at = ?
                WHERE user_id = ?
            """,
                (datetime.now().isoformat(), row[0]),
            )
            conn.commit()
            return True
        finally:
            conn.close()


# Global conversation manager instance
conversation_manager = ConversationManager()
