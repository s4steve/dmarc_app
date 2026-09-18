import os
import pytest
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient
from datetime import datetime, timezone

# Global test client for helper functions
_test_client = None

def get_test_client():
    """Get or create the test client"""
    global _test_client
    if _test_client is None:
        from app.main import app
        _test_client = TestClient(app)
    return _test_client

TEST_ADMIN_EMAIL = "sysadmin@test.example"
TEST_ADMIN_PASSWORD = "test-admin-password"

def get_auth_headers():
    """Log in as the in-memory test system admin (see offline_infra)"""
    client = get_test_client()
    response = client.post(
        "/api/v1/auth/login",
        json={"email": TEST_ADMIN_EMAIL, "password": TEST_ADMIN_PASSWORD}
    )
    if response.status_code == 200:
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    return {}

@pytest.fixture(autouse=True)
def offline_infra():
    """Run without Redis or a users index: fakeredis sessions, in-memory rate limits,
    and a single test system admin. Tests that patch user_service themselves override this."""
    import fakeredis
    from limits.storage import MemoryStorage
    from limits.strategies import FixedWindowRateLimiter
    from app.core.security import get_password_hash
    from app.models.user import UserInDB, UserRole
    from app.services.session_service import session_service
    from app.services.user_service import user_service
    from app.middleware.rate_limiter import limiter, user_limiter

    admin = UserInDB(
        id="test-sysadmin", email=TEST_ADMIN_EMAIL, role=UserRole.SYSTEM_ADMIN,
        customer_id="default", is_active=True, hashed_password=get_password_hash(TEST_ADMIN_PASSWORD),
        created_at="2026-01-01T00:00:00", updated_at="2026-01-01T00:00:00",
    )

    async def by_email(email):
        return admin if email == TEST_ADMIN_EMAIL else None

    saved = [(l, l._storage, l._limiter) for l in (limiter, user_limiter)]
    for l in (limiter, user_limiter):
        l._storage = MemoryStorage()
        l._limiter = FixedWindowRateLimiter(l._storage)
    with patch.object(session_service, "redis", fakeredis.FakeRedis(decode_responses=True)), \
         patch.object(user_service, "get_user_by_email", side_effect=by_email):
        yield
    for l, storage, strategy in saved:
        l._storage, l._limiter = storage, strategy

# Global mock auth headers for tests that use direct variable
mock_auth_headers = {"Authorization": "Bearer mock-test-token"}

@pytest.fixture
def auth_headers():
    """Fixture to get authentication headers"""
    return get_auth_headers()

@pytest.fixture
def mock_auth_headers_fixture():
    """Fixture providing mock auth headers"""
    return {"Authorization": "Bearer mock-test-token"}

@pytest.fixture
def authenticated_client():
    """Fixture providing an authenticated test client"""
    client = get_test_client()
    headers = get_auth_headers()
    return client, headers
