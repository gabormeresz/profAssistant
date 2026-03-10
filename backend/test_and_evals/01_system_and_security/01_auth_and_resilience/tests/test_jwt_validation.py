"""
Test 1.1c — JWT Validation
===========================

**Objective:** Verify that calling protected endpoints (generation, conversations,
user settings) with an expired, invalid, or missing Bearer token results in a
strict ``401 Unauthorized`` rejection — blocking LLM calls before any token
consumption or database modification occurs.

**Strategy:**
We create a *raw* FastAPI test application **without** the ``get_current_user``
dependency override used by the other 1.1 tests.  Instead we patch only the
database and MCP lifespan services (so no real SQLite/MCP is needed) and let
the real ``get_current_user`` dependency run.  This way:

- Missing ``Authorization`` header → ``get_current_user`` raises 401
- Malformed / garbage token       → ``decode_access_token`` raises 401
- Expired token                   → ``jwt.ExpiredSignatureError`` → 401
- Wrong-secret token              → ``jwt.InvalidTokenError`` → 401
- Wrong token type (refresh)      → ``jwt.InvalidTokenError`` → 401
- Valid token, user not found     → user lookup raises 401
- Valid token, deactivated user   → 403 Forbidden

We test a *representative set* of protected endpoints across all three routers
to confirm the guard is applied consistently:

- ``POST /course-outline-generator``   (generation router)
- ``POST /enhance-prompt``             (generation router)
- ``GET  /auth/me``                    (auth router)
- ``GET  /auth/settings``              (auth router)
- ``GET  /conversations``              (conversations router)
"""

import time
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import jwt as pyjwt
import httpx
import pytest
import pytest_asyncio


# ---------------------------------------------------------------------------
# Test-local JWT secret — matches what AuthConfig will use in the test env
# ---------------------------------------------------------------------------
# We read the real secret from config so tokens we forge are signed correctly
# (or intentionally incorrectly, depending on the test).
from config import AuthConfig

JWT_SECRET = AuthConfig.JWT_SECRET
JWT_ALGORITHM = AuthConfig.JWT_ALGORITHM


# ---------------------------------------------------------------------------
# Helper: forge tokens
# ---------------------------------------------------------------------------


def _make_access_token(
    user_id: str = "test-user-jwt",
    role: str = "user",
    token_type: str = "access",
    expire_minutes: int = 30,
    secret: str | None = None,
) -> str:
    """Create a JWT access token with customisable claims."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "role": role,
        "type": token_type,
        "iat": now,
        "exp": now + timedelta(minutes=expire_minutes),
    }
    return pyjwt.encode(payload, secret or JWT_SECRET, algorithm=JWT_ALGORITHM)


def _make_expired_token(user_id: str = "test-user-jwt") -> str:
    """Create a JWT that expired 10 minutes ago."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "role": "user",
        "type": "access",
        "iat": now - timedelta(minutes=40),
        "exp": now - timedelta(minutes=10),
    }
    return pyjwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


# ---------------------------------------------------------------------------
# Fixtures — raw app WITHOUT auth override
# ---------------------------------------------------------------------------

FAKE_ACTIVE_USER = {
    "user_id": "test-user-jwt",
    "email": "jwt@test.com",
    "role": "user",
    "password_hash": "xxx",
    "is_active": True,
    "is_email_verified": False,
    "created_at": datetime.now(timezone.utc).isoformat(),
    "updated_at": datetime.now(timezone.utc).isoformat(),
}

FAKE_DEACTIVATED_USER = {
    **FAKE_ACTIVE_USER,
    "user_id": "deactivated-user",
    "is_active": False,
}


@pytest_asyncio.fixture(scope="module")
async def jwt_app():
    """
    FastAPI app with real auth but stubbed DB / MCP.

    Unlike the session-scoped ``test_app`` in the root conftest (which
    overrides ``get_current_user``), this fixture lets the real dependency
    run so we can test JWT validation end-to-end.
    """
    with (
        patch("services.database.db.connect", new_callable=AsyncMock),
        patch("services.database.db.close", new_callable=AsyncMock),
        patch("services.mcp_client.mcp_manager.initialize", new_callable=AsyncMock),
        patch("services.mcp_client.mcp_manager.cleanup", new_callable=AsyncMock),
    ):
        from main import app

        # Make sure NO dependency override for get_current_user is present
        from services.auth_service import get_current_user

        app.dependency_overrides.pop(get_current_user, None)

        yield app

        app.dependency_overrides.clear()


