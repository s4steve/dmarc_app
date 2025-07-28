import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
from app.main import app
from app.models.user import User, UserCreate, UserUpdate

client = TestClient(app)

# Sample test data
sample_user_data = {
    "id": "test-user-id",
    "email": "test@example.com",
    "full_name": "Test User",
    "role": "admin",
    "customer_id": "test-customer",
    "is_active": True,
    "created_at": "2025-07-28T10:00:00",
    "updated_at": "2025-07-28T10:00:00"
}

admin_token_data = {
    "sub": "admin@example.com",
    "customer_id": "default",
    "role": "system_admin",
    "user_id": "admin"
}

def get_auth_headers():
    """Get authorization headers for testing"""
    response = client.post("/api/v1/auth/login", json={
        "email": "admin@example.com",
        "password": "admin123"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

class TestUserEndpoints:
    """Test suite for user management endpoints"""
    
    def test_get_users_endpoint_success(self):
        """Test successful retrieval of users list"""
        with patch('app.services.user_service.user_service.get_users_by_customer') as mock_get_users:
            # Mock the async method
            mock_get_users.return_value = [User(**sample_user_data)]
            
            headers = get_auth_headers()
            response = client.get("/api/v1/users/", headers=headers)
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            
    def test_get_users_endpoint_empty_list(self):
        """Test users endpoint returns empty list when no users exist"""
        with patch('app.services.user_service.user_service.get_users_by_customer') as mock_get_users:
            # Mock empty result
            mock_get_users.return_value = []
            
            headers = get_auth_headers()
            response = client.get("/api/v1/users/", headers=headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data == []
            
    def test_get_users_endpoint_unauthorized(self):
        """Test users endpoint requires authentication"""
        response = client.get("/api/v1/users/")
        assert response.status_code == 403  # No auth header provided
        
    def test_get_users_endpoint_invalid_token(self):
        """Test users endpoint rejects invalid token"""
        headers = {"Authorization": "Bearer invalid-token"}
        response = client.get("/api/v1/users/", headers=headers)
        assert response.status_code == 401
        
    def test_create_user_endpoint_success(self):
        """Test successful user creation"""
        with patch('app.services.user_service.user_service.get_user_by_email') as mock_get_by_email, \
             patch('app.services.user_service.user_service.create_user') as mock_create:
            
            # Mock no existing user and successful creation
            mock_get_by_email.return_value = None
            mock_create.return_value = User(**sample_user_data)
            
            headers = get_auth_headers()
            user_data = {
                "email": "newuser@example.com",
                "password": "password123",
                "full_name": "New User",
                "role": "admin",
                "customer_id": "test-customer",
                "is_active": True
            }
            
            response = client.post("/api/v1/users/", json=user_data, headers=headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data["email"] == sample_user_data["email"]
            
    def test_create_user_endpoint_duplicate_email(self):
        """Test user creation fails with duplicate email"""
        with patch('app.services.user_service.user_service.get_user_by_email') as mock_get_by_email:
            # Mock existing user
            mock_get_by_email.return_value = User(**sample_user_data)
            
            headers = get_auth_headers()
            user_data = {
                "email": "test@example.com",
                "password": "password123",
                "full_name": "Test User",
                "role": "admin",
                "customer_id": "test-customer",
                "is_active": True
            }
            
            response = client.post("/api/v1/users/", json=user_data, headers=headers)
            
            assert response.status_code == 400
            assert "already exists" in response.json()["detail"]
            
    def test_update_user_endpoint_success(self):
        """Test successful user update"""
        with patch('app.services.user_service.user_service.get_user_by_id') as mock_get_by_id, \
             patch('app.services.user_service.user_service.update_user') as mock_update:
            
            # Mock existing user and successful update
            mock_get_by_id.return_value = User(**sample_user_data)
            updated_data = {**sample_user_data, "full_name": "Updated Name"}
            mock_update.return_value = User(**updated_data)
            
            headers = get_auth_headers()
            update_data = {"full_name": "Updated Name"}
            
            response = client.put("/api/v1/users/test-user-id", json=update_data, headers=headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data["full_name"] == "Updated Name"
            
    def test_update_user_endpoint_not_found(self):
        """Test user update fails when user not found"""
        with patch('app.services.user_service.user_service.get_user_by_id') as mock_get_by_id:
            # Mock user not found
            mock_get_by_id.return_value = None
            
            headers = get_auth_headers()
            update_data = {"full_name": "Updated Name"}
            
            response = client.put("/api/v1/users/nonexistent-id", json=update_data, headers=headers)
            
            assert response.status_code == 404
            assert "not found" in response.json()["detail"]
            
    def test_delete_user_endpoint_success(self):
        """Test successful user deletion"""
        with patch('app.services.user_service.user_service.get_user_by_id') as mock_get_by_id, \
             patch('app.services.user_service.user_service.delete_user') as mock_delete:
            
            # Mock existing user and successful deletion
            mock_get_by_id.return_value = User(**sample_user_data)
            mock_delete.return_value = True
            
            headers = get_auth_headers()
            
            response = client.delete("/api/v1/users/test-user-id", headers=headers)
            
            assert response.status_code == 200
            data = response.json()
            assert "deleted successfully" in data["message"]
            
    def test_delete_user_endpoint_not_found(self):
        """Test user deletion fails when user not found"""
        with patch('app.services.user_service.user_service.get_user_by_id') as mock_get_by_id:
            # Mock user not found
            mock_get_by_id.return_value = None
            
            headers = get_auth_headers()
            
            response = client.delete("/api/v1/users/nonexistent-id", headers=headers)
            
            assert response.status_code == 404
            assert "not found" in response.json()["detail"]
            
    def test_delete_user_endpoint_cannot_delete_self(self):
        """Test user cannot delete themselves"""
        with patch('app.services.user_service.user_service.get_user_by_id') as mock_get_by_id:
            # Mock user trying to delete themselves
            self_data = {**sample_user_data, "id": "admin"}
            mock_get_by_id.return_value = User(**self_data)
            
            headers = get_auth_headers()
            
            response = client.delete("/api/v1/users/admin", headers=headers)
            
            assert response.status_code == 400
            assert "Cannot delete yourself" in response.json()["detail"]

class TestUserServiceAsyncFunctionality:
    """Test suite for async functionality in user service"""
    
    @pytest.mark.asyncio
    async def test_user_service_methods_are_async(self):
        """Test that all user service methods are properly async"""
        from app.services.user_service import user_service
        import inspect
        
        # Check that key methods are async
        methods_to_check = [
            'create_user',
            'get_user_by_email', 
            'get_user_by_id',
            'authenticate_user',
            'get_users_by_customer',
            'update_user',
            'delete_user'
        ]
        
        for method_name in methods_to_check:
            method = getattr(user_service, method_name)
            assert inspect.iscoroutinefunction(method), f"{method_name} should be async"
            
    @pytest.mark.asyncio
    async def test_get_users_by_customer_async(self):
        """Test get_users_by_customer works as async method"""
        from app.services.user_service import user_service
        
        with patch('app.services.elasticsearch.es_service.search_documents') as mock_search:
            # Mock Elasticsearch response
            mock_search.return_value = {
                "hits": {
                    "hits": [],
                    "total": {"value": 0}
                }
            }
            
            # This should not raise an error if properly async
            result = await user_service.get_users_by_customer("test-customer")
            assert isinstance(result, list)
            assert result == []
            
    @pytest.mark.asyncio 
    async def test_create_user_async(self):
        """Test create_user works as async method"""
        from app.services.user_service import user_service
        from app.models.user import UserCreate
        
        with patch('app.services.elasticsearch.es_service.index_document') as mock_index:
            mock_index.return_value = None
            
            user_data = UserCreate(
                email="test@example.com",
                password="password123",
                full_name="Test User",
                role="admin",
                customer_id="test-customer",
                is_active=True
            )
            
            # This should not raise an error if properly async
            result = await user_service.create_user(user_data)
            assert result.email == "test@example.com"
            assert result.full_name == "Test User"

class TestUserEndpointIntegration:
    """Integration tests for user endpoints working with async service layer"""
    
    def test_users_endpoint_integration_no_500_error(self):
        """Test that users endpoint doesn't throw 500 errors due to async issues"""
        headers = get_auth_headers()
        
        # This should return 200, not 500
        response = client.get("/api/v1/users/", headers=headers)
        assert response.status_code == 200
        
        # Should return valid JSON
        data = response.json()
        assert isinstance(data, list)
        
    def test_current_user_endpoint_works(self):
        """Test that /me endpoint works correctly"""
        headers = get_auth_headers()
        
        response = client.get("/api/v1/users/me", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["email"] == "admin@example.com"
        assert data["role"] == "system_admin"