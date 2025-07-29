import pytest
import gzip
import io
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from app.main import app
from app.models.user import User
from app.models.dmarc import DMARCReportSummary

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

@pytest.fixture
def sample_xml_report():
    return """<?xml version="1.0" encoding="UTF-8"?>
<feedback>
    <report_metadata>
        <org_name>example.com</org_name>
        <email>postmaster@example.com</email>
        <report_id>12345</report_id>
        <date_range>
            <begin>1640995200</begin>
            <end>1641081600</end>
        </date_range>
    </report_metadata>
    <policy_published>
        <domain>example.com</domain>
        <adkim>r</adkim>
        <aspf>r</aspf>
        <p>quarantine</p>
        <sp>quarantine</sp>
        <pct>100</pct>
    </policy_published>
    <record>
        <row>
            <source_ip>209.85.128.1</source_ip>
            <count>100</count>
            <policy_evaluated>
                <disposition>none</disposition>
                <dkim>pass</dkim>
                <spf>pass</spf>
            </policy_evaluated>
        </row>
        <identifiers>
            <header_from>example.com</header_from>
        </identifiers>
        <auth_results>
            <dkim>
                <domain>example.com</domain>
                <result>pass</result>
            </dkim>
            <spf>
                <domain>example.com</domain>
                <result>pass</result>
            </spf>
        </auth_results>
    </record>
</feedback>"""

@pytest.fixture
def sample_dmarc_summary():
    return DMARCReportSummary(
        total_emails=1000,
        passed_emails=800,
        failed_emails=200,
        pass_rate=80.0,
        date_range={
            "start": datetime.utcnow() - timedelta(days=7),
            "end": datetime.utcnow()
        },
        top_services=[
            {"service": "Google Workspace", "email_count": 500},
            {"service": "SendGrid", "email_count": 300}
        ]
    )

