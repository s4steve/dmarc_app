"""
Test configuration and fixtures for DMARC Analytics Platform
"""
import pytest
import tempfile
import os
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from backend.app.services.elasticsearch import ElasticsearchService
from backend.app.services.dmarc_service import DMARCService
from backend.app.services.dmarc_parser import DMARCParser

@pytest.fixture
def mock_elasticsearch():
    """Mock Elasticsearch service for testing"""
    mock_es = Mock(spec=ElasticsearchService)
    mock_es.index_document.return_value = {"_id": "test-id", "result": "created"}
    mock_es.search_documents.return_value = {
        "hits": {"total": {"value": 0}, "hits": []},
        "aggregations": {}
    }
    return mock_es

@pytest.fixture
def sample_dmarc_xml():
    """Sample DMARC XML report for testing"""
    return """<?xml version="1.0" encoding="UTF-8"?>
    <feedback>
        <report_metadata>
            <org_name>Test Organization</org_name>
            <email>test@example.com</email>
            <report_id>test_report_123</report_id>
            <date_range>
                <begin>1640995200</begin>
                <end>1641081600</end>
            </date_range>
        </report_metadata>
        <policy_published>
            <domain>example.com</domain>
            <adkim>r</adkim>
            <aspf>r</aspf>
            <p>none</p>
            <sp>none</sp>
            <pct>100</pct>
        </policy_published>
        <record>
            <row>
                <source_ip>192.168.1.1</source_ip>
                <count>100</count>
                <policy_evaluated>
                    <disposition>none</disposition>
                    <dkim>pass</dkim>
                    <spf>pass</spf>
                </policy_evaluated>
            </row>
            <identifiers>
                <header_from>example.com</header_from>
                <envelope_from>bounce@mailchimp.com</envelope_from>
                <envelope_to>user@example.com</envelope_to>
            </identifiers>
            <auth_results>
                <spf>
                    <domain>example.com</domain>
                    <scope>mfrom</scope>
                    <result>pass</result>
                </spf>
                <dkim>
                    <domain>example.com</domain>
                    <selector>k1</selector>
                    <result>pass</result>
                </dkim>
            </auth_results>
        </record>
        <record>
            <row>
                <source_ip>10.0.0.1</source_ip>
                <count>50</count>
                <policy_evaluated>
                    <disposition>quarantine</disposition>
                    <dkim>fail</dkim>
                    <spf>fail</spf>
                </policy_evaluated>
            </row>
            <identifiers>
                <header_from>example.com</header_from>
                <envelope_from>spammer@suspicious.com</envelope_from>
                <envelope_to>user@example.com</envelope_to>
            </identifiers>
            <auth_results>
                <spf>
                    <domain>example.com</domain>
                    <scope>mfrom</scope>
                    <result>fail</result>
                </spf>
                <dkim>
                    <domain>example.com</domain>
                    <selector>default</selector>
                    <result>fail</result>
                </dkim>
            </auth_results>
        </record>
    </feedback>"""

@pytest.fixture
def sample_dmarc_xml_gzipped():
    """Sample gzipped DMARC XML report for testing"""
    import gzip
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <feedback>
        <report_metadata>
            <org_name>Test Gzip Organization</org_name>
            <email>gzip@example.com</email>
            <report_id>gzip_test_456</report_id>
            <date_range>
                <begin>1640995200</begin>
                <end>1641081600</end>
            </date_range>
        </report_metadata>
        <policy_published>
            <domain>example.com</domain>
            <p>none</p>
            <pct>100</pct>
        </policy_published>
        <record>
            <row>
                <source_ip>203.0.113.1</source_ip>
                <count>25</count>
                <policy_evaluated>
                    <disposition>none</disposition>
                    <dkim>pass</dkim>
                    <spf>pass</spf>
                </policy_evaluated>
            </row>
            <identifiers>
                <header_from>example.com</header_from>
                <envelope_from>sender@legitimate.com</envelope_from>
            </identifiers>
            <auth_results>
                <spf>
                    <domain>example.com</domain>
                    <result>pass</result>
                </spf>
                <dkim>
                    <domain>example.com</domain>
                    <result>pass</result>
                </dkim>
            </auth_results>
        </record>
    </feedback>"""
    return gzip.compress(xml_content.encode('utf-8'))

@pytest.fixture 
def test_client():
    """Test client for FastAPI application"""
    from fastapi.testclient import TestClient
    from backend.app.main import app
    return TestClient(app)

@pytest.fixture
def authenticated_headers(test_client):
    """Get authentication headers for test requests"""
    login_data = {
        "email": "admin@example.com",
        "password": "admin123"
    }
    response = test_client.post("/api/v1/auth/login", json=login_data)
    if response.status_code == 200:
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    return {}

@pytest.fixture
def sample_aggregation_data():
    """Sample Elasticsearch aggregation response"""
    return {
        "aggregations": {
            "records": {
                "doc_count": 2,
                "total_emails": {"value": 150.0},
                "passed_emails": {
                    "doc_count": 1,
                    "count": {"value": 100.0}
                },
                "services": {
                    "buckets": [
                        {
                            "key": "unknown",
                            "doc_count": 2,
                            "email_count": {"value": 150.0}
                        }
                    ]
                }
            }
        }
    }

@pytest.fixture
def sample_time_series_data():
    """Sample time series aggregation response"""
    return {
        "aggregations": {
            "daily_stats": {
                "buckets": [
                    {
                        "key_as_string": "2025-07-21T00:00:00.000Z",
                        "key": 1642723200000,
                        "doc_count": 1,
                        "records": {
                            "doc_count": 2,
                            "total_emails": {"value": 150.0},
                            "passed_emails": {
                                "doc_count": 1,
                                "count": {"value": 100.0}
                            }
                        }
                    }
                ]
            }
        }
    }