import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from app.services.elasticsearch import ElasticsearchService, es_service

class TestElasticsearchService:
    
    @pytest.fixture
    def mock_es_client(self):
        return Mock()
    
    @pytest.fixture
    def es_service_instance(self, mock_es_client):
        with patch('app.services.elasticsearch.Elasticsearch', return_value=mock_es_client):
            return ElasticsearchService()
    
    def test_index_document_success(self, es_service_instance, mock_es_client):
        """Test successful document indexing"""
        mock_es_client.index.return_value = {"_id": "doc-1", "result": "created"}
        
        document = {
            "service_name": "Google Workspace",
            "ip_ranges": ["209.85.128.0/17"],
            "is_active": True
        }
        
        result = es_service_instance.index_document("services", "doc-1", document)
        
        assert result["_id"] == "doc-1"
        assert result["result"] == "created"
        mock_es_client.index.assert_called_once_with(
            index="dmarc-services",
            id="doc-1",
            body=document
        )
    
    def test_index_document_elasticsearch_error(self, es_service_instance, mock_es_client):
        """Test document indexing with Elasticsearch error"""
        from elasticsearch import ElasticsearchException
        mock_es_client.index.side_effect = ElasticsearchException("Connection failed")
        
        document = {"test": "data"}
        
        with pytest.raises(Exception) as exc_info:
            es_service_instance.index_document("test_index", "doc-1", document)
        
        assert "Connection failed" in str(exc_info.value)
    
    def test_get_document_success(self, es_service_instance, mock_es_client):
        """Test successful document retrieval"""
        mock_response = {
            "_id": "doc-1",
            "_source": {
                "service_name": "SendGrid",
                "ip_ranges": ["149.72.0.0/16"],
                "is_active": True
            },
            "_index": "services"
        }
        mock_es_client.get.return_value = mock_response
        
        result = es_service_instance.get_document("services", "doc-1")
        
        assert result["_id"] == "doc-1"
        assert result["_source"]["service_name"] == "SendGrid"
        mock_es_client.get.assert_called_once_with(index="dmarc-services", id="doc-1")
    
    def test_get_document_not_found(self, es_service_instance, mock_es_client):
        """Test document retrieval when document doesn't exist"""
        from elasticsearch import NotFoundError
        mock_es_client.get.side_effect = NotFoundError("Document not found")
        
        result = es_service_instance.get_document("services", "nonexistent")
        
        assert result is None
    
    def test_search_documents_success(self, es_service_instance, mock_es_client):
        """Test successful document search"""
        mock_response = {
            "took": 5,
            "hits": {
                "total": {"value": 2},
                "hits": [
                    {
                        "_id": "doc-1",
                        "_source": {"service_name": "Google Workspace", "is_active": True}
                    },
                    {
                        "_id": "doc-2", 
                        "_source": {"service_name": "SendGrid", "is_active": True}
                    }
                ]
            },
            "aggregations": {}
        }
        mock_es_client.search.return_value = mock_response
        
        query = {
            "query": {
                "term": {"is_active": True}
            }
        }
        
        result = es_service_instance.search_documents("services", query)
        
        assert result["hits"]["total"]["value"] == 2
        assert len(result["hits"]["hits"]) == 2
        mock_es_client.search.assert_called_once_with(
            index="dmarc-services",
            body=query,
            size=100
        )
    
    def test_search_documents_with_size_parameter(self, es_service_instance, mock_es_client):
        """Test document search with custom size parameter"""
        mock_response = {"hits": {"hits": []}}
        mock_es_client.search.return_value = mock_response
        
        query = {"query": {"match_all": {}}}
        
        es_service_instance.search_documents("services", query, size=50)
        
        mock_es_client.search.assert_called_once_with(
            index="dmarc-services",
            body=query,
            size=50
        )
    
    def test_search_documents_elasticsearch_error(self, es_service_instance, mock_es_client):
        """Test document search with Elasticsearch error"""
        from elasticsearch import ElasticsearchException
        mock_es_client.search.side_effect = ElasticsearchException("Search failed")
        
        query = {"query": {"match_all": {}}}
        
        with pytest.raises(Exception) as exc_info:
            es_service_instance.search_documents("services", query)
        
        assert "Search failed" in str(exc_info.value)
    
    def test_delete_document_success(self, es_service_instance, mock_es_client):
        """Test successful document deletion"""
        mock_es_client.delete.return_value = {"result": "deleted"}
        
        result = es_service_instance.delete_document("services", "doc-1")
        
        assert result["result"] == "deleted"
        mock_es_client.delete.assert_called_once_with(index="dmarc-services", id="doc-1")
    
    def test_delete_document_not_found(self, es_service_instance, mock_es_client):
        """Test document deletion when document doesn't exist"""
        from elasticsearch import NotFoundError
        mock_es_client.delete.side_effect = NotFoundError("Document not found")
        
        result = es_service_instance.delete_document("services", "nonexistent")
        
        assert result is None
    
    def test_create_indices_success(self, es_service_instance, mock_es_client):
        """Test successful indices creation"""
        mock_es_client.indices.exists.return_value = False
        mock_es_client.indices.create.return_value = {"acknowledged": True}
        
        es_service_instance.create_indices()
        
        # Verify that indices.create was called for each index
        assert mock_es_client.indices.create.call_count == 4  # reports, dns, users, services
    
    def test_create_indices_already_exist(self, es_service_instance, mock_es_client):
        """Test indices creation when indices already exist"""
        mock_es_client.indices.exists.return_value = True
        
        es_service_instance.create_indices()
        
        # Should not call create if indices already exist
        mock_es_client.indices.create.assert_not_called()
    
    def test_recreate_services_index_success(self, es_service_instance, mock_es_client):
        """Test successful services index recreation"""
        mock_es_client.indices.exists.return_value = True
        mock_es_client.indices.delete.return_value = {"acknowledged": True}
        mock_es_client.indices.create.return_value = {"acknowledged": True}
        
        es_service_instance.recreate_services_index()
        
        mock_es_client.indices.delete.assert_called_once_with(index="dmarc-services")
        mock_es_client.indices.create.assert_called_once()

