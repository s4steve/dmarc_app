"""
Tests for DMARC service functionality
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from backend.app.services.dmarc_service import DMARCService

class TestDMARCService:
    """Test DMARC business logic and data processing"""
    
    def setup_method(self):
        self.service = DMARCService()
    
    @patch('backend.app.services.dmarc_service.es_service')
    @patch('backend.app.services.dmarc_service.dmarc_parser')
    def test_ingest_report_success(self, mock_parser, mock_es):
        """Test successful report ingestion"""
        # Setup mocks
        mock_report = Mock()
        mock_report.records = [Mock()]
        mock_report.records[0].source_ip = "1.2.3.4"
        mock_report.records[0].third_party_service = None
        mock_report.dict.return_value = {"test": "data"}
        
        mock_parser.parse_xml_report.return_value = mock_report
        mock_es.index_document.return_value = {"result": "created"}
        
        # Test
        xml_content = "<test>xml</test>"
        customer_id = "test_customer"
        
        result = self.service.ingest_report(xml_content, customer_id)
        
        # Assertions
        assert result is not None
        mock_parser.parse_xml_report.assert_called_once_with(xml_content, customer_id)
        mock_es.index_document.assert_called_once()
        
        # Check that third_party_service was set to "unknown"
        assert mock_report.records[0].third_party_service == "unknown"
    
    @patch('backend.app.services.dmarc_service.es_service')
    def test_get_reports_summary_with_data(self, mock_es, sample_aggregation_data):
        """Test summary generation with sample data"""
        mock_es.search_documents.return_value = sample_aggregation_data
        
        summary = self.service.get_reports_summary("test_customer", 7)
        
        assert summary.total_emails == 150
        assert summary.passed_emails == 100
        assert summary.failed_emails == 50
        assert summary.pass_rate == pytest.approx(66.67, rel=0.01)
        assert len(summary.top_services) == 1
        assert summary.top_services[0]["service"] == "unknown"
        assert summary.top_services[0]["email_count"] == 150.0
    
    @patch('backend.app.services.dmarc_service.es_service')
    def test_get_reports_summary_no_data(self, mock_es):
        """Test summary generation with no data"""
        mock_es.search_documents.return_value = {
            "hits": {"total": {"value": 0}},
            "aggregations": {"records": {"total_emails": {"value": 0}}}
        }
        
        summary = self.service.get_reports_summary("test_customer", 7)
        
        assert summary.total_emails == 0
        assert summary.passed_emails == 0
        assert summary.failed_emails == 0
        assert summary.pass_rate == 0.0
        assert len(summary.top_services) == 0
    
    @patch('backend.app.services.dmarc_service.es_service')
    def test_get_time_series_data(self, mock_es, sample_time_series_data):
        """Test time series data generation - REGRESSION TEST for async issues"""
        mock_es.search_documents.return_value = sample_time_series_data
        
        time_series = self.service.get_time_series_data("test_customer", 30)
        
        assert len(time_series) == 1
        data_point = time_series[0]
        assert data_point["date"] == "2025-07-21T00:00:00.000Z"
        assert data_point["total_emails"] == 150
        assert data_point["passed_emails"] == 100
        assert data_point["failed_emails"] == 50
        assert data_point["pass_rate"] == pytest.approx(66.67, rel=0.01)
    
    @patch('backend.app.services.dmarc_service.es_service')
    def test_get_time_series_data_no_data(self, mock_es):
        """Test time series with no data"""
        mock_es.search_documents.return_value = {
            "aggregations": {"daily_stats": {"buckets": []}}
        }
        
        time_series = self.service.get_time_series_data("test_customer", 30)
        assert len(time_series) == 0
    
    @patch('backend.app.services.dmarc_service.es_service')
    def test_get_reports_by_customer(self, mock_es):
        """Test retrieving reports by customer"""
        mock_es.search_documents.return_value = {
            "hits": {
                "hits": [
                    {
                        "_id": "report1",
                        "_source": {
                            "customer_id": "test_customer",
                            "metadata": {"report_id": "test_report_1"}
                        }
                    },
                    {
                        "_id": "report2", 
                        "_source": {
                            "customer_id": "test_customer",
                            "metadata": {"report_id": "test_report_2"}
                        }
                    }
                ]
            }
        }
        
        reports = self.service.get_reports_by_customer("test_customer", 10)
        
        assert len(reports) == 2
        assert reports[0]["id"] == "report1"
        assert reports[1]["id"] == "report2"
    
    def test_elasticsearch_query_structure(self):
        """Test that Elasticsearch queries use correct nested structure - REGRESSION TEST"""
        # This tests that we're using nested queries instead of script-based ones
        with patch('backend.app.services.dmarc_service.es_service') as mock_es:
            mock_es.search_documents.return_value = {
                "aggregations": {"records": {"total_emails": {"value": 0}}}
            }
            
            self.service.get_reports_summary("test_customer", 7)
            
            # Get the query that was passed to search_documents
            call_args = mock_es.search_documents.call_args
            query = call_args[0][1]  # Second argument is the query
            
            # Verify it uses nested aggregations
            assert "aggs" in query
            assert "records" in query["aggs"]
            assert "nested" in query["aggs"]["records"]
            assert query["aggs"]["records"]["nested"]["path"] == "records"
            
            # Verify it doesn't use script-based aggregations
            def check_no_scripts(obj):
                if isinstance(obj, dict):
                    assert "script" not in obj
                    for value in obj.values():
                        check_no_scripts(value)
                elif isinstance(obj, list):
                    for item in obj:
                        check_no_scripts(item)
            
            check_no_scripts(query["aggs"])
    
    @patch('backend.app.services.dmarc_service.dmarc_parser')
    def test_ingest_report_parsing_error(self, mock_parser):
        """Test error handling during XML parsing"""
        mock_parser.parse_xml_report.side_effect = ValueError("Parse error")
        
        with pytest.raises(ValueError, match="Failed to ingest DMARC report"):
            self.service.ingest_report("<invalid>xml</invalid>", "test_customer")
    
    @patch('backend.app.services.dmarc_service.es_service')
    @patch('backend.app.services.dmarc_service.dmarc_parser')
    def test_third_party_service_unknown_assignment(self, mock_parser, mock_es):
        """Test that third_party_service is set to 'unknown' when None - REGRESSION TEST"""
        # Setup mock with None third_party_service
        mock_record = Mock()
        mock_record.source_ip = "1.2.3.4"
        mock_record.third_party_service = None
        
        mock_report = Mock()
        mock_report.records = [mock_record]
        mock_report.dict.return_value = {"test": "data"}
        
        mock_parser.parse_xml_report.return_value = mock_report
        mock_es.index_document.return_value = {"result": "created"}
        
        # Test
        self.service.ingest_report("<test>xml</test>", "test_customer")
        
        # Verify third_party_service was set to "unknown"
        assert mock_record.third_party_service == "unknown"