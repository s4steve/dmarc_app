"""
Regression tests for bugs encountered during development
"""
import pytest
import gzip
import io
from unittest.mock import Mock, patch
from backend.app.services.dmarc_parser import DMARCParser
from backend.app.services.dmarc_service import DMARCService

class TestRegressionBugs:
    """Test fixes for specific bugs encountered during development"""
    
    def test_async_sync_mismatch_fix(self):
        """REGRESSION TEST: Ensure async/sync mismatch is fixed in Elasticsearch service"""
        # This was causing "object dict can't be used in 'await' expression" errors
        
        service = DMARCService()
        
        # Mock Elasticsearch to return sample data
        with patch('backend.app.services.dmarc_service.es_service') as mock_es:
            mock_es.search_documents.return_value = {
                "aggregations": {
                    "daily_stats": {
                        "buckets": [
                            {
                                "key_as_string": "2025-07-21T00:00:00.000Z",
                                "records": {
                                    "total_emails": {"value": 100},
                                    "passed_emails": {"count": {"value": 80}}
                                }
                            }
                        ]
                    }
                }
            }
            
            # This should not raise an async/await error
            result = service.get_time_series_data("test_customer", 7)
            
            assert len(result) == 1
            assert result[0]["total_emails"] == 100
            
            # Verify that the method was called synchronously (not with await)
            assert mock_es.search_documents.called
    
    def test_gzip_file_support_fix(self):
        """REGRESSION TEST: Ensure gzip file upload support works"""
        # Originally only XML files were supported, causing user upload failures
        
        from fastapi.testclient import TestClient
        from backend.app.main import app
        
        client = TestClient(app)
        
        # Create gzipped content
        xml_content = """<?xml version="1.0"?>
        <feedback>
            <report_metadata>
                <org_name>Test</org_name>
                <email>test@example.com</email>
                <report_id>test</report_id>
                <date_range><begin>1640995200</begin><end>1641081600</end></date_range>
            </report_metadata>
            <policy_published><domain>example.com</domain><p>none</p></policy_published>
        </feedback>"""
        
        gzipped_content = gzip.compress(xml_content.encode('utf-8'))
        
        # Mock the service
        with patch('backend.app.api.dmarc.dmarc_service') as mock_service:
            mock_service.ingest_report.return_value = "test-id"
            
            # Get auth token
            login_response = client.post("/api/v1/auth/login", json={
                "email": "admin@example.com", 
                "password": "admin123"
            })
            token = login_response.json()["access_token"]
            
            # Upload gzipped file
            response = client.post(
                "/api/v1/dmarc/upload-report",
                headers={"Authorization": f"Bearer {token}"},
                files={"file": ("report.xml.gz", io.BytesIO(gzipped_content), "application/gzip")}
            )
            
            # Should succeed
            assert response.status_code == 200
            assert "successfully" in response.json()["message"]
    
    def test_dmarc_result_logic_fix(self):
        """REGRESSION TEST: Ensure DMARC pass/fail logic is correct"""
        # Originally used policy disposition instead of SPF/DKIM results
        
        parser = DMARCParser()
        
        # Test the corrected logic
        assert parser._determine_dmarc_result("pass", "pass") == "pass"
        assert parser._determine_dmarc_result("pass", "fail") == "pass"  # SPF passes -> DMARC passes
        assert parser._determine_dmarc_result("fail", "pass") == "pass"  # DKIM passes -> DMARC passes
        assert parser._determine_dmarc_result("fail", "fail") == "fail"  # Both fail -> DMARC fails
        
        # Test with actual XML parsing
        xml_with_mixed_results = """<?xml version="1.0"?>
        <feedback>
            <report_metadata>
                <org_name>Test</org_name>
                <email>test@example.com</email>
                <report_id>test</report_id>
                <date_range><begin>1640995200</begin><end>1641081600</end></date_range>
            </report_metadata>
            <policy_published><domain>example.com</domain><p>none</p></policy_published>
            <record>
                <row>
                    <source_ip>1.2.3.4</source_ip>
                    <count>100</count>
                    <policy_evaluated>
                        <disposition>quarantine</disposition>
                        <dkim>fail</dkim>
                        <spf>pass</spf>
                    </policy_evaluated>
                </row>
                <identifiers><header_from>example.com</header_from></identifiers>
                <auth_results>
                    <spf><result>pass</result></spf>
                    <dkim><result>fail</result></dkim>
                </auth_results>
            </record>
        </feedback>"""
        
        report = parser.parse_xml_report(xml_with_mixed_results, "test_customer")
        
        # Even though disposition is "quarantine", DMARC should pass because SPF passes
        assert report.records[0].dmarc_result == "pass"
        assert report.records[0].spf_result == "pass"
        assert report.records[0].dkim_result == "fail"
    
    def test_elasticsearch_version_compatibility_fix(self):
        """REGRESSION TEST: Ensure Elasticsearch version compatibility"""
        # Originally failed with "Accept version must be either version 8 or 7, but found 9" error
        
        from backend.app.services.elasticsearch import ElasticsearchService
        
        with patch('backend.app.services.elasticsearch.settings') as mock_settings:
            mock_settings.ELASTICSEARCH_URL = "http://localhost:9200"
            mock_settings.ELASTICSEARCH_INDEX_PREFIX = "test-dmarc"
            
            # Mock Elasticsearch client
            with patch('backend.app.services.elasticsearch.Elasticsearch') as mock_es_class:
                mock_client = Mock()
                mock_es_class.return_value = mock_client
                mock_client.search.return_value = {"hits": {"total": {"value": 0}}}
                
                service = ElasticsearchService()
                
                # This should not raise media-type compatibility errors
                result = service.search_documents("reports", {"query": {"match_all": {}}})
                
                # Verify search was called with body parameter (ES 7.x format)
                mock_client.search.assert_called_once()
                call_args = mock_client.search.call_args
                assert "body" in call_args[1]  # Should use body parameter, not direct JSON
    
    def test_third_party_service_null_handling_fix(self):
        """REGRESSION TEST: Ensure third_party_service null values are handled"""
        # Originally left as null, causing frontend display issues
        
        service = DMARCService()
        
        with patch('backend.app.services.dmarc_service.dmarc_parser') as mock_parser:
            with patch('backend.app.services.dmarc_service.es_service') as mock_es:
                # Mock record with null third_party_service
                mock_record = Mock()
                mock_record.source_ip = "1.2.3.4"
                mock_record.third_party_service = None
                
                mock_report = Mock()
                mock_report.records = [mock_record]
                mock_report.dict.return_value = {"test": "data"}
                
                mock_parser.parse_xml_report.return_value = mock_report
                mock_es.index_document.return_value = {"result": "created"}
                
                # Process the report
                service.ingest_report("<test>xml</test>", "test_customer")
                
                # third_party_service should be set to "unknown", not left as null
                assert mock_record.third_party_service == "unknown"
    
    def test_login_hanging_fix(self):
        """REGRESSION TEST: Ensure login doesn't hang indefinitely"""
        # Originally login would hang due to async/sync mismatches in user service
        
        from fastapi.testclient import TestClient
        from backend.app.main import app
        import time
        
        client = TestClient(app)
        
        start_time = time.time()
        
        response = client.post("/api/v1/auth/login", json={
            "email": "admin@example.com",
            "password": "admin123"
        })
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Login should complete quickly (within 2 seconds)
        assert duration < 2.0, f"Login took {duration} seconds, indicating it may be hanging"
        assert response.status_code == 200
        assert "access_token" in response.json()
    
    def test_nested_aggregation_instead_of_scripts_fix(self):
        """REGRESSION TEST: Ensure we use nested aggregations instead of Painless scripts"""
        # Originally used Java-like stream syntax that wasn't compatible with Elasticsearch
        
        service = DMARCService()
        
        with patch('backend.app.services.dmarc_service.es_service') as mock_es:
            mock_es.search_documents.return_value = {
                "aggregations": {
                    "records": {
                        "total_emails": {"value": 1000},
                        "passed_emails": {"count": {"value": 800}},
                        "services": {"buckets": []}
                    }
                }
            }
            
            # Get summary
            summary = service.get_reports_summary("test_customer", 7)
            
            # Verify the query uses nested structure
            call_args = mock_es.search_documents.call_args
            query = call_args[0][1]
            
            # Should use nested aggregations
            assert "aggs" in query
            assert "records" in query["aggs"]
            assert "nested" in query["aggs"]["records"]
            assert query["aggs"]["records"]["nested"]["path"] == "records"
            
            # Should NOT use script-based aggregations
            def check_no_scripts(obj):
                if isinstance(obj, dict):
                    assert "script" not in obj
                    for value in obj.values():
                        check_no_scripts(value)
                elif isinstance(obj, list):
                    for item in obj:
                        check_no_scripts(item)
            
            check_no_scripts(query["aggs"])
            
            # Verify results are processed correctly
            assert summary.total_emails == 1000
            assert summary.passed_emails == 800
    
    def test_file_type_validation_improvement(self):
        """REGRESSION TEST: Ensure file type validation accepts both .xml and .xml.gz"""
        # Originally only accepted .xml files
        
        from fastapi.testclient import TestClient
        from backend.app.main import app
        
        client = TestClient(app)
        
        # Get auth token
        login_response = client.post("/api/v1/auth/login", json={
            "email": "admin@example.com",
            "password": "admin123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test that .xml files are accepted
        xml_file = io.BytesIO(b"<feedback></feedback>")
        with patch('backend.app.api.dmarc.dmarc_service') as mock_service:
            mock_service.ingest_report.return_value = "test-id"
            
            response = client.post(
                "/api/v1/dmarc/upload-report",
                headers=headers,
                files={"file": ("report.xml", xml_file, "application/xml")}
            )
            assert response.status_code == 200
        
        # Test that .xml.gz files are accepted
        gz_file = io.BytesIO(gzip.compress(b"<feedback></feedback>"))
        with patch('backend.app.api.dmarc.dmarc_service') as mock_service:
            mock_service.ingest_report.return_value = "test-id-gz"
            
            response = client.post(
                "/api/v1/dmarc/upload-report",
                headers=headers,
                files={"file": ("report.xml.gz", gz_file, "application/gzip")}
            )
            assert response.status_code == 200
        
        # Test that other file types are rejected
        txt_file = io.BytesIO(b"not xml")
        response = client.post(
            "/api/v1/dmarc/upload-report",
            headers=headers,
            files={"file": ("report.txt", txt_file, "text/plain")}
        )
        assert response.status_code == 400
        assert "Only XML and XML.GZ files are allowed" in response.json()["detail"]