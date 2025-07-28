from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class DMARCRecord(BaseModel):
    source_ip: str
    count: int
    spf_result: str
    dkim_result: str
    dmarc_result: str
    third_party_service: Optional[str] = None
    header_from: Optional[str] = None
    envelope_from: Optional[str] = None

class DMARCReportMetadata(BaseModel):
    org_name: str
    email: str
    report_id: str
    date_range_begin: datetime
    date_range_end: datetime

class DMARCReportPolicy(BaseModel):
    domain: str
    adkim: Optional[str] = None
    aspf: Optional[str] = None
    p: str
    sp: Optional[str] = None
    pct: Optional[int] = None

class DMARCReport(BaseModel):
    customer_id: str
    metadata: DMARCReportMetadata
    policy: DMARCReportPolicy
    records: List[DMARCRecord]
    processed_at: datetime
    raw_xml: Optional[str] = None

class DMARCReportSummary(BaseModel):
    total_emails: int
    passed_emails: int
    failed_emails: int
    pass_rate: float
    date_range: Dict[str, datetime]
    top_services: List[Dict[str, Any]]

class ThirdPartyService(BaseModel):
    service_name: str
    ip_ranges: List[str]
    domain_patterns: List[str]
    reverse_dns_patterns: List[str]
    configuration_instructions: Optional[str] = None
    is_active: bool = True