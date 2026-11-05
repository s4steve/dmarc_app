import uuid
from datetime import datetime
from elasticsearch import ConflictError
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from pydantic import BaseModel, Field
from ..models.user import User
from ..services.elasticsearch import es_service
from ..utils.sanitizer import InputSanitizer
from .auth import get_current_active_user

router = APIRouter()

INDEX = "domains"

class Domain(BaseModel):
    id: str
    name: str
    created_at: str
    updated_at: str
    is_active: bool

class DomainCreate(BaseModel):
    name: str = Field(min_length=1, max_length=253)

def list_domains(customer_id: str) -> List[dict]:
    query = {"query": {"term": {"customer_id": customer_id}}, "sort": [{"name": "asc"}]}
    hits = es_service.search_documents(INDEX, query, size=1000)["hits"]["hits"]
    return [{k: v for k, v in h["_source"].items() if k != "customer_id"} for h in hits]

@router.get("/", response_model=List[Domain])
async def get_domains(current_user: User = Depends(get_current_active_user)):
    """Get all domains for the current user's customer"""
    return list_domains(current_user.customer_id)

@router.post("/", response_model=Domain)
async def create_domain(
    domain: DomainCreate,
    current_user: User = Depends(get_current_active_user)
):
    """Create a new domain"""
    name = InputSanitizer.sanitize_domain(domain.name)
    now = datetime.utcnow().isoformat()
    doc = {"customer_id": current_user.customer_id, "id": str(uuid.uuid4()), "name": name,
           "created_at": now, "updated_at": now, "is_active": True}
    try:
        # The document id makes a domain unique per customer
        es_service.client.create(index=f"{es_service.index_prefix}-{INDEX}",
                                 id=f"{current_user.customer_id}:{name}", document=doc, refresh="true")
    except ConflictError:
        raise HTTPException(status_code=409, detail=f"{name} has already been added")
    return {k: v for k, v in doc.items() if k != "customer_id"}

@router.delete("/{domain_id}")
async def delete_domain(
    domain_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Delete a domain. Its reports are kept."""
    query = {"query": {"bool": {"filter": [
        {"term": {"customer_id": current_user.customer_id}}, {"term": {"id": domain_id}}]}}}
    hits = es_service.search_documents(INDEX, query, size=1)["hits"]["hits"]
    if not hits:
        raise HTTPException(status_code=404, detail="Domain not found")
    es_service.delete_document(INDEX, hits[0]["_id"], refresh="true")
    return {"message": "Domain deleted"}
