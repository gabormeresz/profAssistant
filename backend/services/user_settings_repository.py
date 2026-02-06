"""
Repository for user settings: API-key encryption and model preferences.
"""

import logging
from datetime import datetime
from typing import Optional

from cryptography.fernet import Fernet

from config import AuthConfig
from services.database import DatabaseManager

logger = logging.getLogger(__name__)


class UserSettingsRepository:
    """Manages rows in the ``user_settings`` table."""

    def __init__(self, db: DatabaseManager):
        self._db = db

    @property
    def conn(self):
        return self._db.conn

    # ------------------------------------------------------------------
    #  Encryption helper
    # ------------------------------------------------------------------

    @staticmethod
    def _get_fernet() -> Fernet:
        """Get Fernet cipher using the server-side ENCRYPTION_KEY."""
        key = AuthConfig.ENCRYPTION_KEY
        if not key:
            raise ValueError("ENCRYPTION_KEY not set in environment")
        return Fernet(key.encode())

    # ------------------------------------------------------------------
    #  Settings CRUD
    # ------------------------------------------------------------------

    async def get_user_settings(self, user_id: str) -> Optional[dict]:
        """Get user settings."""
        conn = self.conn

        cursor = await conn.execute(
            """
            SELECT openai_api_key_encrypted, preferred_model, updated_at
            FROM user_settings WHERE user_id = ?
        """,
            (user_id,),
        )
        row = await cursor.fetchone()
        if not row:
            return None
        return {
            "has_api_key": row[0] is not None,
            "preferred_model": row[1],
            "updated_at": row[2],
        }

    async def update_user_settings(
        self,
        user_id: str,
        openai_api_key: Optional[str] = None,
        preferred_model: Optional[str] = None,
    ) -> bool:
        """Update user settings. Encrypts API key before storing."""
        conn = self.conn

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

        cursor = await conn.execute(
            f"UPDATE user_settings SET {', '.join(updates)} WHERE user_id = ?",
            tuple(params),
        )
        updated = cursor.rowcount > 0
        await conn.commit()
        return updated

    async def get_decrypted_api_key(self, user_id: str) -> Optional[str]:
        """Get the decrypted OpenAI API key for a user. Returns None if not set."""
        conn = self.conn

        cursor = await conn.execute(
            "SELECT openai_api_key_encrypted FROM user_settings WHERE user_id = ?",
            (user_id,),
        )
        row = await cursor.fetchone()
        if not row or not row[0]:
            return None

        fernet = self._get_fernet()
        return fernet.decrypt(row[0].encode()).decode()

    async def user_has_api_key(self, user_id: str) -> bool:
        """Check if a user has provided an API key."""
        conn = self.conn

        cursor = await conn.execute(
            "SELECT openai_api_key_encrypted FROM user_settings WHERE user_id = ?",
            (user_id,),
        )
        row = await cursor.fetchone()
        return row is not None and row[0] is not None


# ---------------------------------------------------------------------------
#  Global instance — wired to the shared ``db`` from database.py
# ---------------------------------------------------------------------------
from services.database import db

user_settings_repository = UserSettingsRepository(db)