@pytest_asyncio.fixture()
async def jwt_client(jwt_app):
    """Async HTTP client bound to the JWT test application."""
    transport = httpx.ASGITransport(app=jwt_app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as ac:
        yield ac


# ---------------------------------------------------------------------------
# Representative protected endpoints to test
# ---------------------------------------------------------------------------
PROTECTED_ENDPOINTS = [
    # (method, path, kwargs)
    (
        "POST",
        "/course-outline-generator",
        {
            "data": {
                "message": "test",
                "topic": "AI",
                "number_of_classes": "4",
                "language": "English",
            }
        },
    ),
    ("POST", "/enhance-prompt", {"data": {"message": "test"}}),
    ("GET", "/auth/me", {}),
    ("GET", "/auth/settings", {}),
    ("GET", "/conversations", {}),
]

ENDPOINT_IDS = [
    "course-outline-generator",
    "enhance-prompt",
    "auth-me",
    "auth-settings",
    "conversations",
]


# ═══════════════════════════════════════════════════════════════════════════
# 1. Missing token
# ═══════════════════════════════════════════════════════════════════════════


class TestMissingToken:
    """Requests without an Authorization header must be rejected with 401."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "method,path,kwargs", PROTECTED_ENDPOINTS, ids=ENDPOINT_IDS
    )
    async def test_no_auth_header_returns_401(self, jwt_client, method, path, kwargs):
        response = await jwt_client.request(method, path, **kwargs)
        assert response.status_code == 401, (
            f"{method} {path} returned {response.status_code} instead of 401 "
            f"when no Authorization header was sent"
        )
        body = response.json()
        assert "detail" in body


# ═══════════════════════════════════════════════════════════════════════════
# 2. Malformed / garbage token
# ═══════════════════════════════════════════════════════════════════════════


class TestMalformedToken:
    """Non-JWT strings in the Authorization header must be rejected with 401."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "bad_token",
        [
            "not-a-jwt",
            "eyJhbGciOiJIUzI1NiJ9.INVALID.GARBAGE",
            "",
            "Bearer nested-bearer",
            "a.b.c",
        ],
        ids=["plaintext", "corrupt-jwt", "empty", "nested-bearer", "three-dots"],
    )
    async def test_malformed_token_returns_401(self, jwt_client, bad_token):
        headers = {"Authorization": f"Bearer {bad_token}"}
        response = await jwt_client.get("/auth/me", headers=headers)
        assert (
            response.status_code == 401
        ), f"Malformed token '{bad_token[:30]}' was not rejected"

    @pytest.mark.asyncio
    async def test_malformed_token_blocks_generation(self, jwt_client):
        """Generation endpoint also rejects garbage tokens before any LLM call."""
        headers = {"Authorization": "Bearer not-a-real-token"}
        response = await jwt_client.post(
            "/course-outline-generator",
            data={
                "message": "test",
                "topic": "AI",
                "number_of_classes": "4",
                "language": "English",
            },
            headers=headers,
        )
        assert response.status_code == 401


# ═══════════════════════════════════════════════════════════════════════════
# 3. Expired token
# ═══════════════════════════════════════════════════════════════════════════


