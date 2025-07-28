"""
Tests for DMARC file upload API endpoints
"""
import pytest
import io
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient

class TestDMARCUploadAPI:
    """Test file upload functionality and gzip support"""
    
    def test_upload_xml_file_success(self, test_client, authenticated_headers, sample_dmarc_xml):
        """Test successful XML file upload"""
        with patch('backend.app.api.dmarc.dmarc_service') as mock_service:
            mock_service.ingest_report.return_value = "test-report-id"
            
            # Create file-like object
            xml_file = io.BytesIO(sample_dmarc_xml.encode('utf-8'))
            
            response = test_client.post(
                "/api/v1/dmarc/upload-report",
                headers=authenticated_headers,
                files={"file": ("test_report.xml", xml_file, "application/xml")}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "DMARC report uploaded successfully"
        assert data["report_id"] == "test-report-id"
    
    def test_upload_gzip_file_success(self, test_client, authenticated_headers, sample_dmarc_xml_gzipped):
        """Test successful gzipped XML file upload - REGRESSION TEST for gzip support"""
        with patch('backend.app.api.dmarc.dmarc_service') as mock_service:
            mock_service.ingest_report.return_value = "test-gzip-report-id"
            
            # Create gzipped file-like object
            gzip_file = io.BytesIO(sample_dmarc_xml_gzipped)
            
            response = test_client.post(
                "/api/v1/dmarc/upload-report",
                headers=authenticated_headers,
                files={"file": ("test_report.xml.gz", gzip_file, "application/gzip")}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "DMARC report uploaded successfully"
        assert data["report_id"] == "test-gzip-report-id"
    
    def test_upload_invalid_file_type(self, test_client, authenticated_headers):
        """Test upload with invalid file type"""
        text_file = io.BytesIO(b"This is not XML")
        
        response = test_client.post(
            "/api/v1/dmarc/upload-report",
            headers=authenticated_headers,
            files={"file": ("test.txt", text_file, "text/plain")}
        )
        
        assert response.status_code == 400
        assert "Only XML and XML.GZ files are allowed" in response.json()["detail"]
    
    def test_upload_corrupted_gzip(self, test_client, authenticated_headers):
        """Test upload with corrupted gzip file"""
        # Create invalid gzip data
        invalid_gzip = io.BytesIO(b"not gzip data")
        
        response = test_client.post(
            "/api/v1/dmarc/upload-report",
            headers=authenticated_headers,
            files={"file": ("corrupted.xml.gz", invalid_gzip, "application/gzip")}
        )
        
        assert response.status_code == 400
        assert "Failed to decompress gzip file" in response.json()["detail"]
    
    def test_upload_without_authentication(self, test_client, sample_dmarc_xml):
        """Test upload without authentication token"""
        xml_file = io.BytesIO(sample_dmarc_xml.encode('utf-8'))
        
        response = test_client.post(
            "/api/v1/dmarc/upload-report",
            files={"file": ("test_report.xml", xml_file, "application/xml")}
        )
        
        assert response.status_code == 403
        assert response.json()["detail"] == "Not authenticated"
    
    def test_upload_processing_error(self, test_client, authenticated_headers, sample_dmarc_xml):
        """Test upload when processing fails"""
        with patch('backend.app.api.dmarc.dmarc_service') as mock_service:
            mock_service.ingest_report.side_effect = ValueError("Processing failed")
            
            xml_file = io.BytesIO(sample_dmarc_xml.encode('utf-8'))
            
            response = test_client.post(
                "/api/v1/dmarc/upload-report",
                headers=authenticated_headers,
                files={"file": ("test_report.xml", xml_file, "application/xml")}
            )
        
        assert response.status_code == 400
        assert "Failed to process report" in response.json()["detail"]
    
    def test_upload_empty_file(self, test_client, authenticated_headers):
        """Test upload with empty file"""
        empty_file = io.BytesIO(b"")
        
        response = test_client.post(
            "/api/v1/dmarc/upload-report",
            headers=authenticated_headers,
            files={"file": ("empty.xml", empty_file, "application/xml")}
        )
        
        assert response.status_code == 400
        assert "Failed to process report" in response.json()["detail"]
    
    def test_upload_large_file(self, test_client, authenticated_headers):
        """Test upload with reasonably large file"""
        # Create a larger XML file (simulate real DMARC report)
        large_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <feedback>
            <report_metadata>
                <org_name>Large Report Test</org_name>
                <email>large@example.com</email>
                <report_id>large_test_789</report_id>
                <date_range>
                    <begin>1640995200</begin>
                    <end>1641081600</end>
                </date_range>
            </report_metadata>
            <policy_published>
                <domain>example.com</domain>
                <p>none</p>
            </policy_published>"""
        
        # Add many records to make it larger
        for i in range(100):
            large_xml += f"""
            <record>
                <row>
                    <source_ip>192.168.1.{i % 255}</source_ip>
                    <count>{i + 1}</count>
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
                    <spf><result>pass</result></spf>
                    <dkim><result>pass</result></dkim>
                </auth_results>
            </record>"""
        
        large_xml += "</feedback>"
        
        with patch('backend.app.api.dmarc.dmarc_service') as mock_service:
            mock_service.ingest_report.return_value = "large-report-id"
            
            large_file = io.BytesIO(large_xml.encode('utf-8'))
            
            response = test_client.post(
                "/api/v1/dmarc/upload-report",
                headers=authenticated_headers,
                files={"file": ("large_report.xml", large_file, "application/xml")}
            )
        
        assert response.status_code == 200
        assert response.json()["report_id"] == "large-report-id"