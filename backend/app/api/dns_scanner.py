from fastapi import APIRouter, Depends, HTTPException
from app.api.auth import get_current_active_user
from app.models.user import User
from app.services.dns_service import DNSScanner

router = APIRouter()

@router.post("/scan-domain/", summary="Scan a domain for DMARC, SPF, and DKIM records", response_description="DMARC, SPF, and DKIM records for the specified domain")
def scan_domain(
    domain: str,
    current_user: User = Depends(get_current_active_user),
):
    """
    Scans a domain for DMARC, SPF, and DKIM records.

    - **domain**: The domain to scan.
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only administrators can access this resource.")

    scanner = DNSScanner(domain)
    dmarc_record = scanner.get_dmarc_record()
    spf_record = scanner.get_spf_record()
    dkim_record = scanner.get_dkim_record("_dkim") # Default selector

    return {
        "domain": domain,
        "dmarc": dmarc_record,
        "spf": spf_record,
        "dkim": dkim_record,
    }