class TestDMARCReportUpload:
    
    @patch('app.api.auth.get_current_active_user')
    @patch('app.services.dmarc_service.dmarc_service.ingest_report')
    def test_upload_xml_report_success(self, mock_ingest, mock_get_user, mock_user, sample_xml_report, mock_auth_headers):
        """Test successful XML report upload"""
        mock_get_user.return_value = mock_user
        mock_ingest.return_value = "report-id-123"
        
        # Create a file-like object for upload
        file_content = sample_xml_report.encode('utf-8')
        files = {"file": ("test_report.xml", io.BytesIO(file_content), "application/xml")}
        
        response = client.post("/api/v1/dmarc/upload-report", files=files, headers=mock_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "DMARC report uploaded successfully"
        assert data["report_id"] == "report-id-123"
        mock_ingest.assert_called_once_with(sample_xml_report, "test-customer")
    
    @patch('app.api.auth.get_current_active_user')
    @patch('app.services.dmarc_service.dmarc_service.ingest_report')
    def test_upload_gzipped_xml_report_success(self, mock_ingest, mock_get_user, mock_user, sample_xml_report, mock_auth_headers):
        """Test successful gzipped XML report upload"""
        mock_get_user.return_value = mock_user
        mock_ingest.return_value = "report-id-456"
        
        # Create gzipped content
        xml_bytes = sample_xml_report.encode('utf-8')
        gzipped_content = gzip.compress(xml_bytes)
        
        files = {"file": ("test_report.xml.gz", io.BytesIO(gzipped_content), "application/gzip")}
        
        response = client.post("/api/v1/dmarc/upload-report", files=files, headers=mock_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "DMARC report uploaded successfully"
        assert data["report_id"] == "report-id-456"
        mock_ingest.assert_called_once_with(sample_xml_report, "test-customer")
    
    @patch('app.api.auth.get_current_active_user')
    def test_upload_invalid_file_type(self, mock_get_user, mock_user, mock_auth_headers):
        """Test upload with invalid file type"""
        mock_get_user.return_value = mock_user
        
        # Create a non-XML file
        file_content = b"This is not XML content"
        files = {"file": ("test.txt", io.BytesIO(file_content), "text/plain")}
        
        response = client.post("/api/v1/dmarc/upload-report", files=files, headers=mock_auth_headers)
        
        assert response.status_code == 400
        assert "Only XML and XML.GZ files are allowed" in response.json()["detail"]
    
    @patch('app.api.auth.get_current_active_user')
    def test_upload_corrupted_gzip_file(self, mock_get_user, mock_user, mock_auth_headers):
        """Test upload with corrupted gzip file"""
        mock_get_user.return_value = mock_user
        
        # Create corrupted gzip content
        corrupted_gzip = b"corrupted gzip content"
        files = {"file": ("corrupted.xml.gz", io.BytesIO(corrupted_gzip), "application/gzip")}
        
        response = client.post("/api/v1/dmarc/upload-report", files=files, headers=mock_auth_headers)
        
        assert response.status_code == 400
        assert "Failed to decompress gzip file" in response.json()["detail"]
    
    @patch('app.api.auth.get_current_active_user')
    @patch('app.services.dmarc_service.dmarc_service.ingest_report')
    def test_upload_invalid_xml_content(self, mock_ingest, mock_get_user, mock_user, mock_auth_headers):
        """Test upload with invalid XML content"""
        mock_get_user.return_value = mock_user
        mock_ingest.side_effect = ValueError("Invalid XML format")
        
        invalid_xml = "This is not valid XML"
        file_content = invalid_xml.encode('utf-8')
        files = {"file": ("invalid.xml", io.BytesIO(file_content), "application/xml")}
        
        response = client.post("/api/v1/dmarc/upload-report", files=files, headers=mock_auth_headers)
        
        assert response.status_code == 400
        assert "Failed to process report" in response.json()["detail"]
    
    @patch('app.api.auth.get_current_active_user')
    def test_upload_without_file(self, mock_get_user, mock_user, mock_auth_headers):
        """Test upload without providing a file"""
        mock_get_user.return_value = mock_user
        
        response = client.post("/api/v1/dmarc/upload-report", headers=mock_auth_headers)
        
        assert response.status_code == 422  # Validation error
    
    def test_upload_without_authentication(self):
        """Test upload without authentication"""
        file_content = b"test content"
        files = {"file": ("test.xml", io.BytesIO(file_content), "application/xml")}
        
        response = client.post("/api/v1/dmarc/upload-report", files=files)
        
        assert response.status_code == 401

class TestDMARCSummaryEndpoint:
    
    @patch('app.api.auth.get_current_active_user')
    @patch('app.services.dmarc_service.dmarc_service.get_reports_summary')
    def test_get_summary_success(self, mock_get_summary, mock_get_user, mock_user, sample_dmarc_summary, mock_auth_headers):
        """Test successful summary retrieval"""
        mock_get_user.return_value = mock_user
        mock_get_summary.return_value = sample_dmarc_summary
        
        response = client.get("/api/v1/dmarc/summary?days=7", headers=mock_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_emails"] == 1000
        assert data["passed_emails"] == 800
        assert data["pass_rate"] == 80.0
        assert len(data["top_services"]) == 2
    
    @patch('app.api.auth.get_current_active_user')
    @patch('app.services.dmarc_service.dmarc_service.get_reports_summary')
    def test_get_summary_with_domain_filter(self, mock_get_summary, mock_get_user, mock_user, sample_dmarc_summary, mock_auth_headers):
        """Test summary with domain filter"""
        mock_get_user.return_value = mock_user
        mock_get_summary.return_value = sample_dmarc_summary
        
        response = client.get("/api/v1/dmarc/summary?days=30&domain=example.com", headers=mock_auth_headers)
        
        assert response.status_code == 200
        mock_get_summary.assert_called_once_with("test-customer", 30, "example.com")
    
    @patch('app.api.auth.get_current_active_user')
    @patch('app.services.dmarc_service.dmarc_service.get_reports_summary')
    def test_get_summary_invalid_days_parameter(self, mock_get_summary, mock_get_user, mock_user, mock_auth_headers):
        """Test summary with invalid days parameter"""
        mock_get_user.return_value = mock_user
        
        # Test days < 1
        response = client.get("/api/v1/dmarc/summary?days=0", headers=mock_auth_headers)
        assert response.status_code == 422
        
        # Test days > 365
        response = client.get("/api/v1/dmarc/summary?days=400", headers=mock_auth_headers)
        assert response.status_code == 422
    
    @patch('app.api.auth.get_current_active_user')
    @patch('app.services.dmarc_service.dmarc_service.get_reports_summary')
    def test_get_summary_service_error(self, mock_get_summary, mock_get_user, mock_user, mock_auth_headers):
        """Test summary with service error"""
        mock_get_user.return_value = mock_user
        mock_get_summary.side_effect = Exception("Database connection failed")
        
        response = client.get("/api/v1/dmarc/summary?days=7", headers=mock_auth_headers)
        
        assert response.status_code == 500
        assert "Failed to get summary" in response.json()["detail"]
    
    @patch('app.api.auth.get_current_active_user')
    @patch('app.services.dmarc_service.dmarc_service.get_reports_summary')
    def test_get_summary_default_parameters(self, mock_get_summary, mock_get_user, mock_user, sample_dmarc_summary, mock_auth_headers):
        """Test summary with default parameters"""
        mock_get_user.return_value = mock_user
        mock_get_summary.return_value = sample_dmarc_summary
        
        response = client.get("/api/v1/dmarc/summary", headers=mock_auth_headers)
        
        assert response.status_code == 200
        mock_get_summary.assert_called_once_with("test-customer", 7, None)

class TestDMARCReportsEndpoint:
    
    @patch('app.api.auth.get_current_active_user')
    @patch('app.services.dmarc_service.dmarc_service.get_reports_by_customer')
    def test_get_reports_success(self, mock_get_reports, mock_get_user, mock_user, mock_auth_headers):
        """Test successful reports retrieval"""
        mock_get_user.return_value = mock_user
        sample_reports = [
            {
                "id": "report-1",
                "policy": {"domain": "example.com"},
                "metadata": {"report_id": "12345", "org_name": "Google"}
            },
            {
                "id": "report-2", 
                "policy": {"domain": "test.com"},
                "metadata": {"report_id": "67890", "org_name": "Microsoft"}
            }
        ]
        mock_get_reports.return_value = sample_reports
        
        response = client.get("/api/v1/dmarc/reports?limit=100", headers=mock_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["id"] == "report-1"
        mock_get_reports.assert_called_once_with("test-customer", 100, None)
    
    @patch('app.api.auth.get_current_active_user')
    @patch('app.services.dmarc_service.dmarc_service.get_reports_by_customer')
    def test_get_reports_with_domain_filter(self, mock_get_reports, mock_get_user, mock_user, mock_auth_headers):
        """Test reports retrieval with domain filter"""
        mock_get_user.return_value = mock_user
        filtered_reports = [
            {
                "id": "report-1",
                "policy": {"domain": "example.com"},
                "metadata": {"report_id": "12345"}
            }
        ]
        mock_get_reports.return_value = filtered_reports
        
        response = client.get("/api/v1/dmarc/reports?limit=50&domain=example.com", headers=mock_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["policy"]["domain"] == "example.com"
        mock_get_reports.assert_called_once_with("test-customer", 50, "example.com")
    
    @patch('app.api.auth.get_current_active_user')
    @patch('app.services.dmarc_service.dmarc_service.get_reports_by_customer')
    def test_get_reports_invalid_limit_parameter(self, mock_get_reports, mock_get_user, mock_user, mock_auth_headers):
        """Test reports with invalid limit parameter"""
        mock_get_user.return_value = mock_user
        
        # Test limit < 1
        response = client.get("/api/v1/dmarc/reports?limit=0", headers=mock_auth_headers)
        assert response.status_code == 422
        
        # Test limit > 1000
        response = client.get("/api/v1/dmarc/reports?limit=1500", headers=mock_auth_headers)
        assert response.status_code == 422
    
    @patch('app.api.auth.get_current_active_user')
    @patch('app.services.dmarc_service.dmarc_service.get_reports_by_customer')
    def test_get_reports_empty_result(self, mock_get_reports, mock_get_user, mock_user, mock_auth_headers):
        """Test reports retrieval with empty result"""
        mock_get_user.return_value = mock_user
        mock_get_reports.return_value = []
        
        response = client.get("/api/v1/dmarc/reports", headers=mock_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

class TestDMARCTimeSeriesEndpoint:
    
    @patch('app.api.auth.get_current_active_user')
    @patch('app.services.dmarc_service.dmarc_service.get_time_series_data')
    def test_get_time_series_success(self, mock_get_time_series, mock_get_user, mock_user, mock_auth_headers):
        """Test successful time series data retrieval"""
        mock_get_user.return_value = mock_user
        sample_time_series = [
            {
                "date": "2024-01-15",
                "total_emails": 100,
                "passed_emails": 80,
                "failed_emails": 20,
                "pass_rate": 80.0
            },
            {
                "date": "2024-01-16",
                "total_emails": 150,
                "passed_emails": 120,
                "failed_emails": 30,
                "pass_rate": 80.0
            }
        ]
        mock_get_time_series.return_value = sample_time_series
        
        response = client.get("/api/v1/dmarc/time-series?days=30", headers=mock_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["date"] == "2024-01-15"
        assert data[0]["pass_rate"] == 80.0
        mock_get_time_series.assert_called_once_with("test-customer", 30, None)
    
    @patch('app.api.auth.get_current_active_user')
    @patch('app.services.dmarc_service.dmarc_service.get_time_series_data')
    def test_get_time_series_with_domain_filter(self, mock_get_time_series, mock_get_user, mock_user, mock_auth_headers):
        """Test time series with domain filter"""
        mock_get_user.return_value = mock_user
        mock_get_time_series.return_value = []
        
        response = client.get("/api/v1/dmarc/time-series?days=60&domain=example.com", headers=mock_auth_headers)
        
        assert response.status_code == 200
        mock_get_time_series.assert_called_once_with("test-customer", 60, "example.com")
    
    @patch('app.api.auth.get_current_active_user')
    @patch('app.services.dmarc_service.dmarc_service.get_time_series_data')
    def test_get_time_series_invalid_days_parameter(self, mock_get_time_series, mock_get_user, mock_user, mock_auth_headers):
        """Test time series with invalid days parameter"""
        mock_get_user.return_value = mock_user
        
        # Test days < 1
        response = client.get("/api/v1/dmarc/time-series?days=0", headers=mock_auth_headers)
        assert response.status_code == 422
        
        # Test days > 365
        response = client.get("/api/v1/dmarc/time-series?days=400", headers=mock_auth_headers)
        assert response.status_code == 422
    
    @patch('app.api.auth.get_current_active_user')
    @patch('app.services.dmarc_service.dmarc_service.get_time_series_data')
    def test_get_time_series_service_error(self, mock_get_time_series, mock_get_user, mock_user, mock_auth_headers):
        """Test time series with service error"""
        mock_get_user.return_value = mock_user
        mock_get_time_series.side_effect = Exception("Elasticsearch query failed")
        
        response = client.get("/api/v1/dmarc/time-series?days=30", headers=mock_auth_headers)
        
        assert response.status_code == 500
        assert "Failed to get time series data" in response.json()["detail"]

class TestDMARCHealthEndpoint:
    
    def test_health_check(self):
        """Test DMARC API health check endpoint"""
        response = client.get("/api/v1/dmarc/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "dmarc-api"

class TestEdgeCasesAndErrorHandling:
    
    @patch('app.api.auth.get_current_active_user')
    @patch('app.services.dmarc_service.dmarc_service.ingest_report')
    def test_upload_extremely_large_file(self, mock_ingest, mock_get_user, mock_user, mock_auth_headers):
        """Test upload with extremely large file"""
        mock_get_user.return_value = mock_user
        mock_ingest.side_effect = MemoryError("File too large")
        
        # Create a large XML content (simulated)
        large_xml = "<feedback>" + "x" * 10000 + "</feedback>"
        file_content = large_xml.encode('utf-8')
        files = {"file": ("large.xml", io.BytesIO(file_content), "application/xml")}
        
        response = client.post("/api/v1/dmarc/upload-report", files=files, headers=mock_auth_headers)
        
        assert response.status_code == 400
        assert "Failed to process report" in response.json()["detail"]
    
    @patch('app.api.auth.get_current_active_user')
    @patch('app.services.dmarc_service.dmarc_service.get_reports_summary')
    def test_get_summary_with_special_characters_in_domain(self, mock_get_summary, mock_get_user, mock_user, sample_dmarc_summary, mock_auth_headers):
        """Test summary with special characters in domain"""
        mock_get_user.return_value = mock_user
        mock_get_summary.return_value = sample_dmarc_summary
        
        special_domains = [
            "xn--fsq.xn--0zwm56d",  # IDN domain
            "sub-domain.example.com",
            "domain_with_underscore.com",
            "123.example.com"
        ]
        
        for domain in special_domains:
            response = client.get(f"/api/v1/dmarc/summary?domain={domain}", headers=mock_auth_headers)
            assert response.status_code == 200
    
    @patch('app.api.auth.get_current_active_user')
    def test_endpoints_with_non_ascii_filenames(self, mock_get_user, mock_user, mock_auth_headers):
        """Test file upload with non-ASCII filenames"""
        mock_get_user.return_value = mock_user
        
        # Test with non-ASCII filename
        file_content = b"<feedback></feedback>"
        files = {"file": ("报告.xml", io.BytesIO(file_content), "application/xml")}
        
        with patch('app.services.dmarc_service.dmarc_service.ingest_report') as mock_ingest:
            mock_ingest.return_value = "report-id"
            response = client.post("/api/v1/dmarc/upload-report", files=files, headers=mock_auth_headers)
            
            # Should handle non-ASCII filenames gracefully
            assert response.status_code in [200, 400]
    
    @patch('app.api.auth.get_current_active_user')
    @patch('app.services.dmarc_service.dmarc_service.get_reports_summary')
    def test_concurrent_requests_handling(self, mock_get_summary, mock_get_user, mock_user, sample_dmarc_summary, mock_auth_headers):
        """Test handling of concurrent requests"""
        mock_get_user.return_value = mock_user
        mock_get_summary.return_value = sample_dmarc_summary
        
        # Simulate multiple concurrent requests
        import threading
        results = []
        
        def make_request():
            response = client.get("/api/v1/dmarc/summary", headers=mock_auth_headers)
            results.append(response.status_code)
        
        threads = [threading.Thread(target=make_request) for _ in range(5)]
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # All requests should succeed
        assert all(status == 200 for status in results)
        assert len(results) == 5
    
    @patch('app.api.auth.get_current_active_user')
    def test_malformed_gzip_headers(self, mock_get_user, mock_user, mock_auth_headers):
        """Test handling of files with gzip extension but not gzipped content"""
        mock_get_user.return_value = mock_user
        
        # Create non-gzipped content with .gz extension
        file_content = b"This is not gzipped content"
        files = {"file": ("fake.xml.gz", io.BytesIO(file_content), "application/gzip")}
        
        response = client.post("/api/v1/dmarc/upload-report", files=files, headers=mock_auth_headers)
        
        assert response.status_code == 400
        assert "Failed to decompress gzip file" in response.json()["detail"]