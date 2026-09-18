from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from pydantic import BaseModel, Field
from ..models.user import User
from ..services.notification_service import notification_service
from .auth import require_admin

router = APIRouter()

class AlertThreshold(BaseModel):
    failure_rate: float = Field(50.0, ge=0, le=100)
    volume_spike: float = Field(2.0, gt=0)

class NotificationPreferences(BaseModel):
    model_config = {"extra": "forbid"}
    email_alerts: bool = True
    weekly_summary: bool = True
    dns_change_alerts: bool = True
    high_severity_only: bool = False
    alert_threshold: AlertThreshold = AlertThreshold()

@router.get("/preferences", response_model=Dict[str, Any])
async def get_notification_preferences(current_user: User = Depends(require_admin)):
    """Get notification preferences for the customer"""
    return await notification_service.get_notification_preferences(current_user.customer_id)

@router.put("/preferences", response_model=Dict[str, str])
async def update_notification_preferences(
    preferences: NotificationPreferences,
    current_user: User = Depends(require_admin)
):
    """Update notification preferences for the customer"""
    if not await notification_service.update_notification_preferences(
        current_user.customer_id, preferences.model_dump()
    ):
        raise HTTPException(status_code=400, detail="Failed to update preferences")
    return {"message": "Notification preferences updated successfully"}

@router.post("/test-alert")
async def send_test_alert(current_user: User = Depends(require_admin)):
    """Send a test alert notification"""
    test_alert = {
        'id': 'test-alert-123',
        'title': 'Test Alert Notification',
        'description': 'This is a test alert to verify email notifications are working correctly.',
        'severity': 'medium',
        'created_at': '2024-01-01T12:00:00Z',
        'data': {'test_parameter': 'test_value'}
    }
    if not await notification_service.send_alert_notification(current_user.customer_id, test_alert):
        raise HTTPException(status_code=400, detail="Failed to send test notification")
    return {"message": "Test notification sent successfully"}

@router.get("/health")
async def notifications_health_check():
    return {"status": "healthy", "service": "notifications-api"}
