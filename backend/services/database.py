"""
Shared database connection manager.

Owns the single ``aiosqlite`` connection, schema initialisation, and
admin seeding.  All repository classes receive their connection from
the :pyattr:`DatabaseManager.conn` property.
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Optional

import aiosqlite
from passlib.hash import bcrypt

from config import AuthConfig, DBConfig, LLMConfig

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages the persistent aiosqlite connection and DB schema.

    Call ``await .connect()`` once at application startup and
    ``await .close()`` at shutdown.
    """

    def __init__(self, db_path: str = DBConfig.CONVERSATIONS_DB):
        self.db_path = db_path
        self._conn: Optional[aiosqlite.Connection] = None

    # ------------------------------------------------------------------
    #  Connection lifecycle
    # ------------------------------------------------------------------

    async def connect(self):
        """Open the persistent database connection and initialise the schema."""
        self._conn = await aiosqlite.connect(self.db_path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.execute("PRAGMA journal_mode=WAL")
        await self._conn.execute("PRAGMA foreign_keys = ON")
        await self._init_db()

    async def close(self):
        """Close the persistent database connection."""
        if self._conn:
            await self._conn.close()
            self._conn = None

    @property
    def conn(self) -> aiosqlite.Connection:
        """Return the active connection, raising if not connected."""
        if self._conn is None:
            raise RuntimeError(
                "DatabaseManager is not connected. " "Call 'await db.connect()' first."
            )
        return self._conn

    # ------------------------------------------------------------------
    #  Schema initialisation
    # ------------------------------------------------------------------

    async def _init_db(self):
        """Initialize the database schema with all tables and seed admin user."""
        conn = self.conn

        # ── Users table ──
        await conn.execute(
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
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users (email)"
        )

        # ── User sessions table (refresh tokens) ──
        await conn.execute(
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
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_sessions_user_expires ON user_sessions (user_id, expires_at)"
        )

        # ── User settings table (1:1 with users) ──
        await conn.execute(
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
        await conn.execute(
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
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations (user_id)"
        )

        # ── Course outline specific table ──
        await conn.execute(
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
        await conn.execute(
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

        # ── Presentation specific table ──
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS presentations (
                thread_id TEXT PRIMARY KEY,
                course_title TEXT NOT NULL,
                class_number INTEGER NOT NULL,
                class_title TEXT NOT NULL,
                learning_objective TEXT,
                key_points TEXT,
                lesson_breakdown TEXT,
                activities TEXT,
                homework TEXT,
                extra_activities TEXT,
                user_comment TEXT,
                FOREIGN KEY (thread_id) REFERENCES conversations (thread_id) ON DELETE CASCADE
            )
        """
        )

        await conn.commit()

        # ── Seed admin user ──
        await self._seed_admin()

    async def _seed_admin(self):
        """Create the admin user from env vars if it doesn't already exist."""
        admin_email = AuthConfig.ADMIN_EMAIL
        admin_password = AuthConfig.ADMIN_PASSWORD

        if not admin_email or not admin_password:
            logger.warning(
                "ADMIN_EMAIL or ADMIN_PASSWORD not set — skipping admin seed"
            )
            return

        conn = self.conn
        cursor = await conn.execute(
            "SELECT user_id FROM users WHERE email = ?", (admin_email,)
        )
        if await cursor.fetchone():
            return  # Admin already exists

        now = datetime.now().isoformat()
        admin_id = str(uuid.uuid4())
        password_hash = await asyncio.to_thread(bcrypt.hash, admin_password)

        await conn.execute(
            """
            INSERT INTO users (user_id, email, password_hash, role, is_active, is_email_verified, created_at, updated_at)
            VALUES (?, ?, ?, 'admin', 1, 1, ?, ?)
        """,
            (admin_id, admin_email, password_hash, now, now),
        )

        # Auto-create settings row for admin (NULL api key — uses server-side key)
        await conn.execute(
            """
            INSERT INTO user_settings (user_id, openai_api_key_encrypted, preferred_model, updated_at)
            VALUES (?, NULL, ?, ?)
        """,
            (admin_id, LLMConfig.DEFAULT_MODEL, now),
        )

        await conn.commit()
        logger.info(f"Admin user seeded: {admin_email}")


# Global instance — call .connect() in FastAPI lifespan
db = DatabaseManager()
