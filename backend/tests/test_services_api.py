import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from datetime import datetime

from app.main import app
from app.models.user import User
from app.models.dmarc import ThirdPartyService

client = TestClient(app)

@pytest.fixture
def mock_user():
    return User(
        id="test-user-id",
        email="test@example.com",
        customer_id="test-customer",
        role="admin",
        full_name="Test User",
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

@pytest.fixture
def system_admin_user():
    return User(
        id="admin-user-id",
        email="admin@example.com",
        customer_id="admin-customer",
        role="system_admin",
        full_name="System Admin",
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

@pytest.fixture
def mock_auth_headers():
    return {"Authorization": "Bearer valid-token"}

@pytest.fixture
def sample_service():
    return {
        "id": "service-1",
        "service_name": "Google Workspace",
        "ip_ranges": ["209.85.128.0/17", "64.233.160.0/19"],
        "domain_patterns": ["*.google.com", "*.googlemail.com"],
        "reverse_dns_patterns": ["*.google.com", "*.googlemail.com"],
        "configuration_instructions": "Add 'include:_spf.google.com' to your SPF record",
        "documentation": "Google Workspace email service documentation",
        "setup_guide": "Setup guide for Google Workspace",
        "troubleshooting": "Common troubleshooting steps",
        "is_active": True,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    }

class TestServicesPublicAPI:
    
    @patch('app.api.auth.get_current_active_user')
    @patch('app.services.third_party_service.third_party_service_identifier.get_all_services')
    def test_get_services_success(self, mock_get_services, mock_get_user, mock_user, sample_service, mock_auth_headers):
        """Test successful retrieval of services"""
        mock_get_user.return_value = mock_user
        mock_get_services.return_value = [sample_service]
        
        response = client.get("/api/v1/services/", headers=mock_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["service_name"] == "Google Workspace"
        assert data[0]["is_active"] == True
    
    @patch('app.api.auth.get_current_active_user')
    @patch('app.services.third_party_service.third_party_service_identifier.get_all_services')
    def test_get_services_empty_list(self, mock_get_services, mock_get_user, mock_user, mock_auth_headers):
        """Test retrieval when no services exist"""
        mock_get_user.return_value = mock_user
        mock_get_services.return_value = []
        
        response = client.get("/api/v1/services/", headers=mock_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0
    
    @patch('app.api.auth.get_current_active_user')
    @patch('app.services.third_party_service.third_party_service_identifier.get_all_services')
    def test_get_services_elasticsearch_error(self, mock_get_services, mock_get_user, mock_user, mock_auth_headers):
        """Test handling of Elasticsearch errors"""
        mock_get_user.return_value = mock_user
        mock_get_services.side_effect = Exception("Elasticsearch connection failed")
        
        response = client.get("/api/v1/services/", headers=mock_auth_headers)
        
        assert response.status_code == 500
        assert "Failed to get services" in response.json()["detail"]
    
    @patch('app.api.auth.get_current_active_user')
    @patch('app.services.third_party_service.third_party_service_identifier.initialize_services')
    def test_initialize_services_success(self, mock_initialize, mock_get_user, mock_user, mock_auth_headers):
        """Test successful services initialization"""
        mock_get_user.return_value = mock_user
        mock_initialize.return_value = None
        
        response = client.post("/api/v1/services/initialize", headers=mock_auth_headers)
        
        assert response.status_code == 200
        assert response.json()["message"] == "Services initialized successfully"
        mock_initialize.assert_called_once()
    
    @patch('app.api.auth.get_current_active_user')
    @patch('app.services.third_party_service.third_party_service_identifier.initialize_services')
    def test_initialize_services_error(self, mock_initialize, mock_get_user, mock_user, mock_auth_headers):
        """Test services initialization error handling"""
        mock_get_user.return_value = mock_user
        mock_initialize.side_effect = Exception("Initialization failed")
        
        response = client.post("/api/v1/services/initialize", headers=mock_auth_headers)
        
        assert response.status_code == 500
        assert "Failed to initialize services" in response.json()["detail"]
    
    def test_get_services_unauthorized(self):
        """Test services endpoint without authentication"""
        response = client.get("/api/v1/services/")
        
        assert response.status_code == 401

class TestServicesAdminAPI:
    
    @patch('app.api.auth.get_current_active_user')
    @patch('app.services.third_party_service.third_party_service_identifier.get_all_services')
    def test_get_services_admin_success(self, mock_get_services, mock_get_user, system_admin_user, sample_service, mock_auth_headers):
        """Test successful admin services retrieval"""
        mock_get_user.return_value = system_admin_user
        mock_get_services.return_value = [sample_service]
        
        response = client.get("/api/v1/services/admin", headers=mock_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["service_name"] == "Google Workspace"
        assert "documentation" in data[0]
    
    @patch('app.api.auth.get_current_active_user')
    @patch('app.services.third_party_service.third_party_service_identifier.get_service_by_id')
    def test_get_service_details_success(self, mock_get_service, mock_get_user, system_admin_user, sample_service, mock_auth_headers):
        """Test successful service details retrieval"""
        mock_get_user.return_value = system_admin_user
        mock_get_service.return_value = sample_service
        
        response = client.get("/api/v1/services/admin/service-1", headers=mock_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["service_name"] == "Google Workspace"
        assert data["documentation"] == "Google Workspace email service documentation"
    
    @patch('app.api.auth.get_current_active_user')
    @patch('app.services.third_party_service.third_party_service_identifier.get_service_by_id')
    def test_get_service_details_not_found(self, mock_get_service, mock_get_user, system_admin_user, mock_auth_headers):
        """Test service details retrieval for non-existent service"""
        mock_get_user.return_value = system_admin_user
        mock_get_service.return_value = None
        
        response = client.get("/api/v1/services/admin/nonexistent-service", headers=mock_auth_headers)
        
        assert response.status_code == 404
        assert "Service not found" in response.json()["detail"]
    
    @patch('app.api.auth.get_current_active_user')
    @patch('app.services.third_party_service.third_party_service_identifier.update_service')
    def test_update_service_success(self, mock_update_service, mock_get_user, system_admin_user, mock_auth_headers):
        """Test successful service update"""
        mock_get_user.return_value = system_admin_user
        mock_update_service.return_value = True
        
        update_data = {
            "service_name": "Updated Google Workspace",
            "documentation": "Updated documentation",
            "is_active": False
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
    @patch('app.services.third_party_service.third_party_service_identifier.update_service')
    def test_update_service_not_found(self, mock_update_service, mock_get_user, system_admin_user, mock_auth_headers):
        """Test service update for non-existent service"""
        mock_get_user.return_value = system_admin_user
        mock_update_service.return_value = False
        
        update_data = {"service_name": "Updated Name"}
        
        response = client.put(
            "/api/v1/services/admin/nonexistent-service",
            json=update_data,
            headers=mock_auth_headers
        )
        
        assert response.status_code == 404
        assert "Service not found" in response.json()["detail"]
    
    @patch('app.api.auth.get_current_active_user')
    @patch('app.services.third_party_service.third_party_service_identifier.delete_service')
    def test_delete_service_success(self, mock_delete_service, mock_get_user, system_admin_user, mock_auth_headers):
        """Test successful service deletion"""
        mock_get_user.return_value = system_admin_user
        mock_delete_service.return_value = True
        
        response = client.delete("/api/v1/services/admin/service-1", headers=mock_auth_headers)
        
        assert response.status_code == 200
        assert response.json()["message"] == "Service deleted successfully"
        mock_delete_service.assert_called_once_with("service-1")
    
    @patch('app.api.auth.get_current_active_user')
    @patch('app.services.third_party_service.third_party_service_identifier.delete_service')
    def test_delete_service_not_found(self, mock_delete_service, mock_get_user, system_admin_user, mock_auth_headers):
        """Test service deletion for non-existent service"""
        mock_get_user.return_value = system_admin_user
        mock_delete_service.return_value = False
        
        response = client.delete("/api/v1/services/admin/nonexistent-service", headers=mock_auth_headers)
        
        assert response.status_code == 404
        assert "Service not found" in response.json()["detail"]
    
    @patch('app.api.auth.get_current_active_user')
    @patch('app.services.third_party_service.third_party_service_identifier.update_service_documentation')
    def test_update_documentation_success(self, mock_update_doc, mock_get_user, system_admin_user, mock_auth_headers):
        """Test successful documentation update"""
        mock_get_user.return_value = system_admin_user
        mock_update_doc.return_value = True
        
        doc_data = {
            "service_id": "service-1",
            "documentation": "Updated comprehensive documentation",
            "setup_guide": "Updated setup guide",
            "troubleshooting": "Updated troubleshooting steps"
        }
        
        response = client.post(
            "/api/v1/services/admin/service-1/documentation",
            json=doc_data,
            headers=mock_auth_headers
        )
        
        assert response.status_code == 200
        assert response.json()["message"] == "Documentation updated successfully"
        mock_update_doc.assert_called_once_with("service-1", doc_data)
    
    @patch('app.api.auth.get_current_active_user')
    @patch('app.services.third_party_service.third_party_service_identifier.update_service_documentation')
    def test_update_documentation_service_not_found(self, mock_update_doc, mock_get_user, system_admin_user, mock_auth_headers):
        """Test documentation update for non-existent service"""
        mock_get_user.return_value = system_admin_user
        mock_update_doc.return_value = False
        
        doc_data = {
            "service_id": "nonexistent-service",
            "documentation": "Documentation"
        }
        
        response = client.post(
            "/api/v1/services/admin/nonexistent-service/documentation",
            json=doc_data,
            headers=mock_auth_headers
        )
        
        assert response.status_code == 404
        assert "Service not found" in response.json()["detail"]

class TestServiceCreation:
    
    @patch('app.api.auth.get_current_active_user')
    @patch('app.services.third_party_service.third_party_service_identifier.add_custom_service')
    def test_create_service_success(self, mock_add_service, mock_get_user, system_admin_user, mock_auth_headers):
        """Test successful service creation"""
        mock_get_user.return_value = system_admin_user
        mock_add_service.return_value = "new-service-id"
        
        new_service = {
            "service_name": "New Email Service",
            "ip_ranges": ["192.168.1.0/24", "10.0.0.0/8"],
            "domain_patterns": ["*.newservice.com"],
            "reverse_dns_patterns": ["*.newservice.com"],
            "configuration_instructions": "Add include:newservice.com to SPF",
            "documentation": "New service documentation",
            "setup_guide": "Setup guide",
            "troubleshooting": "Troubleshooting steps",
            "is_active": True
        }
        
        response = client.post("/api/v1/services/", json=new_service, headers=mock_auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "Service added successfully"
        assert data["service_id"] == "new-service-id"
    
    @patch('app.api.auth.get_current_active_user')
    @patch('app.services.third_party_service.third_party_service_identifier.add_custom_service')
    def test_create_service_minimal_data(self, mock_add_service, mock_get_user, system_admin_user, mock_auth_headers):
        """Test service creation with minimal required data"""
        mock_get_user.return_value = system_admin_user
        mock_add_service.return_value = "new-service-id"
        
        minimal_service = {
            "service_name": "Minimal Service",
            "ip_ranges": ["192.168.1.0/24"],
            "domain_patterns": [],
            "reverse_dns_patterns": [],
            "is_active": True
        }
        
        response = client.post("/api/v1/services/", json=minimal_service, headers=mock_auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "Service added successfully"
    
    @patch('app.api.auth.get_current_active_user')
    @patch('app.services.third_party_service.third_party_service_identifier.add_custom_service')
    def test_create_service_error(self, mock_add_service, mock_get_user, system_admin_user, mock_auth_headers):
        """Test service creation error handling"""
        mock_get_user.return_value = system_admin_user
        mock_add_service.side_effect = Exception("Database error")
        
        new_service = {
            "service_name": "Test Service",
            "ip_ranges": ["192.168.1.0/24"],
            "domain_patterns": [],
            "reverse_dns_patterns": [],
            "is_active": True
        }
        
        response = client.post("/api/v1/services/", json=new_service, headers=mock_auth_headers)
        
        assert response.status_code == 500
        assert "Failed to add service" in response.json()["detail"]

class TestServiceValidation:
    
    @patch('app.api.auth.get_current_active_user')
    def test_create_service_missing_required_fields(self, mock_get_user, system_admin_user, mock_auth_headers):
        """Test service creation with missing required fields"""
        mock_get_user.return_value = system_admin_user
        
        invalid_service = {
            "ip_ranges": ["192.168.1.0/24"],
            "domain_patterns": []
            # Missing service_name and is_active
        }
        
        response = client.post("/api/v1/services/", json=invalid_service, headers=mock_auth_headers)
        
        assert response.status_code == 422  # Validation error
    
    @patch('app.api.auth.get_current_active_user')
    def test_create_service_invalid_ip_range_format(self, mock_get_user, system_admin_user, mock_auth_headers):
        """Test service creation with invalid IP range format"""
        mock_get_user.return_value = system_admin_user
        
        invalid_service = {
            "service_name": "Test Service",
            "ip_ranges": ["invalid-ip-range", "256.256.256.256/24"],
            "domain_patterns": [],
            "reverse_dns_patterns": [],
            "is_active": True
        }
        
        # Note: Validation might happen at service layer rather than API layer
        with patch('app.services.third_party_service.third_party_service_identifier.add_custom_service') as mock_add:
            mock_add.side_effect = ValueError("Invalid IP range format")
            
            response = client.post("/api/v1/services/", json=invalid_service, headers=mock_auth_headers)
            
            assert response.status_code == 500
            assert "Failed to add service" in response.json()["detail"]
    
    @patch('app.api.auth.get_current_active_user')
    def test_create_service_empty_arrays(self, mock_get_user, system_admin_user, mock_auth_headers):
        """Test service creation with empty arrays"""
        mock_get_user.return_value = system_admin_user
        
        service_with_empty_arrays = {
            "service_name": "Service With Empty Arrays",
            "ip_ranges": [],
            "domain_patterns": [],
            "reverse_dns_patterns": [],
            "is_active": True
        }
        
        with patch('app.services.third_party_service.third_party_service_identifier.add_custom_service') as mock_add:
            mock_add.return_value = "new-service-id"
            
            response = client.post("/api/v1/services/", json=service_with_empty_arrays, headers=mock_auth_headers)
            
            # Should be allowed - service might be useful for documentation
            assert response.status_code == 201
    
    @patch('app.api.auth.get_current_active_user')
    def test_update_service_partial_data(self, mock_get_user, system_admin_user, mock_auth_headers):
        """Test service update with partial data"""
        mock_get_user.return_value = system_admin_user
        
        partial_update = {
            "documentation": "Updated documentation only"
        }
        
        with patch('app.services.third_party_service.third_party_service_identifier.update_service') as mock_update:
            mock_update.return_value = True
            
            response = client.put(
                "/api/v1/services/admin/service-1",
                json=partial_update,
                headers=mock_auth_headers
            )
            
            assert response.status_code == 200
            mock_update.assert_called_once_with("service-1", partial_update)

class TestElasticsearchIndexRecreation:
    
    @patch('app.api.auth.get_current_active_user')
    @patch('app.services.elasticsearch.es_service.delete_index')
    @patch('app.services.elasticsearch.es_service.create_index')
    def test_recreate_index_success(self, mock_create_index, mock_delete_index, mock_get_user, system_admin_user, mock_auth_headers):
        """Test successful index recreation"""
        mock_get_user.return_value = system_admin_user
        mock_delete_index.return_value = True
        mock_create_index.return_value = True
        
        response = client.post("/api/v1/services/admin/recreate-index", headers=mock_auth_headers)
        
        assert response.status_code == 200
        assert response.json()["message"] == "Index recreated successfully"
        mock_delete_index.assert_called_once_with("services")
        mock_create_index.assert_called_once()
    
    @patch('app.api.auth.get_current_active_user')
    @patch('app.services.elasticsearch.es_service.delete_index')
    @patch('app.services.elasticsearch.es_service.create_index')  
    def test_recreate_index_delete_error(self, mock_create_index, mock_delete_index, mock_get_user, system_admin_user, mock_auth_headers):
        """Test index recreation with delete error"""
        mock_get_user.return_value = system_admin_user
        mock_delete_index.side_effect = Exception("Failed to delete index")
        mock_create_index.return_value = True
        
        response = client.post("/api/v1/services/admin/recreate-index", headers=mock_auth_headers)
        
        assert response.status_code == 500
        assert "Failed to recreate index" in response.json()["detail"]
    
    @patch('app.api.auth.get_current_active_user')
    @patch('app.services.elasticsearch.es_service.delete_index')
    @patch('app.services.elasticsearch.es_service.create_index')
    def test_recreate_index_create_error(self, mock_create_index, mock_delete_index, mock_get_user, system_admin_user, mock_auth_headers):
        """Test index recreation with create error"""
        mock_get_user.return_value = system_admin_user
        mock_delete_index.return_value = True
        mock_create_index.side_effect = Exception("Failed to create index")
        
        response = client.post("/api/v1/services/admin/recreate-index", headers=mock_auth_headers)
        
        assert response.status_code == 500
        assert "Failed to recreate index" in response.json()["detail"]