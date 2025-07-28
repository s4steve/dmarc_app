from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any
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
    try:
        report = await analytics_service.get_detailed_report(current_user.customer_id, days)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate analytics report: {str(e)}")

@router.get("/export/{format}")
async def export_analytics_report(
    format: str,
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_active_user)
):
    """Export analytics report in various formats (JSON, CSV, PDF)"""
    try:
        if format not in ["json", "csv", "pdf"]:
            raise HTTPException(status_code=400, detail="Unsupported export format. Use: json, csv, pdf")
        
        report = await analytics_service.get_detailed_report(current_user.customer_id, days)
        
        if format == "json":
            return report
        elif format == "csv":
            # Convert to CSV format
            csv_data = await analytics_service.export_to_csv(report)
            return {"data": csv_data, "filename": f"dmarc_report_{days}d.csv"}
        elif format == "pdf":
            # Generate PDF report
            pdf_data = await analytics_service.export_to_pdf(report)
            return {"data": pdf_data, "filename": f"dmarc_report_{days}d.pdf"}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export report: {str(e)}")

@router.get("/health")
async def analytics_health_check():
    return {"status": "healthy", "service": "analytics-api"}