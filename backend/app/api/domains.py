from fastapi import APIRouter, Depends, HTTPException
from typing import List
from pydantic import BaseModel
from ..models.user import User
from .auth import get_current_active_user

router = APIRouter()

class Domain(BaseModel):
    id: str
    name: str
    created_at: str
    updated_at: str
    is_active: bool

class DomainCreate(BaseModel):
    name: str

# In-memory domain storage for now (could be moved to Elasticsearch later)
_domains = {
    "default": [
        {
            "id": "1",
            "name": "example.com",
            "created_at": "2025-01-01T00:00:00",
            "updated_at": "2025-01-01T00:00:00",
            "is_active": True
        }
    ]
}

@router.get("/", response_model=List[Domain])
async def get_domains(current_user: User = Depends(get_current_active_user)):
    """Get all domains for the current user's customer"""
    customer_id = current_user.customer_id
    return _domains.get(customer_id, [])

@router.post("/", response_model=Domain)
async def create_domain(
    domain: DomainCreate,
    current_user: User = Depends(get_current_active_user)
):
    """Create a new domain"""
    customer_id = current_user.customer_id
    if customer_id not in _domains:
        _domains[customer_id] = []

    import uuid
    from datetime import datetime

    new_domain = {
        "id": str(uuid.uuid4()),
        "name": domain.name,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "is_active": True
    }
    _domains[customer_id].append(new_domain)
    return new_domain

@router.delete("/{domain_id}")
async def delete_domain(
    domain_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Delete a domain"""
    customer_id = current_user.customer_id
    if customer_id not in _domains:
        raise HTTPException(status_code=404, detail="Domain not found")

    domains = _domains[customer_id]
    for i, d in enumerate(domains):
        if d["id"] == domain_id:
            del domains[i]
            return {"message": "Domain deleted"}

    raise HTTPException(status_code=404, detail="Domain not found")
