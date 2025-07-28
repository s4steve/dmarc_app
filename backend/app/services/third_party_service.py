import socket
import ipaddress
from typing import List, Dict, Any, Optional
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
            )
        ]
    
    async def initialize_services(self):
        for service in self.known_services:
            service_id = str(uuid.uuid4())
            service_doc = service.dict()
            await es_service.index_document("services", service_id, service_doc)
    
    async def identify_service_by_ip(self, ip_address: str) -> Optional[str]:
        try:
            ip_obj = ipaddress.ip_address(ip_address)
            
            query = {
                "query": {
                    "bool": {
                        "must": [
                            {"term": {"is_active": True}}
                        ]
                    }
                }
            }
            
            result = await es_service.search_documents("services", query)
            
            for hit in result["hits"]["hits"]:
                service = hit["_source"]
                for ip_range in service.get("ip_ranges", []):
                    try:
                        network = ipaddress.ip_network(ip_range, strict=False)
                        if ip_obj in network:
                            return service["service_name"]
                    except ValueError:
                        continue
            
            reverse_dns_service = await self._identify_by_reverse_dns(ip_address)
            if reverse_dns_service:
                return reverse_dns_service
            
            return None
            
        except ValueError:
            return None
    
    async def _identify_by_reverse_dns(self, ip_address: str) -> Optional[str]:
        try:
            hostname = socket.gethostbyaddr(ip_address)[0]
            
            query = {
                "query": {
                    "bool": {
                        "must": [
                            {"term": {"is_active": True}}
                        ]
                    }
                }
            }
            
            result = await es_service.search_documents("services", query)
            
            for hit in result["hits"]["hits"]:
                service = hit["_source"]
                for pattern in service.get("reverse_dns_patterns", []):
                    pattern_clean = pattern.replace("*.", "")
                    if pattern_clean in hostname:
                        return service["service_name"]
            
            return None
            
        except socket.herror:
            return None
        except Exception:
            return None
    
    async def add_custom_service(self, service: ThirdPartyService) -> str:
        service_id = str(uuid.uuid4())
        service_doc = service.dict()
        await es_service.index_document("services", service_id, service_doc)
        return service_id
    
    async def get_all_services(self) -> List[Dict[str, Any]]:
        query = {
            "query": {
                "term": {"is_active": True}
            },
            "sort": [
                {"service_name.keyword": {"order": "asc"}}
            ]
        }
        
        result = await es_service.search_documents("services", query)
        services = []
        for hit in result["hits"]["hits"]:
            service_data = hit["_source"]
            service_data["id"] = hit["_id"]
            services.append(service_data)
        
        return services
    
    async def update_service(self, service_id: str, service_data: Dict[str, Any]) -> bool:
        try:
            current_service = await es_service.get_document("services", service_id)
            if not current_service:
                return False
            
            updated_data = current_service["_source"]
            updated_data.update(service_data)
            
            await es_service.index_document("services", service_id, updated_data)
            return True
        except Exception:
            return False

third_party_service_identifier = ThirdPartyServiceIdentifier()