import dns.resolver
from typing import List, Dict, Any, Optional
from datetime import datetime
from ..models.dns import DNSRecord, DNSCheckResult, DNSRecordType, DNSRecommendation
from .elasticsearch import es_service
import uuid
import re

class DNSService:
    def __init__(self):
        self.resolver = dns.resolver.Resolver()
        self.resolver.timeout = 10
        self.resolver.lifetime = 10
    
    async def check_domain_records(self, customer_id: str, domain: str) -> DNSCheckResult:
        spf_record = await self._check_spf_record(customer_id, domain)
        dmarc_record = await self._check_dmarc_record(customer_id, domain)
        dkim_records = await self._check_dkim_records(customer_id, domain)
        mx_records = await self._check_mx_records(customer_id, domain)
        
        overall_status = self._calculate_overall_status(spf_record, dmarc_record, dkim_records)
        recommendations = self._generate_recommendations(spf_record, dmarc_record, dkim_records)
        
        return DNSCheckResult(
            domain=domain,
            spf_record=spf_record,
            dmarc_record=dmarc_record,
            dkim_records=dkim_records,
            mx_records=mx_records,
            overall_status=overall_status,
            recommendations=recommendations
        )
    
    async def _check_spf_record(self, customer_id: str, domain: str) -> Optional[DNSRecord]:
        try:
            answers = self.resolver.resolve(domain, 'TXT')
            spf_records = [str(rdata) for rdata in answers if str(rdata).startswith('"v=spf1')]
            
            if not spf_records:
                return None
            
            spf_value = spf_records[0].strip('"')
            syntax_valid, errors = self._validate_spf_syntax(spf_value)
            recommendations = self._get_spf_recommendations(spf_value)
            
            record = DNSRecord(
                customer_id=customer_id,
                domain=domain,
                record_type=DNSRecordType.SPF,
                record_name=domain,
                record_value=spf_value,
                last_checked=datetime.utcnow(),
                syntax_valid=syntax_valid,
                recommendations=recommendations,
                errors=errors
            )
            
            await self._store_dns_record(record)
            return record
            
        except Exception as e:
            return None
    
    async def _check_dmarc_record(self, customer_id: str, domain: str) -> Optional[DNSRecord]:
        try:
            dmarc_domain = f"_dmarc.{domain}"
            answers = self.resolver.resolve(dmarc_domain, 'TXT')
            dmarc_records = [str(rdata) for rdata in answers if str(rdata).startswith('"v=DMARC1')]
            
            if not dmarc_records:
                return None
            
            dmarc_value = dmarc_records[0].strip('"')
            syntax_valid, errors = self._validate_dmarc_syntax(dmarc_value)
            recommendations = self._get_dmarc_recommendations(dmarc_value)
            
            record = DNSRecord(
                customer_id=customer_id,
                domain=domain,
                record_type=DNSRecordType.DMARC,
                record_name=dmarc_domain,
                record_value=dmarc_value,
                last_checked=datetime.utcnow(),
                syntax_valid=syntax_valid,
                recommendations=recommendations,
                errors=errors
            )
            
            await self._store_dns_record(record)
            return record
            
        except Exception as e:
            return None
    
    async def _check_dkim_records(self, customer_id: str, domain: str) -> List[DNSRecord]:
        dkim_records = []
        common_selectors = ['default', 'google', 'k1', 'mail', 'selector1', 'selector2']
        
        for selector in common_selectors:
            try:
                dkim_domain = f"{selector}._domainkey.{domain}"
                answers = self.resolver.resolve(dkim_domain, 'TXT')
                
                for rdata in answers:
                    dkim_value = str(rdata).strip('"')
                    if 'v=DKIM1' in dkim_value:
                        syntax_valid, errors = self._validate_dkim_syntax(dkim_value)
                        recommendations = self._get_dkim_recommendations(dkim_value)
                        
                        record = DNSRecord(
                            customer_id=customer_id,
                            domain=domain,
                            record_type=DNSRecordType.DKIM,
                            record_name=dkim_domain,
                            record_value=dkim_value,
                            last_checked=datetime.utcnow(),
                            syntax_valid=syntax_valid,
                            recommendations=recommendations,
                            errors=errors
                        )
                        
                        await self._store_dns_record(record)
                        dkim_records.append(record)
                        
            except Exception:
                continue
        
        return dkim_records
    
    async def _check_mx_records(self, customer_id: str, domain: str) -> List[DNSRecord]:
        try:
            answers = self.resolver.resolve(domain, 'MX')
            mx_records = []
            
            for rdata in answers:
                mx_value = f"{rdata.priority} {rdata.exchange}"
                
                record = DNSRecord(
                    customer_id=customer_id,
                    domain=domain,
                    record_type=DNSRecordType.MX,
                    record_name=domain,
                    record_value=mx_value,
                    last_checked=datetime.utcnow(),
                    syntax_valid=True,
                    recommendations=[],
                    errors=[]
                )
                
                await self._store_dns_record(record)
                mx_records.append(record)
            
            return mx_records
            
        except Exception:
            return []
    
    def _validate_spf_syntax(self, spf_record: str) -> tuple[bool, List[str]]:
        errors = []
        
        if not spf_record.startswith('v=spf1'):
            errors.append("SPF record must start with 'v=spf1'")
        
        if not re.search(r'[~-]?all$', spf_record):
            errors.append("SPF record should end with 'all' mechanism")
        
        include_count = len(re.findall(r'include:', spf_record))
        if include_count > 10:
            errors.append("Too many include mechanisms (DNS lookup limit)")
        
        return len(errors) == 0, errors
    
    def _validate_dmarc_syntax(self, dmarc_record: str) -> tuple[bool, List[str]]:
        errors = []
        
        if not dmarc_record.startswith('v=DMARC1'):
            errors.append("DMARC record must start with 'v=DMARC1'")
        
        if 'p=' not in dmarc_record:
            errors.append("DMARC record must contain policy (p=)")
        
        policy_match = re.search(r'p=(none|quarantine|reject)', dmarc_record)
        if not policy_match:
            errors.append("Invalid DMARC policy value")
        
        return len(errors) == 0, errors
    
    def _validate_dkim_syntax(self, dkim_record: str) -> tuple[bool, List[str]]:
        errors = []
        
        if 'v=DKIM1' not in dkim_record:
            errors.append("DKIM record must contain 'v=DKIM1'")
        
        if 'p=' not in dkim_record:
            errors.append("DKIM record must contain public key (p=)")
        
        return len(errors) == 0, errors
    
    def _get_spf_recommendations(self, spf_record: str) -> List[str]:
        recommendations = []
        
        if spf_record.endswith('~all'):
            recommendations.append("Consider upgrading to '-all' for stricter policy")
        elif spf_record.endswith('+all'):
            recommendations.append("Replace '+all' with '-all' for better security")
        
        include_count = len(re.findall(r'include:', spf_record))
        if include_count > 8:
            recommendations.append("Consider reducing include mechanisms to avoid DNS lookup limits")
        
        return recommendations
    
    def _get_dmarc_recommendations(self, dmarc_record: str) -> List[str]:
        recommendations = []
        
        if 'p=none' in dmarc_record:
            recommendations.append("Consider upgrading DMARC policy to 'quarantine' or 'reject'")
        
        if 'rua=' not in dmarc_record:
            recommendations.append("Add aggregate reporting (rua=) to receive DMARC reports")
        
        if 'pct=' not in dmarc_record or 'pct=100' not in dmarc_record:
            recommendations.append("Set pct=100 to apply policy to all emails")
        
        return recommendations
    
    def _get_dkim_recommendations(self, dkim_record: str) -> List[str]:
        recommendations = []
        
        if 't=y' in dkim_record:
            recommendations.append("Remove test mode (t=y) from DKIM record")
        
        return recommendations
    
    def _calculate_overall_status(self, spf: Optional[DNSRecord], dmarc: Optional[DNSRecord], dkim: List[DNSRecord]) -> str:
        if not spf or not dmarc:
            return "Critical"
        
        if not spf.syntax_valid or not dmarc.syntax_valid:
            return "Error"
        
        if len(dkim) == 0:
            return "Warning"
        
        if any(not record.syntax_valid for record in dkim):
            return "Warning"
        
        return "Good"
    
    def _generate_recommendations(self, spf: Optional[DNSRecord], dmarc: Optional[DNSRecord], dkim: List[DNSRecord]) -> List[str]:
        recommendations = []
        
        if not spf:
            recommendations.append("Add SPF record to prevent email spoofing")
        
        if not dmarc:
            recommendations.append("Add DMARC record for email authentication policy")
        
        if len(dkim) == 0:
            recommendations.append("Configure DKIM signing for email authentication")
        
        return recommendations
    
    async def _store_dns_record(self, record: DNSRecord):
        record_id = str(uuid.uuid4())
        record_doc = record.dict()
        await es_service.index_document("dns", record_id, record_doc)
    
    async def get_dns_records_by_customer(self, customer_id: str) -> List[DNSRecord]:
        query = {
            "query": {
                "term": {"customer_id": customer_id}
            },
            "sort": [
                {"last_checked": {"order": "desc"}}
            ]
        }
        
        result = await es_service.search_documents("dns", query)
        records = []
        for hit in result["hits"]["hits"]:
            record_data = hit["_source"]
            records.append(DNSRecord(**record_data))
        
        return records

dns_service = DNSService()