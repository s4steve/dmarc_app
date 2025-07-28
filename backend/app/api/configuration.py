from fastapi import APIRouter, Depends, HTTPException, Path
from typing import Dict, Any, Optional
from ..models.user import User
from ..services.configuration_service import configuration_service
from .auth import get_current_active_user

router = APIRouter()

@router.get("/services", response_model=Dict[str, Dict])
async def get_all_service_configurations(
    current_user: User = Depends(get_current_active_user)
):
    """Get configuration instructions for all supported email services"""
    try:
        configurations = await configuration_service.get_all_service_configurations()
        return configurations
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get service configurations: {str(e)}")

@router.get("/services/{service_name}", response_model=Dict[str, Any])
async def get_service_configuration(
    service_name: str = Path(..., description="Name of the email service"),
    current_user: User = Depends(get_current_active_user)
):
    """Get configuration instructions for a specific email service"""
    try:
        config = await configuration_service.get_service_configuration(service_name)
        if not config:
            raise HTTPException(status_code=404, detail=f"Configuration not found for service: {service_name}")
        return config
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get service configuration: {str(e)}")

@router.get("/guidance/spf", response_model=Dict[str, Any])
async def get_spf_guidance(
    current_user: User = Depends(get_current_active_user)
):
    """Get generic SPF record configuration guidance"""
    try:
        guidance = configuration_service.get_generic_spf_guidance()
        return guidance
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get SPF guidance: {str(e)}")

@router.get("/guidance/dmarc", response_model=Dict[str, Any])
async def get_dmarc_guidance(
    current_user: User = Depends(get_current_active_user)
):
    """Get DMARC policy configuration guidance"""
    try:
        guidance = configuration_service.get_dmarc_policy_guidance()
        return guidance
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get DMARC guidance: {str(e)}")

@router.get("/guidance/dkim", response_model=Dict[str, Any])
async def get_dkim_guidance(
    current_user: User = Depends(get_current_active_user)
):
    """Get DKIM configuration guidance"""
    try:
        guidance = configuration_service.get_dkim_guidance()
        return guidance
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get DKIM guidance: {str(e)}")

@router.get("/health")
async def configuration_health_check():
    return {"status": "healthy", "service": "configuration-api"}