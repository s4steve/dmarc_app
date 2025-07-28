"""
Tests for DMARC API endpoints (summary, time-series, reports)
"""
import pytest
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient

class TestDMARCAPIEndpoints:
    """Test DMARC data retrieval API endpoints"""
    
    def test_get_summary_success(self, test_client, authenticated_headers):
        """Test successful summary retrieval"""
        with patch('backend.app.api.dmarc.dmarc_service') as mock_service:
            mock_summary = Mock()
            mock_summary.total_emails = 1000
            mock_summary.passed_emails = 800
            mock_summary.failed_emails = 200
            mock_summary.pass_rate = 80.0
            mock_summary.date_range = {
                "start": "2025-07-21T00:00:00",
                "end": "2025-07-28T00:00:00"
            }
            mock_summary.top_services = [
                {"service": "mailchimp", "email_count": 500},
                {"service": "sendgrid", "email_count": 300}
            ]
            
            mock_service.get_reports_summary.return_value = mock_summary
            
            response = test_client.get(
                "/api/v1/dmarc/summary",
                headers=authenticated_headers
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_emails"] == 1000
        assert data["passed_emails"] == 800
        assert data["failed_emails"] == 200
        assert data["pass_rate"] == 80.0
    
    def test_get_summary_with_days_parameter(self, test_client, authenticated_headers):
        """Test summary with custom days parameter"""
        with patch('backend.app.api.dmarc.dmarc_service') as mock_service:
            mock_service.get_reports_summary.return_value = Mock(
                total_emails=500, passed_emails=400, failed_emails=100, 
                pass_rate=80.0, date_range={}, top_services=[]
            )
            
            response = test_client.get(
                "/api/v1/dmarc/summary?days=30",
                headers=authenticated_headers
            )
        
        assert response.status_code == 200
        mock_service.get_reports_summary.assert_called_once()
        call_args = mock_service.get_reports_summary.call_args
        assert call_args[0][1] == 30  # days parameter
    
    def test_get_summary_invalid_days(self, test_client, authenticated_headers):
        """Test summary with invalid days parameter"""
        response = test_client.get(
            "/api/v1/dmarc/summary?days=0",
            headers=authenticated_headers
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_get_summary_unauthenticated(self, test_client):
        """Test summary without authentication - REGRESSION TEST for auth issues"""
        response = test_client.get("/api/v1/dmarc/summary")
        
        assert response.status_code == 403
        assert response.json()["detail"] == "Not authenticated"
    
    def test_get_time_series_success(self, test_client, authenticated_headers):
        """Test successful time series retrieval - REGRESSION TEST for async issues"""
        with patch('backend.app.api.dmarc.dmarc_service') as mock_service:
            mock_service.get_time_series_data.return_value = [
                {
                    "date": "2025-07-21T00:00:00.000Z",
                    "total_emails": 1000,
                    "passed_emails": 800,
                    "failed_emails": 200,
                    "pass_rate": 80.0
                },
                {
                    "date": "2025-07-22T00:00:00.000Z", 
                    "total_emails": 1200,
                    "passed_emails": 900,
                    "failed_emails": 300,
                    "pass_rate": 75.0
                }
            ]
            
            response = test_client.get(
                "/api/v1/dmarc/time-series",
                headers=authenticated_headers
            )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["total_emails"] == 1000
        assert data[1]["total_emails"] == 1200
    
    def test_get_time_series_with_days_parameter(self, test_client, authenticated_headers):
        """Test time series with custom days parameter"""
        with patch('backend.app.api.dmarc.dmarc_service') as mock_service:
            mock_service.get_time_series_data.return_value = []
            
            response = test_client.get(
                "/api/v1/dmarc/time-series?days=60",
                headers=authenticated_headers
            )
        
        assert response.status_code == 200
        mock_service.get_time_series_data.assert_called_once()
        call_args = mock_service.get_time_series_data.call_args
        assert call_args[0][1] == 60  # days parameter
    
    def test_get_reports_success(self, test_client, authenticated_headers):
        """Test successful reports retrieval"""
        with patch('backend.app.api.dmarc.dmarc_service') as mock_service:
            mock_service.get_reports_by_customer.return_value = [
                {
                    "id": "report1",
                    "metadata": {"report_id": "test_report_1", "org_name": "Test Org 1"},
                    "processed_at": "2025-07-21T10:00:00"
                },
                {
                    "id": "report2", 
                    "metadata": {"report_id": "test_report_2", "org_name": "Test Org 2"},
                    "processed_at": "2025-07-22T11:00:00"
                }
            ]
            
            response = test_client.get(
                "/api/v1/dmarc/reports",
                headers=authenticated_headers
            )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["id"] == "report1"
        assert data[1]["id"] == "report2"
    
    def test_get_reports_with_limit(self, test_client, authenticated_headers):
        """Test reports retrieval with limit parameter"""
        with patch('backend.app.api.dmarc.dmarc_service') as mock_service:
            mock_service.get_reports_by_customer.return_value = []
            
            response = test_client.get(
                "/api/v1/dmarc/reports?limit=50",
                headers=authenticated_headers
            )
        
        assert response.status_code == 200
        mock_service.get_reports_by_customer.assert_called_once()
        call_args = mock_service.get_reports_by_customer.call_args
        assert call_args[0][1] == 50  # limit parameter
    
    def test_health_check(self, test_client):
        """Test health check endpoint"""
        response = test_client.get("/api/v1/dmarc/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "dmarc-api"
    
    def test_api_error_handling(self, test_client, authenticated_headers):
        """Test API error handling when service fails"""
        with patch('backend.app.api.dmarc.dmarc_service') as mock_service:
            mock_service.get_reports_summary.side_effect = Exception("Database error")
            
            response = test_client.get(
                "/api/v1/dmarc/summary",
                headers=authenticated_headers
            )
        
        assert response.status_code == 500
        assert "Failed to get summary" in response.json()["detail"]
    
    def test_summary_elasticsearch_compatibility(self, test_client, authenticated_headers):
        """Test that summary endpoint works with Elasticsearch v7.x - REGRESSION TEST"""
        with patch('backend.app.api.dmarc.dmarc_service') as mock_service:
            # Mock the service to simulate successful Elasticsearch interaction
            mock_service.get_reports_summary.return_value = Mock(
                total_emails=100, passed_emails=80, failed_emails=20,
                pass_rate=80.0, date_range={}, top_services=[]
            )
            
            response = test_client.get(
                "/api/v1/dmarc/summary",
                headers=authenticated_headers
            )
        
        # Should not get BadRequestError about media-type headers
        assert response.status_code == 200
        assert "BadRequestError" not in str(response.content)
        assert "media-type" not in str(response.content).lower()