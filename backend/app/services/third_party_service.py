import socket
import ipaddress
from typing import List, Dict, Any, Optional
from datetime import datetime
from ..models.dmarc import ThirdPartyService
from .elasticsearch import es_service
import uuid

class ThirdPartyServiceIdentifier:
    def __init__(self):
        self.known_services = self._load_default_services()
    
    def _load_default_services(self) -> List[ThirdPartyService]:
        return [
            ThirdPartyService(
                service_name="Mailchimp",
                ip_ranges=["205.201.128.0/20", "198.2.128.0/18", "148.105.8.0/21"],
                domain_patterns=["*.mailchimp.com", "*.mcsv.net"],
                reverse_dns_patterns=["*.mailchimp.com", "*.mcsv.net"],
                configuration_instructions="Add 'include:servers.mcsv.net' to your SPF record"
            ),
            ThirdPartyService(
                service_name="SendGrid",
                ip_ranges=["149.72.0.0/16", "208.115.214.0/24", "198.37.147.0/24"],
                domain_patterns=["*.sendgrid.net", "*.sendgrid.com"],
                reverse_dns_patterns=["*.sendgrid.net", "*.sendgrid.com"],
                configuration_instructions="Add 'include:sendgrid.net' to your SPF record"
            ),
            ThirdPartyService(
                service_name="Amazon SES",
                ip_ranges=["54.240.0.0/12", "205.251.192.0/19"],
                domain_patterns=["*.amazonses.com", "*.ses.amazonaws.com"],
                reverse_dns_patterns=["*.amazonses.com", "*.amazonaws.com"],
                configuration_instructions="Add 'include:amazonses.com' to your SPF record"
            ),
            ThirdPartyService(
                service_name="Microsoft 365",
                ip_ranges=["40.92.0.0/15", "40.107.0.0/16", "52.100.0.0/14"],
                domain_patterns=["*.outlook.com", "*.office365.com", "*.microsoft.com"],
                reverse_dns_patterns=["*.outlook.com", "*.protection.outlook.com"],
                configuration_instructions="Add 'include:spf.protection.outlook.com' to your SPF record"
            ),
            ThirdPartyService(
                service_name="Google Workspace",
                ip_ranges=["209.85.128.0/17", "64.233.160.0/19", "66.249.80.0/20"],
                domain_patterns=["*.google.com", "*.googlemail.com"],
                reverse_dns_patterns=["*.google.com", "*.googlemail.com"],
                configuration_instructions="Add 'include:_spf.google.com' to your SPF record"
            ),
            ThirdPartyService(
                service_name="Constant Contact",
                ip_ranges=["208.75.123.0/24", "69.57.132.0/24"],
                domain_patterns=["*.constantcontact.com", "*.ctctcdn.com"],
                reverse_dns_patterns=["*.constantcontact.com"],
                configuration_instructions="Add 'include:spf.constantcontact.com' to your SPF record"
            ),
            ThirdPartyService(
                service_name="Hubspot",
                ip_ranges=["209.62.12.0/24", "208.85.238.0/24"],
                domain_patterns=["*.hubspot.com", "*.hs-sites.com"],
                reverse_dns_patterns=["*.hubspot.com"],
                configuration_instructions="Add 'include:_spf.hubspot.com' to your SPF record"
            ),
            ThirdPartyService(
                service_name="Klaviyo",
                ip_ranges=["50.31.156.0/24", "198.2.185.0/24"],
                domain_patterns=["*.klaviyo.com", "*.klaviyomail.com"],
                reverse_dns_patterns=["*.klaviyo.com"],
                configuration_instructions="Add 'include:spf.klaviyo.com' to your SPF record"
            ),
            ThirdPartyService(
                service_name="Campaign Monitor",
                ip_ranges=["103.47.147.0/24", "103.47.148.0/24"],
                domain_patterns=["*.campaignmonitor.com", "*.createsend.com"],
                reverse_dns_patterns=["*.campaignmonitor.com"],
                configuration_instructions="Add 'include:cmail1.com' to your SPF record"
            ),
            ThirdPartyService(
                service_name="Mandrill/Mailchimp Transactional",
                ip_ranges=["198.2.128.0/24", "198.2.129.0/24"],
                domain_patterns=["*.mandrillapp.com"],
                reverse_dns_patterns=["*.mandrillapp.com"],
                configuration_instructions="Add 'include:spf.mandrillapp.com' to your SPF record"
            ),
            ThirdPartyService(
                service_name="Postmark",
                ip_ranges=["50.31.156.6/32", "50.31.156.77/32"],
                domain_patterns=["*.postmarkapp.com"],
                reverse_dns_patterns=["*.postmarkapp.com"],
                configuration_instructions="Add 'include:spf.postmarkapp.com' to your SPF record"
            ),
            ThirdPartyService(
                service_name="Salesforce Marketing Cloud",
                ip_ranges=["136.147.0.0/16", "199.21.137.0/24"],
                domain_patterns=["*.exacttarget.com", "*.salesforce.com"],
                reverse_dns_patterns=["*.exacttarget.com", "*.salesforce.com"],
                configuration_instructions="Add 'include:exacttarget.com' to your SPF record"
            )
        ]
    
    async def initialize_services(self):
        for service in self.known_services:
            service_id = str(uuid.uuid4())
            service_doc = service.dict()
            # Add timestamps
            service_doc["created_at"] = datetime.utcnow().isoformat()
            service_doc["updated_at"] = datetime.utcnow().isoformat()
            es_service.index_document("services", service_id, service_doc)
    
    def identify_service_by_ip(self, ip_address: str) -> Optional[str]:
        try:
            ip_obj = ipaddress.ip_address(ip_address)
            
            # First check against our known services in memory for better performance
            for service in self.known_services:
                for ip_range in service.ip_ranges:
                    try:
                        network = ipaddress.ip_network(ip_range, strict=False)
                        if ip_obj in network:
                            return service.service_name
                    except ValueError:
                        continue
            
            # Then check reverse DNS
            reverse_dns_service = self._identify_by_reverse_dns(ip_address)
            if reverse_dns_service:
                return reverse_dns_service
            
            return "unknown"
            
        except ValueError:
            return "unknown"
    
    def _identify_by_reverse_dns(self, ip_address: str) -> Optional[str]:
        try:
            hostname = socket.gethostbyaddr(ip_address)[0]
            
            # Check against our known services in memory
            for service in self.known_services:
                for pattern in service.reverse_dns_patterns:
                    pattern_clean = pattern.replace("*.", "")
                    if pattern_clean in hostname:
                        return service.service_name
            
            return None
            
        except socket.herror:
            return None
        except Exception:
            return None
    
    async def add_custom_service(self, service: ThirdPartyService) -> str:
        service_id = str(uuid.uuid4())
        service_doc = service.dict()
        es_service.index_document("services", service_id, service_doc)
        return service_id
    
    async def get_all_services(self) -> List[Dict[str, Any]]:
        try:
            # Try with the new keyword field first
            query = {
                "query": {
                    "bool": {
                        "must": [
                            {"term": {"is_active": True}}
                        ]
                    }
                },
                "sort": [
                    {"service_name.keyword": {"order": "asc"}}
                ]
            }
            
            result = es_service.search_documents("services", query)
        except Exception:
            # Fallback to simple query without sorting if index doesn't exist yet
            try:
                query = {
                    "query": {
                        "match_all": {}
                    }
                }
                result = es_service.search_documents("services", query)
            except Exception:
                # If no index exists, return empty list
                return []
        
        services = []
        for hit in result["hits"]["hits"]:
            service_data = hit["_source"]
            service_data["id"] = hit["_id"]
            services.append(service_data)
        
        # Sort in Python if Elasticsearch sorting failed
        if not services:
            return services
            
        try:
            services.sort(key=lambda x: x.get("service_name", "").lower())
        except Exception:
            pass
            
        return services
    
    async def update_service(self, service_id: str, service_data: Dict[str, Any]) -> bool:
        try:
            current_service = es_service.get_document("services", service_id)
            if not current_service:
                return False
            
            updated_data = current_service["_source"]
            updated_data.update(service_data)
            
            es_service.index_document("services", service_id, updated_data)
            return True
        except Exception:
            return False
    
    async def get_service_by_id(self, service_id: str) -> Optional[Dict[str, Any]]:
        try:
            result = es_service.get_document("services", service_id)
            if result:
                service_data = result["_source"]
                service_data["id"] = result["_id"]
                return service_data
            return None
        except Exception:
            return None
    
    async def delete_service(self, service_id: str) -> bool:
        try:
            # Instead of actually deleting, mark as inactive
            return self.update_service(service_id, {"is_active": False})
        except Exception:
            return False
    
    async def update_service_documentation(self, service_id: str, doc_data: Dict[str, Any]) -> bool:
        try:
            current_service = es_service.get_document("services", service_id)
            if not current_service:
                return False
            
            updated_data = current_service["_source"]
            updated_data.update(doc_data)
            
            es_service.index_document("services", service_id, updated_data)
            return True
        except Exception:
            return False

third_party_service_identifier = ThirdPartyServiceIdentifier()