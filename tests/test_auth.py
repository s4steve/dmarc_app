"""
Tests for authentication functionality
"""
import pytest
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient

class TestAuthentication:
    """Test authentication and authorization functionality"""
    
    def test_login_success(self, test_client):
        """Test successful login - REGRESSION TEST for login hanging issues"""
        response = test_client.post(
            "/api/v1/auth/login",
            json={
                "email": "admin@example.com",
                "password": "admin123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0
    
    def test_login_invalid_credentials(self, test_client):
        """Test login with invalid credentials"""
        response = test_client.post(
            "/api/v1/auth/login",
            json={
                "email": "admin@example.com",
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == 401
        assert response.json()["detail"] == "Incorrect email or password"
    
    def test_login_invalid_email(self, test_client):
        """Test login with invalid email"""
        response = test_client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "admin123"
            }
        )
        
        assert response.status_code == 401
        assert response.json()["detail"] == "Incorrect email or password"
    
    def test_login_missing_fields(self, test_client):
        """Test login with missing fields"""
        response = test_client.post(
            "/api/v1/auth/login",
            json={
                "email": "admin@example.com"
                # Missing password
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_login_malformed_json(self, test_client):
        """Test login with malformed JSON"""
        response = test_client.post(
            "/api/v1/auth/login",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
    
    def test_protected_endpoint_with_valid_token(self, test_client):
        """Test accessing protected endpoint with valid token"""
        # First login to get token
        login_response = test_client.post(
            "/api/v1/auth/login",
            json={
                "email": "admin@example.com",
                "password": "admin123"
            }
        )
        token = login_response.json()["access_token"]
        
        # Use token to access protected endpoint
        with patch('backend.app.api.dmarc.dmarc_service') as mock_service:
            mock_service.get_reports_summary.return_value = Mock(
                total_emails=0, passed_emails=0, failed_emails=0,
                pass_rate=0.0, date_range={}, top_services=[]
            )
            
            response = test_client.get(
                "/api/v1/dmarc/summary",
                headers={"Authorization": f"Bearer {token}"}
            )
        
        assert response.status_code == 200
    
    def test_protected_endpoint_without_token(self, test_client):
        """Test accessing protected endpoint without token"""
        response = test_client.get("/api/v1/dmarc/summary")
        
        assert response.status_code == 403
        assert response.json()["detail"] == "Not authenticated"
    
    def test_protected_endpoint_with_invalid_token(self, test_client):
        """Test accessing protected endpoint with invalid token"""
        response = test_client.get(
            "/api/v1/dmarc/summary",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        assert response.status_code == 401
        assert response.json()["detail"] == "Could not validate credentials"
    
    def test_protected_endpoint_with_malformed_token(self, test_client):
        """Test accessing protected endpoint with malformed token"""
        response = test_client.get(
            "/api/v1/dmarc/summary",
            headers={"Authorization": "NotBearer token"}
        )
        
        assert response.status_code == 403
    
    def test_token_expiration_handling(self, test_client):
        """Test handling of expired tokens"""
        # Create an expired token (this is a simplified test)
        from jose import jwt
        from datetime import datetime, timedelta
        
        expired_payload = {
            "sub": "admin@example.com",
            "exp": datetime.utcnow() - timedelta(hours=1)  # Expired 1 hour ago
        }
        expired_token = jwt.encode(expired_payload, "test_secret", algorithm="HS256")
        
        response = test_client.get(
            "/api/v1/dmarc/summary",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        
        assert response.status_code == 401
        assert response.json()["detail"] == "Could not validate credentials"
    
    def test_login_response_does_not_hang(self, test_client):
        """Test that login completes quickly and doesn't hang - REGRESSION TEST"""
        import time
        
        start_time = time.time()
        
        response = test_client.post(
            "/api/v1/auth/login",
            json={
                "email": "admin@example.com",
                "password": "admin123"
            }
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Login should complete within 5 seconds (generous allowance for CI/test environment)
        assert duration < 5.0, f"Login took {duration} seconds, which is too long"
        assert response.status_code == 200
    
    def test_multiple_simultaneous_logins(self, test_client):
        """Test multiple simultaneous login requests don't cause issues"""
        import threading
        import time
        
        results = []
        
        def login():
            response = test_client.post(
                "/api/v1/auth/login",
                json={
                    "email": "admin@example.com",
                    "password": "admin123"
                }
            )
            results.append(response.status_code)
        
        # Start multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=login)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=10)  # 10 second timeout
        
        # All logins should succeed
        assert len(results) == 5
        assert all(status == 200 for status in results)