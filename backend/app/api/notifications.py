from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from ..models.user import User
from ..services.notification_service import notification_service
from .auth import get_current_active_user, require_admin

router = APIRouter()

@router.get("/preferences", response_model=Dict[str, Any])
async def get_notification_preferences(
    current_user: User = Depends(require_admin)
):
    """Get notification preferences for the customer"""
    try:
        preferences = await notification_service.get_notification_preferences(current_user.customer_id)
        return preferences
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get notification preferences: {str(e)}")

@router.put("/preferences", response_model=Dict[str, str])
async def update_notification_preferences(
    preferences: Dict[str, Any],
    current_user: User = Depends(require_admin)
):
    """Update notification preferences for the customer"""
    try:
        success = await notification_service.update_notification_preferences(
            current_user.customer_id, 
            preferences
        )
        if not success:
            raise HTTPException(status_code=400, detail="Failed to update preferences")
        
        return {"message": "Notification preferences updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update notification preferences: {str(e)}")

@router.post("/test-alert")
async def send_test_alert(
    current_user: User = Depends(require_admin)
):
    """Send a test alert notification"""
    try:
        test_alert = {
            'id': 'test-alert-123',
            'title': 'Test Alert Notification',
            'description': 'This is a test alert to verify email notifications are working correctly.',
            'severity': 'medium',
            'created_at': '2024-01-01T12:00:00Z',
            'data': {
                'test_parameter': 'test_value'
            }
        }
        
        success = await notification_service.send_alert_notification(current_user.customer_id, test_alert)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to send test notification")
        
        return {"message": "Test notification sent successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send test notification: {str(e)}")

@router.get("/health")
async def notifications_health_check():
    return {"status": "healthy", "service": "notifications-api"}