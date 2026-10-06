from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Any, Dict, List
from pydantic import BaseModel, Field
from ..models.user import User
from ..services.elasticsearch import es_service
from ..services.spf_flattening_service import spf_flattening_service as spf
from ..services.third_party_service import third_party_service_identifier
from ..middleware.rate_limiter import user_limiter
from ..utils.sanitizer import InputSanitizer
from .auth import get_current_active_user, require_admin, require_system_admin

# Managed (flattened) SPF per domain, published on the DNS control plane.
# Writes change who may send as the domain, so they need an admin.
router = APIRouter()

class SpfPolicyUpdate(BaseModel):
    # Include domains (e.g. _spf.google.com) or IPs/CIDRs; the control plane validates each
    senders: List[str] = Field(min_length=1, max_length=50)

async def _status(customer_id: str, domain: str) -> Dict[str, Any]:
    mapping = spf.get_mapping(customer_id, domain)
    if not mapping:
        return {"domain": domain, "configured": False}
    fqdn = mapping["fqdn"]
    policy = await spf.get_policy(fqdn) or {}
    live = await spf.live_spf(domain)
    return {
        "domain": domain,
        "configured": bool(policy),
        "include": fqdn,
        "senders": policy.get("senders", []),
        "terms": policy.get("terms", []),
        # Lookups a receiver spends on the include: the root record plus its chunks
        "lookups": policy.get("records"),
        "last_error": policy.get("last_error"),
        "updated_at": policy.get("updated_at"),
        "current_record": live,
        "installed": None if live is None else spf.includes(live, fqdn),
        "suggested_record": spf.suggested_record(live, fqdn),
    }

@router.get("/admin/status")
async def get_spf_connection_status(current_user: User = Depends(require_system_admin)):
    """The control-plane connection settings (never the token), for system admins."""
    return spf.status()

@router.post("/admin/test")
@user_limiter.limit("10/minute")
async def test_spf_connection(request: Request, current_user: User = Depends(require_system_admin)):
    """Checks the settings, the connection, the token and its access to SPF_ZONE."""
    return await spf.test_connection()

@router.get("/{domain}")
@user_limiter.limit("30/minute")
async def get_spf_policy(request: Request, domain: str, current_user: User = Depends(get_current_active_user)):
    domain = InputSanitizer.sanitize_domain(domain)
    return await _status(current_user.customer_id, domain)

@router.get("/{domain}/suggestions")
@user_limiter.limit("30/minute")
async def get_spf_suggestions(request: Request, domain: str, current_user: User = Depends(get_current_active_user)):
    """Catalog services that can be flattened, flagging those seen sending as the domain."""
    domain = InputSanitizer.sanitize_domain(domain)
    query = {
        "query": {"bool": {"filter": [
            {"term": {"customer_id": current_user.customer_id}},
            {"term": {"policy.domain": domain}},
        ]}},
        "aggs": {"records": {"nested": {"path": "records"}, "aggs": {
            "services": {"terms": {"field": "records.third_party_service", "size": 100},
                         "aggs": {"emails": {"sum": {"field": "records.count"}}}},
        }}},
    }
    try:
        buckets = es_service.search_documents("reports", query, size=0)["aggregations"]["records"]["services"]["buckets"]
    except Exception:  # no reports index yet
        buckets = []
    seen = {b["key"]: int(b["emails"]["value"]) for b in buckets}
    return {"services": [
        {"service_name": s.service_name, "spf_includes": s.spf_includes, "emails_seen": seen.get(s.service_name, 0)}
        for s in third_party_service_identifier.known_services if s.spf_includes
    ]}

@router.put("/{domain}")
@user_limiter.limit("10/minute")
async def put_spf_policy(
    request: Request, domain: str, update: SpfPolicyUpdate, current_user: User = Depends(require_admin)
):
    domain = InputSanitizer.sanitize_domain(domain)
    senders = [s.strip() for s in update.senders if s.strip()]
    if not senders:
        raise HTTPException(status_code=400, detail="At least one sender is required")
    spf._configured()  # fail before creating a mapping
    mapping = spf.ensure_mapping(current_user.customer_id, domain)
    await spf.put_policy(mapping["fqdn"], senders)
    return await _status(current_user.customer_id, domain)

@router.delete("/{domain}")
@user_limiter.limit("10/minute")
async def delete_spf_policy(request: Request, domain: str, current_user: User = Depends(require_admin)):
    domain = InputSanitizer.sanitize_domain(domain)
    mapping = spf.get_mapping(current_user.customer_id, domain)
    if not mapping:
        raise HTTPException(status_code=404, detail="No managed SPF for this domain")
    # An include of a name that no longer exists is a permerror: SPF fails for all mail
    live = await spf.live_spf(domain)
    if live is None:
        raise HTTPException(status_code=503, detail="Couldn't read the domain's SPF record; try again")
    if spf.includes(live, mapping["fqdn"]):
        raise HTTPException(
            status_code=409,
            detail=f"Remove include:{mapping['fqdn']} from the domain's SPF record first",
        )
    await spf.delete_policy(mapping["fqdn"])
    spf.delete_mapping(current_user.customer_id, domain)
    return {"domain": domain, "configured": False}