class TestExpiredToken:
    """Tokens past their ``exp`` claim must be rejected with 401."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "method,path,kwargs",
        PROTECTED_ENDPOINTS,
        ids=ENDPOINT_IDS,
    )
    async def test_expired_token_returns_401(self, jwt_client, method, path, kwargs):
        token = _make_expired_token()
        headers = {"Authorization": f"Bearer {token}"}
        response = await jwt_client.request(method, path, headers=headers, **kwargs)
        assert (
            response.status_code == 401
        ), f"{method} {path} accepted an expired token (got {response.status_code})"
        body = response.json()
        assert "expired" in body["detail"].lower()


# ═══════════════════════════════════════════════════════════════════════════
# 4. Wrong secret
# ═══════════════════════════════════════════════════════════════════════════


class TestWrongSecretToken:
    """Tokens signed with a different secret must be rejected with 401."""

    @pytest.mark.asyncio
    async def test_wrong_secret_returns_401(self, jwt_client):
        token = _make_access_token(
            secret="completely-wrong-secret-key-that-does-not-match"
        )
        headers = {"Authorization": f"Bearer {token}"}
        response = await jwt_client.get("/auth/me", headers=headers)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_wrong_secret_blocks_generation(self, jwt_client):
        token = _make_access_token(
            secret="completely-wrong-secret-key-that-does-not-match"
        )
        headers = {"Authorization": f"Bearer {token}"}
        response = await jwt_client.post(
            "/course-outline-generator",
            data={
                "message": "test",
                "topic": "AI",
                "number_of_classes": "4",
                "language": "English",
            },
            headers=headers,
        )
        assert response.status_code == 401


# ═══════════════════════════════════════════════════════════════════════════
# 5. Wrong token type
# ═══════════════════════════════════════════════════════════════════════════


class TestWrongTokenType:
    """A refresh-type JWT must not be accepted as an access token."""

    @pytest.mark.asyncio
    async def test_refresh_token_type_returns_401(self, jwt_client):
        token = _make_access_token(token_type="refresh")
        headers = {"Authorization": f"Bearer {token}"}
        response = await jwt_client.get("/auth/me", headers=headers)
        assert response.status_code == 401
        body = response.json()
        assert "invalid" in body["detail"].lower() or "token" in body["detail"].lower()

    @pytest.mark.asyncio
    async def test_arbitrary_token_type_returns_401(self, jwt_client):
        token = _make_access_token(token_type="admin_override")
        headers = {"Authorization": f"Bearer {token}"}
        response = await jwt_client.get("/auth/me", headers=headers)
        assert response.status_code == 401


# ═══════════════════════════════════════════════════════════════════════════
# 6. Valid token but user not found / deactivated
# ═══════════════════════════════════════════════════════════════════════════


class TestUserLookupFailures:
    """
    Even with a cryptographically valid token, access must be denied if the
    user no longer exists or is deactivated.
    """

    @pytest.mark.asyncio
    async def test_nonexistent_user_returns_401(self, jwt_client):
        """User ID in token does not exist in the database → 401."""
        token = _make_access_token(user_id="ghost-user-does-not-exist")
        headers = {"Authorization": f"Bearer {token}"}
        with patch(
            "services.auth_service.user_repository.get_user_by_id",
            new=AsyncMock(return_value=None),
        ):
            response = await jwt_client.get("/auth/me", headers=headers)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_deactivated_user_returns_403(self, jwt_client):
        """User exists but ``is_active=False`` → 403 Forbidden."""
        token = _make_access_token(user_id="deactivated-user")
        headers = {"Authorization": f"Bearer {token}"}
        with patch(
            "services.auth_service.user_repository.get_user_by_id",
            new=AsyncMock(return_value=FAKE_DEACTIVATED_USER),
        ):
            response = await jwt_client.get("/auth/me", headers=headers)
        assert response.status_code == 403


# ═══════════════════════════════════════════════════════════════════════════
# 7. Valid token — positive control
# ═══════════════════════════════════════════════════════════════════════════


class TestValidTokenAccepted:
    """
    Positive control: a correctly signed, non-expired access token for an
    active user must NOT be rejected at the auth layer.

    We don't check the full response body (the downstream handler may fail
    due to missing DB data), only that the status code is NOT 401/403.
    """

    @pytest.mark.asyncio
    async def test_valid_token_passes_auth(self, jwt_client):
        token = _make_access_token(user_id="test-user-jwt")
        headers = {"Authorization": f"Bearer {token}"}
        with patch(
            "services.auth_service.user_repository.get_user_by_id",
            new=AsyncMock(return_value=FAKE_ACTIVE_USER),
        ):
            response = await jwt_client.get("/auth/me", headers=headers)
        # Should NOT be 401/403 — may be 200 or another code depending on DB state
        assert response.status_code not in (
            401,
            403,
        ), f"/auth/me rejected a valid token with {response.status_code}"

    @pytest.mark.asyncio
    async def test_valid_token_passes_auth_on_conversations(self, jwt_client):
        """Conversations endpoint also accepts valid tokens."""
        token = _make_access_token(user_id="test-user-jwt")
        headers = {"Authorization": f"Bearer {token}"}
        with patch(
            "services.auth_service.user_repository.get_user_by_id",
            new=AsyncMock(return_value=FAKE_ACTIVE_USER),
        ):
            response = await jwt_client.get("/conversations", headers=headers)
        assert response.status_code not in (401, 403)


# ═══════════════════════════════════════════════════════════════════════════
# 8. Cross-endpoint consistency
# ═══════════════════════════════════════════════════════════════════════════


class TestCrossEndpointConsistency:
    """
    Confirm that the JWT guard is applied uniformly across different routers
    and HTTP methods.  All endpoints should return the same 401 detail
    structure for the same failure mode.
    """

    @pytest.mark.asyncio
    async def test_all_endpoints_return_consistent_401_detail(self, jwt_client):
        """
        All protected endpoints should return a JSON body with a ``detail``
        field when the token is missing.
        """
        details = []
        for method, path, kwargs in PROTECTED_ENDPOINTS:
            response = await jwt_client.request(method, path, **kwargs)
            assert response.status_code == 401
            body = response.json()
            assert "detail" in body
            details.append(body["detail"])

        # All details should be the same string (consistent error messaging)
        assert (
            len(set(details)) == 1
        ), f"Inconsistent 401 detail messages across endpoints: {details}"

    @pytest.mark.asyncio
    async def test_expired_token_message_consistent(self, jwt_client):
        """Expired token → all endpoints should return the same expiry message."""
        token = _make_expired_token()
        headers = {"Authorization": f"Bearer {token}"}
        details = []
        for method, path, kwargs in PROTECTED_ENDPOINTS:
            response = await jwt_client.request(method, path, headers=headers, **kwargs)
            assert response.status_code == 401
            details.append(response.json()["detail"])

        assert len(set(details)) == 1, f"Inconsistent expired-token messages: {details}"
