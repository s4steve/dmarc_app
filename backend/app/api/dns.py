from fastapi import APIRouter, Depends
from typing import List
from ..models.user import User
from ..models.dns import DNSCheckResult, DNSRecord
from ..services.dns_service import dns_service
from ..utils.sanitizer import InputSanitizer
from .auth import get_current_active_user

router = APIRouter()

@router.post("/check/{domain}", response_model=DNSCheckResult)
async def check_domain_dns(
    domain: str,
    current_user: User = Depends(get_current_active_user)
):
    domain = InputSanitizer.sanitize_domain(domain)
    return await dns_service.check_domain_records(current_user.customer_id, domain)

@router.get("/records", response_model=List[DNSRecord])
async def get_dns_records(current_user: User = Depends(get_current_active_user)):
    return await dns_service.get_dns_records_by_customer(current_user.customer_id)

@router.get("/health")
async def dns_health_check():
    return {"status": "healthy", "service": "dns-api"}
