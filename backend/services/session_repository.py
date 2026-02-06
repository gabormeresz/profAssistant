"""
Repository for session / refresh-token management.
"""

import logging
import uuid
from datetime import datetime
from typing import Optional

from services.database import DatabaseManager

logger = logging.getLogger(__name__)


class SessionRepository:
    """Manages rows in the ``user_sessions`` table."""

    def __init__(self, db: DatabaseManager):
        self._db = db

    @property
    def conn(self):
        return self._db.conn

    async def create_session(
        self, user_id: str, refresh_token_hash: str, expires_at: str
    ) -> str:
        """Create a new session with a hashed refresh token. Returns session_id."""
        conn = self.conn

        session_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        await conn.execute(
            """
            INSERT INTO user_sessions (session_id, user_id, refresh_token_hash, expires_at, created_at)
            VALUES (?, ?, ?, ?, ?)
        """,
            (session_id, user_id, refresh_token_hash, expires_at, now),
        )
        await conn.commit()
        return session_id

    async def get_session(self, session_id: str) -> Optional[dict]:
        """Get a session by session_id."""
        conn = self.conn

        cursor = await conn.execute(
            """
            SELECT session_id, user_id, refresh_token_hash, expires_at, created_at
            FROM user_sessions WHERE session_id = ?
        """,
            (session_id,),
        )
        row = await cursor.fetchone()
        if not row:
            return None
        return {
            "session_id": row[0],
            "user_id": row[1],
            "refresh_token_hash": row[2],
            "expires_at": row[3],
            "created_at": row[4],
        }

    async def get_session_by_refresh_hash(
        self, refresh_token_hash: str
    ) -> Optional[dict]:
        """Look up a session by the SHA-256 hash of its refresh token."""
        conn = self.conn

        cursor = await conn.execute(
            """
            SELECT session_id, user_id, refresh_token_hash, expires_at, created_at
            FROM user_sessions WHERE refresh_token_hash = ?
        """,
            (refresh_token_hash,),
        )
        row = await cursor.fetchone()
        if not row:
            return None
        return {
            "session_id": row[0],
            "user_id": row[1],
            "refresh_token_hash": row[2],
            "expires_at": row[3],
            "created_at": row[4],
        }

    async def delete_session(self, session_id: str) -> bool:
        """Delete a session (logout)."""
        conn = self.conn

        cursor = await conn.execute(
            "DELETE FROM user_sessions WHERE session_id = ?", (session_id,)
        )
        deleted = cursor.rowcount > 0
        await conn.commit()
        return deleted

    async def delete_user_sessions(self, user_id: str) -> int:
        """Delete all sessions for a user (e.g., on password change). Returns count deleted."""
        conn = self.conn

        cursor = await conn.execute(
            "DELETE FROM user_sessions WHERE user_id = ?", (user_id,)
        )
        count = cursor.rowcount
        await conn.commit()
        return count

    async def cleanup_expired_sessions(self) -> int:
        """Remove expired sessions. Returns count deleted."""
        conn = self.conn

        now = datetime.now().isoformat()
        cursor = await conn.execute(
            "DELETE FROM user_sessions WHERE expires_at < ?", (now,)
        )
        count = cursor.rowcount
        await conn.commit()
        return count


# ---------------------------------------------------------------------------
#  Global instance — wired to the shared ``db`` from database.py
# ---------------------------------------------------------------------------
from services.database import db

session_repository = SessionRepository(db)
