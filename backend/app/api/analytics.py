from fastapi import APIRouter, Depends, Query
from typing import Dict, Any, Literal
from ..models.user import User
from ..services.analytics_service import analytics_service
from .auth import get_current_active_user

router = APIRouter()

@router.get("/detailed-report", response_model=Dict[str, Any])
async def get_detailed_analytics_report(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: User = Depends(get_current_active_user)
):
    """Generate comprehensive analytics report with advanced metrics"""
    return await analytics_service.get_detailed_report(current_user.customer_id, days)

@router.get("/export/{format}")
async def export_analytics_report(
    format: Literal["json", "csv", "pdf"],
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_active_user)
):
    """Export analytics report in various formats (JSON, CSV, PDF)"""
    report = await analytics_service.get_detailed_report(current_user.customer_id, days)
    if format == "json":
        return report
    if format == "csv":
        return {"data": await analytics_service.export_to_csv(report), "filename": f"dmarc_report_{days}d.csv"}
    return {"data": await analytics_service.export_to_pdf(report), "filename": f"dmarc_report_{days}d.pdf"}

@router.get("/health")
async def analytics_health_check():
    return {"status": "healthy", "service": "analytics-api"}
