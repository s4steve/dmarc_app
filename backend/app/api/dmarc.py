from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from typing import List, Dict, Any
import gzip
from ..models.user import User
from ..models.dmarc import DMARCReportSummary
from ..services.dmarc_service import dmarc_service
from .auth import get_current_active_user

router = APIRouter()

@router.post("/upload-report")
async def upload_dmarc_report(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    if not (file.filename.endswith('.xml') or file.filename.endswith('.xml.gz')):
        raise HTTPException(status_code=400, detail="Only XML and XML.GZ files are allowed")
    
    try:
        file_content = await file.read()
        
        # Handle gzipped files
        if file.filename.endswith('.gz'):
            try:
                xml_content = gzip.decompress(file_content)
                xml_string = xml_content.decode('utf-8')
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Failed to decompress gzip file: {str(e)}")
        else:
            # Handle regular XML files
            xml_string = file_content.decode('utf-8')
        
        report_id = dmarc_service.ingest_report(xml_string, current_user.customer_id)
        
        return {
            "message": "DMARC report uploaded successfully",
            "report_id": report_id
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process report: {str(e)}")

@router.get("/summary", response_model=DMARCReportSummary)
async def get_dmarc_summary(
    days: int = Query(7, ge=1, le=365),
    current_user: User = Depends(get_current_active_user)
):
    try:
        summary = dmarc_service.get_reports_summary(current_user.customer_id, days)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get summary: {str(e)}")

@router.get("/reports")
async def get_dmarc_reports(
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_active_user)
) -> List[Dict[str, Any]]:
    try:
        reports = dmarc_service.get_reports_by_customer(current_user.customer_id, limit)
        return reports
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get reports: {str(e)}")

@router.get("/time-series")
async def get_time_series_data(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_active_user)
) -> List[Dict[str, Any]]:
    try:
        data = dmarc_service.get_time_series_data(current_user.customer_id, days)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get time series data: {str(e)}")

@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "dmarc-api"}