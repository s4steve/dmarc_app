from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.api.auth import get_current_active_user
from app.models.user import User
from app.services.dns_service import DNSScanner

router = APIRouter()

class DomainScanRequest(BaseModel):
    domain: str

@router.post("/scan-domain/", summary="Scan a domain for DMARC, SPF, and DKIM records", response_description="DMARC, SPF, and DKIM records for the specified domain")
def scan_domain(
    request: DomainScanRequest,
    current_user: User = Depends(get_current_active_user),
):
    """
    Scans a domain for DMARC, SPF, and DKIM records.

    - **domain**: The domain to scan.
    """
    # Check if user has admin or system_admin role
    if current_user.role not in ["admin", "system_admin"]:
        raise HTTPException(status_code=403, detail="Only administrators can access this resource.")

    scanner = DNSScanner(request.domain)
    dmarc_record = scanner.get_dmarc_record()
    spf_record = scanner.get_spf_record()
    dkim_record = scanner.get_dkim_record("_dkim") # Default selector

    return {
        "domain": request.domain,
        "dmarc": dmarc_record,
        "spf": spf_record,
        "dkim": dkim_record,
    }
