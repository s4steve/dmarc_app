from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
from ..models.user import User
from ..models.dns import DNSCheckResult, DNSRecord
from ..services.dns_service import dns_service
from .auth import get_current_active_user

router = APIRouter()

@router.post("/check/{domain}", response_model=DNSCheckResult)
async def check_domain_dns(
    domain: str,
    current_user: User = Depends(get_current_active_user)
):
    try:
        result = await dns_service.check_domain_records(current_user.customer_id, domain)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check DNS records: {str(e)}")

@router.get("/records", response_model=List[DNSRecord])
async def get_dns_records(
    current_user: User = Depends(get_current_active_user)
):
    try:
        records = await dns_service.get_dns_records_by_customer(current_user.customer_id)
        return records
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get DNS records: {str(e)}")

@router.get("/health")
async def dns_health_check():
    return {"status": "healthy", "service": "dns-api"}