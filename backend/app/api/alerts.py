from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any
from ..models.user import User
from ..services.alert_service import alert_service
from .auth import get_current_active_user

router = APIRouter()

@router.get("/", response_model=List[Dict[str, Any]])
async def get_alerts(
    days: int = Query(7, ge=1, le=30),
    current_user: User = Depends(get_current_active_user)
):
    try:
        alerts = await alert_service.get_alerts_for_customer(current_user.customer_id, days)
        return alerts
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get alerts: {str(e)}")

@router.post("/check")
async def trigger_alert_check(
    current_user: User = Depends(get_current_active_user)
):
    try:
        alerts = await alert_service.check_alerts_for_customer(current_user.customer_id)
        return {
            "message": f"Alert check completed. Generated {len(alerts)} alerts.",
            "alerts": alerts
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check alerts: {str(e)}")

@router.post("/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    current_user: User = Depends(get_current_active_user)
):
    try:
        success = await alert_service.resolve_alert(alert_id)
        if not success:
            raise HTTPException(status_code=404, detail="Alert not found")
        return {"message": "Alert resolved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resolve alert: {str(e)}")

@router.get("/health")
async def alerts_health_check():
    return {"status": "healthy", "service": "alerts-api"}