class TestElasticsearchServiceIntegration:
    
    def test_services_index_mapping_creation(self):
        """Test that services index mapping is created correctly"""
        with patch('app.services.elasticsearch.Elasticsearch') as mock_es_class:
            mock_es_client = Mock()
            mock_es_class.return_value = mock_es_client
            mock_es_client.indices.exists.return_value = False
            mock_es_client.indices.create.return_value = {"acknowledged": True}
            
            service = ElasticsearchService()
            
            # Test the create_indices method
            service.create_indices()
            
            # Verify services index was created with proper mapping
            services_mapping_found = False
            for call in mock_es_client.indices.create.call_args_list:
                if 'dmarc-services' in str(call):
                    services_mapping_found = True
                    
            assert services_mapping_found, "Services index mapping was not created"
    
    def test_reports_index_mapping_creation(self):
        """Test that reports index mapping is created correctly"""
        with patch('app.services.elasticsearch.Elasticsearch') as mock_es_class:
            mock_es_client = Mock()
            mock_es_class.return_value = mock_es_client
            mock_es_client.indices.exists.return_value = False
            mock_es_client.indices.create.return_value = {"acknowledged": True}
            
            service = ElasticsearchService()
            service.create_indices()
            
            # Verify reports index was created
            reports_mapping_found = False
            for call in mock_es_client.indices.create.call_args_list:
                if 'dmarc-reports' in str(call):
                    reports_mapping_found = True
                    
            assert reports_mapping_found, "Reports index mapping was not created"
    
    def test_connection_error_handling(self):
        """Test handling of Elasticsearch connection errors"""
        with patch('app.services.elasticsearch.Elasticsearch') as mock_es_class:
            from elasticsearch import ConnectionError
            mock_es_class.side_effect = ConnectionError("Connection failed")
            
            # Should handle connection error gracefully
            with pytest.raises(Exception):
                ElasticsearchService()
    
    def test_real_query_structures(self):
        """Test with real query structures used in the application"""
        with patch('app.services.elasticsearch.Elasticsearch') as mock_es_class:
            mock_es_client = Mock()
            mock_es_class.return_value = mock_es_client
            
            # Mock search response
            mock_es_client.search.return_value = {
                "hits": {
                    "total": {"value": 1},
                    "hits": [
                        {
                            "_id": "service-1",
                            "_source": {
                                "service_name": "Google Workspace",
                                "ip_ranges": ["209.85.128.0/17"],
                                "is_active": True
                            }
                        }
                    ]
                },
                "aggregations": {
                    "records": {
                        "total_emails": {"value": 1000},
                        "passed_emails": {"count": {"value": 800}},
                        "services": {
                            "buckets": [
                                {"key": "Google Workspace", "email_count": {"value": 500}}
                            ]
                        }
                    }
                }
            }
            
            service = ElasticsearchService()
            
            # Test complex query structure like those used in DMARC service
            complex_query = {
                "query": {
                    "bool": {
                        "must": [
                            {"term": {"customer_id": "test-customer"}},
                            {"range": {
                                "metadata.date_range_begin": {
                                    "gte": "2024-01-01T00:00:00",
                                    "lte": "2024-01-08T00:00:00"
                                }
                            }},
                            {"term": {"policy.domain": "example.com"}}
                        ]
                    }
                },
                "aggs": {
                    "records": {
                        "nested": {"path": "records"},
                        "aggs": {
                            "total_emails": {"sum": {"field": "records.count"}},
                            "passed_emails": {
                                "filter": {"term": {"records.dmarc_result": "pass"}},
                                "aggs": {
                                    "count": {"sum": {"field": "records.count"}}
                                }
                            }
                        }
                    }
                }
            }
            
            result = service.search_documents("reports", complex_query)
            
            assert result["hits"]["total"]["value"] == 1
            assert "aggregations" in result
            assert "records" in result["aggregations"]
    
    def test_error_recovery_scenarios(self):
        """Test various error recovery scenarios"""
        with patch('app.services.elasticsearch.Elasticsearch') as mock_es_class:
            mock_es_client = Mock()
            mock_es_class.return_value = mock_es_client
            
            service = ElasticsearchService()
            
            # Test timeout error
            from elasticsearch import ConnectionTimeout
            mock_es_client.search.side_effect = ConnectionTimeout("Request timed out")
            
            with pytest.raises(Exception):
                service.search_documents("services", {"query": {"match_all": {}}})
            
            # Test cluster unavailable
            from elasticsearch import ConnectionError
            mock_es_client.index.side_effect = ConnectionError("No living connections")
            
            with pytest.raises(Exception):
                service.index_document("services", "doc-1", {"test": "data"})
            
            # Test index corruption/mapping issues
            from elasticsearch import RequestError
            mock_es_client.search.side_effect = RequestError("Mapping error")
            
            with pytest.raises(Exception):
                service.search_documents("services", {"query": {"match_all": {}}})

class TestElasticsearchServiceConfiguration:
    
    def test_elasticsearch_client_configuration(self):
        """Test Elasticsearch client is configured correctly"""
        with patch('app.services.elasticsearch.Elasticsearch') as mock_es_class:
            mock_es_client = Mock()
            mock_es_class.return_value = mock_es_client
            
            ElasticsearchService()
            
            # Verify Elasticsearch client was initialized with correct parameters
            mock_es_class.assert_called_once()
            call_args = mock_es_class.call_args
            
            # Check that hosts parameter is configured
            assert 'hosts' in call_args[1] or len(call_args[0]) > 0
    
    def test_singleton_behavior(self):
        """Test that es_service behaves as a singleton"""
        # The es_service should be the same instance across imports
        from app.services.elasticsearch import es_service as es1
        from app.services.elasticsearch import es_service as es2
        
        assert es1 is es2