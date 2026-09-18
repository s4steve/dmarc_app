from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from ..models.user import User
from ..models.dmarc import ThirdPartyService
from ..services.third_party_service import third_party_service_identifier
from ..services.elasticsearch import es_service
from .auth import get_current_active_user, require_system_admin

# Third-party service definitions are global (shared by all customers),
# so every mutating route requires a system admin.
router = APIRouter()

class ServiceUpdate(BaseModel):
    service_name: Optional[str] = None
    ip_ranges: Optional[List[str]] = None
    domain_patterns: Optional[List[str]] = None
    reverse_dns_patterns: Optional[List[str]] = None
    configuration_instructions: Optional[str] = None
    documentation: Optional[str] = None
    is_active: Optional[bool] = None

class ServiceDocumentation(BaseModel):
    service_id: str
    documentation: str
    setup_guide: Optional[str] = None
    troubleshooting: Optional[str] = None

@router.get("/", response_model=List[Dict[str, Any]])
async def get_third_party_services(current_user: User = Depends(get_current_active_user)):
    return await third_party_service_identifier.get_all_services()

@router.post("/", response_model=Dict[str, str])
async def add_third_party_service(
    service: ThirdPartyService,
    current_user: User = Depends(require_system_admin)
):
    service_id = await third_party_service_identifier.add_custom_service(service)
    return {"message": "Service added successfully", "service_id": service_id}

@router.post("/initialize")
async def initialize_default_services(current_user: User = Depends(require_system_admin)):
    await third_party_service_identifier.initialize_services()
    return {"message": "Default services initialized successfully"}

@router.post("/admin/recreate-index")
async def recreate_services_index(current_user: User = Depends(require_system_admin)):
    """Recreate the services index with correct mapping and reinitialize services"""
    es_service.recreate_services_index()
    await third_party_service_identifier.initialize_services()
    return {"message": "Services index recreated and services reinitialized successfully"}

@router.get("/admin", response_model=List[Dict[str, Any]])
async def get_services_admin_view(current_user: User = Depends(require_system_admin)):
    """Get all services with detailed admin information"""
    return await third_party_service_identifier.get_all_services()

@router.get("/admin/{service_id}")
async def get_service_details(
    service_id: str,
    current_user: User = Depends(require_system_admin)
):
    service = await third_party_service_identifier.get_service_by_id(service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    return service

@router.put("/admin/{service_id}")
async def update_service_admin(
    service_id: str,
    service_update: ServiceUpdate,
    current_user: User = Depends(require_system_admin)
):
    update_data = service_update.model_dump(exclude_none=True)
    if not await third_party_service_identifier.update_service(service_id, update_data):
        raise HTTPException(status_code=404, detail="Service not found")
    return {"message": "Service updated successfully"}

@router.delete("/admin/{service_id}")
async def delete_service(
    service_id: str,
    current_user: User = Depends(require_system_admin)
):
    if not await third_party_service_identifier.delete_service(service_id):
        raise HTTPException(status_code=404, detail="Service not found")
    return {"message": "Service deleted successfully"}

@router.post("/admin/{service_id}/documentation")
async def update_service_documentation(
    service_id: str,
    doc_data: ServiceDocumentation,
    current_user: User = Depends(require_system_admin)
):
    # service_id comes from the path; don't let the body overwrite it
    doc = doc_data.model_dump(exclude={"service_id"}, exclude_none=True)
    if not await third_party_service_identifier.update_service_documentation(service_id, doc):
        raise HTTPException(status_code=404, detail="Service not found")
    return {"message": "Documentation updated successfully"}
