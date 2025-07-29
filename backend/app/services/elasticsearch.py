from elasticsearch import Elasticsearch
from typing import Dict, List, Optional, Any
import json
from datetime import datetime
from ..core.config import settings

class ElasticsearchService:
    def __init__(self):
        self.client = Elasticsearch(
            [settings.ELASTICSEARCH_URL],
            basic_auth=(settings.ELASTICSEARCH_USERNAME, settings.ELASTICSEARCH_PASSWORD),
            verify_certs=False,  # Since we're not using SSL in development
            ssl_show_warn=False
        )
        self.index_prefix = settings.ELASTICSEARCH_INDEX_PREFIX
        
    def create_indices(self):
        indices = [
            self._get_dmarc_reports_index(),
            self._get_dns_records_index(),
            self._get_users_index(),
            self._get_third_party_services_index()
        ]
        
        for index_name, mapping in indices:
            if not self.client.indices.exists(index=index_name):
                self.client.indices.create(
                    index=index_name,
                    body={
                        "mappings": mapping,
                        "settings": {
                            "number_of_shards": 3,
                            "number_of_replicas": 1,
                            "refresh_interval": "30s"
                        }
                    }
                )
    
    def _get_dmarc_reports_index(self):
        index_name = f"{self.index_prefix}-reports"
        mapping = {
            "properties": {
                "customer_id": {"type": "keyword"},
                "metadata": {
                    "properties": {
                        "org_name": {"type": "keyword"},
                        "email": {"type": "keyword"},
                        "report_id": {"type": "keyword"},
                        "date_range_begin": {"type": "date"},
                        "date_range_end": {"type": "date"}
                    }
                },
                "policy": {
                    "properties": {
                        "domain": {"type": "keyword"},
                        "p": {"type": "keyword"},
                        "sp": {"type": "keyword"},
                        "pct": {"type": "integer"}
                    }
                },
                "records": {
                    "type": "nested",
                    "properties": {
                        "source_ip": {"type": "ip"},
                        "count": {"type": "integer"},
                        "spf_result": {"type": "keyword"},
                        "dkim_result": {"type": "keyword"},
                        "dmarc_result": {"type": "keyword"},
                        "third_party_service": {"type": "keyword"}
                    }
                },
                "processed_at": {"type": "date"}
            }
        }
        return index_name, mapping
    
    def _get_dns_records_index(self):
        index_name = f"{self.index_prefix}-dns"
        mapping = {
            "properties": {
                "customer_id": {"type": "keyword"},
                "domain": {"type": "keyword"},
                "record_type": {"type": "keyword"},
                "record_name": {"type": "keyword"},
                "record_value": {"type": "text"},
                "last_checked": {"type": "date"},
                "syntax_valid": {"type": "boolean"},
                "recommendations": {"type": "text"},
                "errors": {"type": "text"}
            }
        }
        return index_name, mapping
    
    def _get_users_index(self):
        index_name = f"{self.index_prefix}-users"
        mapping = {
            "properties": {
                "customer_id": {"type": "keyword"},
                "email": {"type": "keyword"},
                "full_name": {"type": "text"},
                "role": {"type": "keyword"},
                "is_active": {"type": "boolean"},
                "hashed_password": {"type": "keyword"},
                "created_at": {"type": "date"},
                "updated_at": {"type": "date"}
            }
        }
        return index_name, mapping
    
    def _get_third_party_services_index(self):
        index_name = f"{self.index_prefix}-services"
        mapping = {
            "properties": {
                "service_name": {
                    "type": "text",
                    "fields": {
                        "keyword": {
                            "type": "keyword",
                            "ignore_above": 256
                        }
                    }
                },
                "ip_ranges": {"type": "keyword"},
                "domain_patterns": {"type": "keyword"},
                "reverse_dns_patterns": {"type": "keyword"},
                "configuration_instructions": {"type": "text"},
                "documentation": {"type": "text"},
                "setup_guide": {"type": "text"},
                "troubleshooting": {"type": "text"},
                "is_active": {"type": "boolean"},
                "created_at": {"type": "date"},
                "updated_at": {"type": "date"}
            }
        }
        return index_name, mapping
    
    def index_document(self, index_suffix: str, doc_id: str, document: Dict[str, Any]):
        index_name = f"{self.index_prefix}-{index_suffix}"
        return self.client.index(
            index=index_name,
            id=doc_id,
            body=document
        )
    
    def search_documents(self, index_suffix: str, query: Dict[str, Any], size: int = 100):
        index_name = f"{self.index_prefix}-{index_suffix}"
        return self.client.search(
            index=index_name,
            body=query,
            size=size
        )
    
    def get_document(self, index_suffix: str, doc_id: str):
        index_name = f"{self.index_prefix}-{index_suffix}"
        try:
            return self.client.get(index=index_name, id=doc_id)
        except Exception:
            return None
    
    def delete_document(self, index_suffix: str, doc_id: str):
        index_name = f"{self.index_prefix}-{index_suffix}"
        return self.client.delete(index=index_name, id=doc_id)
    
    def recreate_services_index(self):
        """Recreate the services index with the correct mapping"""
        index_name = f"{self.index_prefix}-services"
        
        # Delete the index if it exists
        if self.client.indices.exists(index=index_name):
            self.client.indices.delete(index=index_name)
        
        # Create the index with the new mapping
        _, mapping = self._get_third_party_services_index()
        self.client.indices.create(
            index=index_name,
            body={
                "mappings": mapping,
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0,
                    "refresh_interval": "1s"
                }
            }
        )

es_service = ElasticsearchService()