import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from app.main import app
from app.models.user import User
from app.models.dmarc import DMARCReportSummary
from app.services.dmarc_service import dmarc_service

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
def mock_auth_headers():
    return {"Authorization": "Bearer valid-token"}

class TestDomainFilteringAPI:
    
    @patch('app.api.auth.get_current_active_user')
    @patch('app.services.dmarc_service.dmarc_service.get_reports_summary')
    def test_summary_with_valid_domain_filter(self, mock_get_summary, mock_get_user, mock_user, mock_auth_headers):
        """Test DMARC summary endpoint with valid domain filter"""
        mock_get_user.return_value = mock_user
        
        expected_summary = DMARCReportSummary(
            total_emails=1000,
            passed_emails=800,
            failed_emails=200,
            pass_rate=80.0,
            date_range={
                "start": datetime.utcnow() - timedelta(days=7),
                "end": datetime.utcnow()
            },
            top_services=[{"service": "Google Workspace", "email_count": 500}]
        )
        mock_get_summary.return_value = expected_summary
        
        response = client.get(
            "/api/v1/dmarc/summary?days=7&domain=example.com",
            headers=mock_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_emails"] == 1000
        assert data["pass_rate"] == 80.0
        
        # Verify domain filter was passed to service
        mock_get_summary.assert_called_once_with("test-customer", 7, "example.com")
    
    @patch('app.api.auth.get_current_active_user')
    @patch('app.services.dmarc_service.dmarc_service.get_reports_summary')
    def test_summary_without_domain_filter(self, mock_get_summary, mock_get_user, mock_user, mock_auth_headers):
        """Test DMARC summary endpoint without domain filter"""
        mock_get_user.return_value = mock_user
        
        expected_summary = DMARCReportSummary(
            total_emails=2000,
            passed_emails=1600,
            failed_emails=400,
            pass_rate=80.0,
            date_range={
                "start": datetime.utcnow() - timedelta(days=7),
                "end": datetime.utcnow()
            },
            top_services=[{"service": "Google Workspace", "email_count": 1000}]
        )
        mock_get_summary.return_value = expected_summary
        
        response = client.get(
            "/api/v1/dmarc/summary?days=7",
            headers=mock_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_emails"] == 2000
        
        # Verify no domain filter was passed to service
        mock_get_summary.assert_called_once_with("test-customer", 7, None)
    
    @patch('app.api.auth.get_current_active_user')
    @patch('app.services.dmarc_service.dmarc_service.get_reports_by_customer')
    def test_reports_with_domain_filter(self, mock_get_reports, mock_get_user, mock_user, mock_auth_headers):
        """Test DMARC reports endpoint with domain filter"""
        mock_get_user.return_value = mock_user
        
        expected_reports = [
            {
                "id": "report-1",
                "policy": {"domain": "example.com"},
                "metadata": {"report_id": "12345"}
            }
        ]
        mock_get_reports.return_value = expected_reports
        
        response = client.get(
            "/api/v1/dmarc/reports?limit=100&domain=example.com",
            headers=mock_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["policy"]["domain"] == "example.com"
        
        # Verify domain filter was passed to service
        mock_get_reports.assert_called_once_with("test-customer", 100, "example.com")
    
    @patch('app.api.auth.get_current_active_user')
    @patch('app.services.dmarc_service.dmarc_service.get_time_series_data')
    def test_time_series_with_domain_filter(self, mock_get_time_series, mock_get_user, mock_user, mock_auth_headers):
        """Test DMARC time series endpoint with domain filter"""
        mock_get_user.return_value = mock_user
        
        expected_data = [
            {
                "date": "2024-01-15",
                "total_emails": 100,
                "passed_emails": 80,
                "failed_emails": 20,
                "pass_rate": 80.0
            }
        ]
        mock_get_time_series.return_value = expected_data
        
        response = client.get(
            "/api/v1/dmarc/time-series?days=30&domain=example.com",
            headers=mock_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["pass_rate"] == 80.0
        
        # Verify domain filter was passed to service
        mock_get_time_series.assert_called_once_with("test-customer", 30, "example.com")
    
    @patch('app.api.auth.get_current_active_user')
    @patch('app.services.dmarc_service.dmarc_service.get_reports_summary')
    def test_summary_with_empty_domain_filter(self, mock_get_summary, mock_get_user, mock_user, mock_auth_headers):
        """Test DMARC summary endpoint with empty domain filter"""
        mock_get_user.return_value = mock_user
        
        expected_summary = DMARCReportSummary(
            total_emails=500,
            passed_emails=400,
            failed_emails=100,
            pass_rate=80.0,
            date_range={
                "start": datetime.utcnow() - timedelta(days=7),
                "end": datetime.utcnow()
            },
            top_services=[{"service": "SendGrid", "email_count": 300}]
        )
        mock_get_summary.return_value = expected_summary
        
        response = client.get(
            "/api/v1/dmarc/summary?days=7&domain=",
            headers=mock_auth_headers
        )
        
        assert response.status_code == 200
        
        # Verify empty domain filter is treated as None
        mock_get_summary.assert_called_once_with("test-customer", 7, "")
    
    @patch('app.api.auth.get_current_active_user')
    @patch('app.services.dmarc_service.dmarc_service.get_reports_summary')
    def test_summary_with_invalid_domain_format(self, mock_get_summary, mock_get_user, mock_user, mock_auth_headers):
        """Test DMARC summary endpoint with invalid domain format"""
        mock_get_user.return_value = mock_user
        
        # Service should handle invalid domain gracefully and return empty results
        expected_summary = DMARCReportSummary(
            total_emails=0,
            passed_emails=0,
            failed_emails=0,
            pass_rate=0.0,
            date_range={
                "start": datetime.utcnow() - timedelta(days=7),
                "end": datetime.utcnow()
            },
            top_services=[]
        )
        mock_get_summary.return_value = expected_summary
        
        response = client.get(
            "/api/v1/dmarc/summary?days=7&domain=invalid..domain..format",
            headers=mock_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_emails"] == 0
        
        # Verify invalid domain was passed to service
        mock_get_summary.assert_called_once_with("test-customer", 7, "invalid..domain..format")

class TestDomainFilteringService:
    
    @patch('app.services.elasticsearch.es_service.search_documents')
    def test_get_reports_summary_with_domain_filter(self, mock_search):
        """Test DMARCService get_reports_summary with domain filter"""
        mock_search.return_value = {
            "aggregations": {
                "records": {
                    "total_emails": {"value": 500},
                    "passed_emails": {"count": {"value": 400}},
                    "services": {
                        "buckets": [
                            {"key": "Google Workspace", "email_count": {"value": 300}}
                        ]
                    }
                }
            }
        }
        
        result = dmarc_service.get_reports_summary("test-customer", 7, "example.com")
        
        assert result.total_emails == 500
        assert result.passed_emails == 400
        assert result.failed_emails == 100
        assert result.pass_rate == 80.0
        
        # Verify Elasticsearch query included domain filter
        called_query = mock_search.call_args[0][1]
        must_conditions = called_query["query"]["bool"]["must"]
        
        # Check that domain filter is included
        domain_filter = next((cond for cond in must_conditions if "policy.domain" in str(cond)), None)
        assert domain_filter is not None
        assert domain_filter["term"]["policy.domain"] == "example.com"
    
    @patch('app.services.elasticsearch.es_service.search_documents')
    def test_get_reports_summary_without_domain_filter(self, mock_search):
        """Test DMARCService get_reports_summary without domain filter"""
        mock_search.return_value = {
            "aggregations": {
                "records": {
                    "total_emails": {"value": 1000},
                    "passed_emails": {"count": {"value": 800}},
                    "services": {
                        "buckets": [
                            {"key": "SendGrid", "email_count": {"value": 600}}
                        ]
                    }
                }
            }
        }
        
        result = dmarc_service.get_reports_summary("test-customer", 7, None)
        
        assert result.total_emails == 1000
        assert result.passed_emails == 800
        
        # Verify Elasticsearch query does not include domain filter
        called_query = mock_search.call_args[0][1]
        must_conditions = called_query["query"]["bool"]["must"]
        
        # Check that domain filter is not included
        domain_filter = next((cond for cond in must_conditions if "policy.domain" in str(cond)), None)
        assert domain_filter is None
    
    @patch('app.services.elasticsearch.es_service.search_documents')
    def test_get_reports_by_customer_with_domain_filter(self, mock_search):
        """Test DMARCService get_reports_by_customer with domain filter"""
        mock_search.return_value = {
            "hits": {
                "hits": [
                    {
                        "_id": "report-1",
                        "_source": {
                            "policy": {"domain": "example.com"},
                            "customer_id": "test-customer"
                        }
                    }
                ]
            }
        }
        
        result = dmarc_service.get_reports_by_customer("test-customer", 100, "example.com")
        
        assert len(result) == 1
        assert result[0]["policy"]["domain"] == "example.com"
        
        # Verify Elasticsearch query included domain filter
        called_query = mock_search.call_args[0][1]
        must_conditions = called_query["query"]["bool"]["must"]
        
        # Check that domain filter is included
        domain_filter = next((cond for cond in must_conditions if "policy.domain" in str(cond)), None)
        assert domain_filter is not None
        assert domain_filter["term"]["policy.domain"] == "example.com"
    
    @patch('app.services.elasticsearch.es_service.search_documents')
    def test_get_time_series_data_with_domain_filter(self, mock_search):
        """Test DMARCService get_time_series_data with domain filter"""
        mock_search.return_value = {
            "aggregations": {
                "daily_stats": {
                    "buckets": [
                        {
                            "key_as_string": "2024-01-15",
                            "records": {
                                "total_emails": {"value": 100},
                                "passed_emails": {"count": {"value": 80}}
                            }
                        }
                    ]
                }
            }
        }
        
        result = dmarc_service.get_time_series_data("test-customer", 30, "example.com")
        
        assert len(result) == 1
        assert result[0]["date"] == "2024-01-15"
        assert result[0]["total_emails"] == 100
        assert result[0]["passed_emails"] == 80
        assert result[0]["pass_rate"] == 80.0
        
        # Verify Elasticsearch query included domain filter
        called_query = mock_search.call_args[0][1]
        must_conditions = called_query["query"]["bool"]["must"]
        
        # Check that domain filter is included
        domain_filter = next((cond for cond in must_conditions if "policy.domain" in str(cond)), None)
        assert domain_filter is not None
        assert domain_filter["term"]["policy.domain"] == "example.com"

class TestEdgeCases:
    
    @patch('app.api.auth.get_current_active_user')
    @patch('app.services.dmarc_service.dmarc_service.get_reports_summary')
    def test_domain_filter_with_special_characters(self, mock_get_summary, mock_get_user, mock_user, mock_auth_headers):
        """Test domain filter with special characters"""
        mock_get_user.return_value = mock_user
        
        expected_summary = DMARCReportSummary(
            total_emails=0,
            passed_emails=0,
            failed_emails=0,
            pass_rate=0.0,
            date_range={
                "start": datetime.utcnow() - timedelta(days=7),
                "end": datetime.utcnow()
            },
            top_services=[]
        )
        mock_get_summary.return_value = expected_summary
        
        # Test with various special characters
        special_domains = [
            "domain-with-dash.com",
            "domain_with_underscore.com",
            "sub.domain.example.com",
            "xn--fsq.xn--0zwm56d"  # IDN domain
        ]
        
        for domain in special_domains:
            response = client.get(
                f"/api/v1/dmarc/summary?days=7&domain={domain}",
                headers=mock_auth_headers
            )
            
            assert response.status_code == 200
    
    @patch('app.api.auth.get_current_active_user')
    @patch('app.services.dmarc_service.dmarc_service.get_reports_summary')
    def test_domain_filter_case_sensitivity(self, mock_get_summary, mock_get_user, mock_user, mock_auth_headers):
        """Test domain filter case sensitivity"""
        mock_get_user.return_value = mock_user
        
        expected_summary = DMARCReportSummary(
            total_emails=100,
            passed_emails=80,
            failed_emails=20,
            pass_rate=80.0,
            date_range={
                "start": datetime.utcnow() - timedelta(days=7),
                "end": datetime.utcnow()
            },
            top_services=[]
        )
        mock_get_summary.return_value = expected_summary
        
        # Test with different cases
        test_cases = ["EXAMPLE.COM", "example.com", "Example.Com"]
        
        for domain in test_cases:
            response = client.get(
                f"/api/v1/dmarc/summary?days=7&domain={domain}",
                headers=mock_auth_headers
            )
            
            assert response.status_code == 200
            # Verify the exact domain case was passed to service
            mock_get_summary.assert_called_with("test-customer", 7, domain)
            mock_get_summary.reset_mock()