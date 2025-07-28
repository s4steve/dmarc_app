from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum

class DNSRecordType(str, Enum):
    SPF = "TXT"
    DKIM = "TXT"
    DMARC = "TXT"
    MX = "MX"

class DNSRecord(BaseModel):
    customer_id: str
    domain: str
    record_type: DNSRecordType
    record_name: str
    record_value: str
    last_checked: datetime
    syntax_valid: bool
    recommendations: List[str] = []
    errors: List[str] = []

class DNSCheckResult(BaseModel):
    domain: str
    spf_record: Optional[DNSRecord] = None
    dmarc_record: Optional[DNSRecord] = None
    dkim_records: List[DNSRecord] = []
    mx_records: List[DNSRecord] = []
    overall_status: str
    recommendations: List[str] = []

class DNSRecommendation(BaseModel):
    record_type: DNSRecordType
    current_value: Optional[str]
    recommended_value: str
    priority: str
    description: str