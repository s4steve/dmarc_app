from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from ..models.user import User
from ..models.dmarc import ThirdPartyService
from ..services.third_party_service import third_party_service_identifier
from .auth import get_current_active_user, require_admin, require_system_admin

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
async def get_third_party_services(
    current_user: User = Depends(get_current_active_user)
):
    try:
        services = await third_party_service_identifier.get_all_services()
        return services
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get services: {str(e)}")

@router.post("/", response_model=Dict[str, str])
async def add_third_party_service(
    service: ThirdPartyService,
    current_user: User = Depends(require_admin)
):
    try:
        service_id = await third_party_service_identifier.add_custom_service(service)
        return {"message": "Service added successfully", "service_id": service_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to add service: {str(e)}")

@router.put("/{service_id}", response_model=Dict[str, str])
async def update_third_party_service(
    service_id: str,
    service_data: Dict[str, Any],
    current_user: User = Depends(require_admin)
):
    try:
        success = await third_party_service_identifier.update_service(service_id, service_data)
        if not success:
            raise HTTPException(status_code=404, detail="Service not found")
        return {"message": "Service updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to update service: {str(e)}")

@router.post("/initialize")
async def initialize_default_services(
    current_user: User = Depends(require_admin)
):
    try:
        await third_party_service_identifier.initialize_services()
        return {"message": "Default services initialized successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize services: {str(e)}")

@router.post("/admin/recreate-index")
async def recreate_services_index(
    current_user: User = Depends(require_system_admin)
):
    """Recreate the services index with correct mapping and reinitialize services"""
    try:
        from ..services.elasticsearch import es_service
        
        # Recreate the index with proper mapping
        es_service.recreate_services_index()
        
        # Reinitialize default services
        await third_party_service_identifier.initialize_services()
        
        return {"message": "Services index recreated and services reinitialized successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to recreate index: {str(e)}")

# System Admin only endpoints
@router.get("/admin", response_model=List[Dict[str, Any]])
async def get_services_admin_view(
    current_user: User = Depends(require_system_admin)
):
    """Get all services with detailed admin information"""
    try:
        services = await third_party_service_identifier.get_all_services()
        return services
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get services: {str(e)}")

@router.get("/admin/{service_id}")
async def get_service_details(
    service_id: str,
    current_user: User = Depends(require_system_admin)
):
    """Get detailed information about a specific service"""
    try:
        service = await third_party_service_identifier.get_service_by_id(service_id)
        if not service:
            raise HTTPException(status_code=404, detail="Service not found")
        return service
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get service: {str(e)}")

@router.put("/admin/{service_id}")
async def update_service_admin(
    service_id: str,
    service_update: ServiceUpdate,
    current_user: User = Depends(require_system_admin)
):
    """Update service configuration (System Admin only)"""
    try:
        # Convert to dict and filter out None values
        update_data = {k: v for k, v in service_update.dict().items() if v is not None}
        
        success = await third_party_service_identifier.update_service(service_id, update_data)
        if not success:
            raise HTTPException(status_code=404, detail="Service not found")
        return {"message": "Service updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to update service: {str(e)}")

@router.delete("/admin/{service_id}")
async def delete_service(
    service_id: str,
    current_user: User = Depends(require_system_admin)
):
    """Delete a service (System Admin only)"""
    try:
        success = await third_party_service_identifier.delete_service(service_id)
        if not success:
            raise HTTPException(status_code=404, detail="Service not found")
        return {"message": "Service deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to delete service: {str(e)}")

@router.post("/admin/{service_id}/documentation")
async def update_service_documentation(
    service_id: str,
    doc_data: ServiceDocumentation,
    current_user: User = Depends(require_system_admin)
):
    """Update service documentation (System Admin only)"""
    try:
        success = await third_party_service_identifier.update_service_documentation(
            service_id, doc_data.dict()
        )
        if not success:
            raise HTTPException(status_code=404, detail="Service not found")
        return {"message": "Documentation updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to update documentation: {str(e)}")