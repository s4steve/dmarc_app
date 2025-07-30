import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from datetime import datetime, timezone

from app.main import app
from app.models.user import User, UserRole

client = TestClient(app)

@pytest.fixture
def system_admin_user():
    now = datetime.now(timezone.utc).isoformat()
    return User(
        id="admin-user-id",
        email="admin@example.com",
        customer_id="admin-customer",
        role=UserRole.SYSTEM_ADMIN,
        full_name="System Admin",
        is_active=True,
        created_at=now,
        updated_at=now
    )

@pytest.fixture
def regular_admin_user():
    now = datetime.now(timezone.utc).isoformat()
    return User(
        id="regular-admin-id",
        email="regularadmin@example.com",
        customer_id="regular-customer",
        role=UserRole.ADMIN,
        full_name="Regular Admin",
        is_active=True,
        created_at=now,
        updated_at=now
    )

@pytest.fixture
def regular_user():
    now = datetime.now(timezone.utc).isoformat()
    return User(
        id="user-id",
        email="user@example.com",
        customer_id="user-customer",
        role=UserRole.READ_ONLY,
        full_name="Regular User",
        is_active=True,
        created_at=now,
        updated_at=now
    )



class TestSystemAdminAccess:
    
    @patch('app.api.auth.get_current_active_user')
    @patch('app.services.third_party_service.third_party_service_identifier.get_all_services')
    def test_system_admin_can_access_services_admin(self, mock_get_services, mock_get_user, system_admin_user, auth_headers):
        """Test that system admin can access admin services endpoint"""
        mock_get_user.return_value = system_admin_user
        mock_services = [
            {
                "id": "service-1",
                "service_name": "Google Workspace",
                "ip_ranges": ["209.85.128.0/17"],
                "domain_patterns": ["*.google.com"],
                "reverse_dns_patterns": ["*.google.com"],
                "is_active": True
            }
        ]
        mock_get_services.return_value = mock_services
        
        response = client.get("/api/v1/services/admin", headers=mock_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["service_name"] == "Google Workspace"
    
    @patch('app.api.auth.get_current_active_user')
    def test_regular_admin_cannot_access_services_admin(self, mock_get_user, regular_admin_user, auth_headers):
        """Test that regular admin cannot access admin services endpoint"""
        mock_get_user.return_value = regular_admin_user
        
        response = client.get("/api/v1/services/admin", headers=mock_auth_headers)
        
        assert response.status_code == 403
        assert "System administrator access required" in response.json()["detail"]
    
    @patch('app.api.auth.get_current_active_user')
    def test_regular_user_cannot_access_services_admin(self, mock_get_user, regular_user, auth_headers):
        """Test that regular user cannot access admin services endpoint"""
        mock_get_user.return_value = regular_user
        
        response = client.get("/api/v1/services/admin", headers=mock_auth_headers)
        
        assert response.status_code == 403
        assert "System administrator access required" in response.json()["detail"]
    
    @patch('app.api.auth.get_current_active_user')
    @patch('app.services.third_party_service.third_party_service_identifier.get_service_by_id')
    def test_system_admin_can_get_service_details(self, mock_get_service, mock_get_user, system_admin_user, auth_headers):
        """Test that system admin can get service details"""
        mock_get_user.return_value = system_admin_user
        mock_service = {
            "id": "service-1",
            "service_name": "SendGrid",
            "ip_ranges": ["149.72.0.0/16"],
            "documentation": "SendGrid email service documentation",
            "setup_guide": "Setup guide for SendGrid",
            "is_active": True
        }
        mock_get_service.return_value = mock_service
        
        response = client.get("/api/v1/services/admin/service-1", headers=mock_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["service_name"] == "SendGrid"
        assert data["documentation"] == "SendGrid email service documentation"
    
    @patch('app.api.auth.get_current_active_user')
    @patch('app.services.third_party_service.third_party_service_identifier.update_service')
    def test_system_admin_can_update_service(self, mock_update_service, mock_get_user, system_admin_user, auth_headers):
        """Test that system admin can update services"""
        mock_get_user.return_value = system_admin_user
        mock_update_service.return_value = True
        
        update_data = {
            "service_name": "Updated Service Name",
            "documentation": "Updated documentation"
        }
        
        response = client.put(
            "/api/v1/services/admin/service-1",
            json=update_data,
            headers=mock_auth_headers
        )
        
        assert response.status_code == 200
        assert response.json()["message"] == "Service updated successfully"
        mock_update_service.assert_called_once_with("service-1", update_data)
    
    @patch('app.api.auth.get_current_active_user')
    @patch('app.services.third_party_service.third_party_service_identifier.delete_service')
    def test_system_admin_can_delete_service(self, mock_delete_service, mock_get_user, system_admin_user, auth_headers):
        """Test that system admin can delete services"""
        mock_get_user.return_value = system_admin_user
        mock_delete_service.return_value = True
        
        response = client.delete("/api/v1/services/admin/service-1", headers=mock_auth_headers)
        
        assert response.status_code == 200
        assert response.json()["message"] == "Service deleted successfully"
        mock_delete_service.assert_called_once_with("service-1")
    
    @patch('app.api.auth.get_current_active_user')
    @patch('app.services.third_party_service.third_party_service_identifier.update_service_documentation')
    def test_system_admin_can_update_documentation(self, mock_update_doc, mock_get_user, system_admin_user, auth_headers):
        """Test that system admin can update service documentation"""
        mock_get_user.return_value = system_admin_user
        mock_update_doc.return_value = True
        
        doc_data = {
            "service_id": "service-1",
            "documentation": "Updated comprehensive documentation",
            "setup_guide": "Step-by-step setup guide",
            "troubleshooting": "Common troubleshooting steps"
        }
        
        response = client.post(
            "/api/v1/services/admin/service-1/documentation",
            json=doc_data,
            headers=mock_auth_headers
        )
        
        assert response.status_code == 200
        assert response.json()["message"] == "Documentation updated successfully"
    
    @patch('app.api.auth.get_current_active_user')
    @patch('app.services.elasticsearch.es_service.delete_index')
    @patch('app.services.elasticsearch.es_service.create_index')
    def test_system_admin_can_recreate_index(self, mock_create_index, mock_delete_index, mock_get_user, system_admin_user, auth_headers):
        """Test that system admin can recreate Elasticsearch index"""
        mock_get_user.return_value = system_admin_user
        mock_delete_index.return_value = True
        mock_create_index.return_value = True
        
        response = client.post("/api/v1/services/admin/recreate-index", headers=mock_auth_headers)
        
        assert response.status_code == 200
        assert response.json()["message"] == "Index recreated successfully"

class TestRoleBasedAccessValidation:
    
    @patch('app.api.auth.get_current_active_user')
    def test_unauthenticated_user_cannot_access_admin_endpoints(self, mock_get_user):
        """Test that unauthenticated users cannot access admin endpoints"""
        mock_get_user.side_effect = Exception("Invalid token")
        
        response = client.get("/api/v1/services/admin")
        
        assert response.status_code == 401
    
    @patch('app.api.auth.get_current_active_user')
    def test_inactive_system_admin_cannot_access_admin_endpoints(self, mock_get_user, system_admin_user, auth_headers):
        """Test that inactive system admin cannot access admin endpoints"""
        system_admin_user.is_active = False
        mock_get_user.return_value = system_admin_user
        
        response = client.get("/api/v1/services/admin", headers=mock_auth_headers)
        
        # This should be handled by get_current_active_user dependency
        assert response.status_code in [401, 403]
    
    def test_invalid_token_format(self):
        """Test API with invalid token format"""
        invalid_headers = {"Authorization": "InvalidToken"}
        
        response = client.get("/api/v1/services/admin", headers=invalid_headers)
        
        assert response.status_code == 401
    
    def test_missing_authorization_header(self):
        """Test API without authorization header"""
        response = client.get("/api/v1/services/admin")
        
        assert response.status_code == 401

class TestServiceValidation:
    
    @patch('app.api.auth.get_current_active_user')
    @patch('app.services.third_party_service.third_party_service_identifier.update_service')
    def test_update_service_with_invalid_data(self, mock_update_service, mock_get_user, system_admin_user, auth_headers):
        """Test updating service with invalid data"""
        mock_get_user.return_value = system_admin_user
        mock_update_service.return_value = False  # Simulate failure
        
        # Test with missing required fields
        invalid_data = {}
        
        response = client.put(
            "/api/v1/services/admin/service-1",
            json=invalid_data,
            headers=mock_auth_headers
        )
        
        # Should still accept empty data but service layer handles validation
        assert response.status_code in [200, 400]
    
    @patch('app.api.auth.get_current_active_user')
    @patch('app.services.third_party_service.third_party_service_identifier.get_service_by_id')
    def test_get_nonexistent_service(self, mock_get_service, mock_get_user, system_admin_user, auth_headers):
        """Test getting a service that doesn't exist"""
        mock_get_user.return_value = system_admin_user
        mock_get_service.return_value = None
        
        response = client.get("/api/v1/services/admin/nonexistent-service", headers=mock_auth_headers)
        
        assert response.status_code == 404
        assert "Service not found" in response.json()["detail"]
    
    @patch('app.api.auth.get_current_active_user')
    @patch('app.services.third_party_service.third_party_service_identifier.delete_service')
    def test_delete_nonexistent_service(self, mock_delete_service, mock_get_user, system_admin_user, auth_headers):
        """Test deleting a service that doesn't exist"""
        mock_get_user.return_value = system_admin_user
        mock_delete_service.return_value = False  # Service not found
        
        response = client.delete("/api/v1/services/admin/nonexistent-service", headers=mock_auth_headers)
        
        assert response.status_code == 404
        assert "Service not found" in response.json()["detail"]
    
    @patch('app.api.auth.get_current_active_user')
    def test_update_service_with_malformed_json(self, mock_get_user, system_admin_user, auth_headers):
        """Test updating service with malformed JSON"""
        mock_get_user.return_value = system_admin_user
        
        # Send malformed JSON
        response = client.put(
            "/api/v1/services/admin/service-1",
            data='{"malformed": json}',  # Invalid JSON
            headers={**mock_auth_headers, "Content-Type": "application/json"}
        )
        
        assert response.status_code == 422  # Unprocessable Entity

class TestAdminInterfaceIntegration:
    
    @patch('app.api.auth.get_current_active_user')
    @patch('app.services.third_party_service.third_party_service_identifier.get_all_services')
    @patch('app.services.third_party_service.third_party_service_identifier.add_custom_service')
    def test_full_service_management_workflow(self, mock_add_service, mock_get_services, mock_get_user, system_admin_user, auth_headers):
        """Test complete service management workflow"""
        mock_get_user.return_value = system_admin_user
        
        # Step 1: Get all services (empty initially)
        mock_get_services.return_value = []
        response = client.get("/api/v1/services/admin", headers=mock_auth_headers)
        assert response.status_code == 200
        assert len(response.json()) == 0
        
        # Step 2: Add a new service
        mock_add_service.return_value = "new-service-id"
        new_service = {
            "service_name": "New Email Service",
            "ip_ranges": ["192.168.1.0/24"],
            "domain_patterns": ["*.newservice.com"],
            "reverse_dns_patterns": ["*.newservice.com"],
            "configuration_instructions": "Add include:newservice.com to SPF",
            "is_active": True
        }
        
        response = client.post("/api/v1/services/", json=new_service, headers=mock_auth_headers)
        assert response.status_code == 201
        
        # Step 3: Verify service was added
        mock_get_services.return_value = [{"id": "new-service-id", **new_service}]
        response = client.get("/api/v1/services/admin", headers=mock_auth_headers)
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["service_name"] == "New Email Service"
    
    @patch('app.api.auth.get_current_active_user')
    def test_access_control_across_different_endpoints(self, mock_get_user, auth_headers):
        """Test access control is consistently applied across all admin endpoints"""
        test_users = [
            (User(id="1", email="user@test.com", role="user", customer_id="c1", is_active=True, created_at=datetime.utcnow(), updated_at=datetime.utcnow()), 403),
            (User(id="2", email="admin@test.com", role="admin", customer_id="c2", is_active=True, created_at=datetime.utcnow(), updated_at=datetime.utcnow()), 403),
            (User(id="3", email="sysadmin@test.com", role="system_admin", customer_id="c3", is_active=True, created_at=datetime.utcnow(), updated_at=datetime.utcnow()), 200)
        ]
        
        admin_endpoints = [
            ("GET", "/api/v1/services/admin"),
            ("GET", "/api/v1/services/admin/test-id"),
            ("PUT", "/api/v1/services/admin/test-id"),
            ("DELETE", "/api/v1/services/admin/test-id"),
            ("POST", "/api/v1/services/admin/test-id/documentation"),
            ("POST", "/api/v1/services/admin/recreate-index")
        ]
        
        for user, expected_status in test_users:
            mock_get_user.return_value = user
            
            for method, endpoint in admin_endpoints:
                if method == "GET":
                    with patch('app.services.third_party_service.third_party_service_identifier.get_all_services', return_value=[]):
                        with patch('app.services.third_party_service.third_party_service_identifier.get_service_by_id', return_value={"id": "test"}):
                            response = client.get(endpoint, headers=mock_auth_headers)
                elif method == "PUT":
                    with patch('app.services.third_party_service.third_party_service_identifier.update_service', return_value=True):
                        response = client.put(endpoint, json={}, headers=mock_auth_headers)
                elif method == "DELETE":
                    with patch('app.services.third_party_service.third_party_service_identifier.delete_service', return_value=True):
                        response = client.delete(endpoint, headers=mock_auth_headers)
                elif method == "POST" and "documentation" in endpoint:
                    with patch('app.services.third_party_service.third_party_service_identifier.update_service_documentation', return_value=True):
                        response = client.post(endpoint, json={"service_id": "test"}, headers=mock_auth_headers)
                elif method == "POST" and "recreate-index" in endpoint:
                    with patch('app.services.elasticsearch.es_service.delete_index', return_value=True):
                        with patch('app.services.elasticsearch.es_service.create_index', return_value=True):
                            response = client.post(endpoint, headers=mock_auth_headers)
                
                if user.role == "system_admin":
                    assert response.status_code in [200, 201, 404], f"Failed for {method} {endpoint} with system_admin"
                else:
                    assert response.status_code == 403, f"Failed for {method} {endpoint} with role {user.role}"