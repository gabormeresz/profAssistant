"""
Repository for user CRUD, password verification, and email verification.
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Optional

from passlib.hash import bcrypt

from config import LLMConfig
from services.database import DatabaseManager

logger = logging.getLogger(__name__)


class UserRepository:
    """Manages user records in the ``users`` table."""

    def __init__(self, db: DatabaseManager):
        self._db = db

    @property
    def conn(self):
        return self._db.conn

    # ------------------------------------------------------------------
    #  User CRUD
    # ------------------------------------------------------------------

    async def create_user(self, email: str, password: str) -> Optional[dict]:
        """Create a new user with hashed password and default settings.

        Returns user dict on success, None if email already exists.
        """
        import aiosqlite

        conn = self.conn

        try:
            now = datetime.now().isoformat()
            user_id = str(uuid.uuid4())
            password_hash = await asyncio.to_thread(bcrypt.hash, password)

            await conn.execute(
                """
                INSERT INTO users (user_id, email, password_hash, role, is_active, is_email_verified, created_at, updated_at)
                VALUES (?, ?, ?, 'user', 1, 0, ?, ?)
            """,
                (user_id, email, password_hash, now, now),
            )

            # Auto-create settings row with NULL api key
            await conn.execute(
                """
                INSERT INTO user_settings (user_id, openai_api_key_encrypted, preferred_model, updated_at)
                VALUES (?, NULL, ?, ?)
            """,
                (user_id, LLMConfig.DEFAULT_MODEL, now),
            )

            await conn.commit()
            return {
                "user_id": user_id,
                "email": email,
                "role": "user",
                "is_active": True,
                "is_email_verified": False,
                "created_at": now,
                "updated_at": now,
            }
        except aiosqlite.IntegrityError:
            return None  # Email already exists

    async def get_user_by_email(self, email: str) -> Optional[dict]:
        """Get a user by email address."""
        conn = self.conn

        cursor = await conn.execute(
            """
            SELECT user_id, email, password_hash, role, is_active, is_email_verified, created_at, updated_at
            FROM users WHERE email = ?
        """,
            (email,),
        )
        row = await cursor.fetchone()
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

    async def get_user_by_id(self, user_id: str) -> Optional[dict]:
        """Get a user by user_id."""
        conn = self.conn

        cursor = await conn.execute(
            """
            SELECT user_id, email, password_hash, role, is_active, is_email_verified, created_at, updated_at
            FROM users WHERE user_id = ?
        """,
            (user_id,),
        )
        row = await cursor.fetchone()
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

    async def verify_password(self, plain_password: str, password_hash: str) -> bool:
        """Verify a password against a bcrypt hash."""
        return await asyncio.to_thread(bcrypt.verify, plain_password, password_hash)

    # ------------------------------------------------------------------
    #  Email Verification
    # ------------------------------------------------------------------

    async def set_email_verification_token(self, user_id: str, token: str) -> bool:
        """Store an email verification token for a user."""
        conn = self.conn

        cursor = await conn.execute(
            """
            UPDATE users SET email_verification_token = ?, updated_at = ?
            WHERE user_id = ?
        """,
            (token, datetime.now().isoformat(), user_id),
        )
        updated = cursor.rowcount > 0
        await conn.commit()
        return updated

    async def verify_email(self, token: str) -> bool:
        """Verify a user's email using the one-time token. Returns True on success."""
        conn = self.conn

        cursor = await conn.execute(
            "SELECT user_id FROM users WHERE email_verification_token = ?",
            (token,),
        )
        row = await cursor.fetchone()
        if not row:
            return False

        await conn.execute(
            """
            UPDATE users
            SET is_email_verified = 1, email_verification_token = NULL, updated_at = ?
            WHERE user_id = ?
        """,
            (datetime.now().isoformat(), row[0]),
        )
        await conn.commit()
        return True


# ---------------------------------------------------------------------------
#  Global instance — wired to the shared ``db`` from database.py
# ---------------------------------------------------------------------------
from services.database import db

user_repository = UserRepository(db)
