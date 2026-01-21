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

def get_auth_headers():
    """Helper function to get authentication headers for tests"""
    client = get_test_client()
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "admin123"}
    )
    if response.status_code == 200:
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    return {}

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
