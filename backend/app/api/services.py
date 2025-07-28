from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from ..models.user import User
from ..models.dmarc import ThirdPartyService
from ..services.third_party_service import third_party_service_identifier
from .auth import get_current_active_user, require_admin

router = APIRouter()

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