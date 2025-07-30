import pytest
from unittest.mock import patch

@pytest.fixture
def auth_headers():
    with patch('app.core.security.create_access_token') as mock_create_token:
        mock_create_token.return_value = "mock-token"
        yield {"Authorization": f"Bearer mock-token"}
