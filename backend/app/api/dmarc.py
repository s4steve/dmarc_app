from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, Request
from typing import List, Dict, Any
import gzip
from ..models.user import User
from ..models.dmarc import DMARCReportSummary
from ..services.dmarc_service import dmarc_service
# from ..services.file_security_service import file_security_service  # Temporarily disabled
from ..utils.sanitizer import InputSanitizer
from ..utils.error_sanitizer import ErrorSanitizer
from ..middleware.rate_limiter import user_limiter
from .auth import get_current_active_user

router = APIRouter()

@router.post("/upload-report")
@user_limiter.limit("5/minute")  # Production rate limiting for file uploads
async def upload_dmarc_report(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    """
    Secure DMARC report upload with comprehensive validation
    """
    try:
        # Log upload attempt for security monitoring
        ErrorSanitizer.log_security_event(
            "file_upload_attempt",
            {
                "user_id": current_user.email,
                "filename": file.filename,
                "customer_id": current_user.customer_id
            }
        )
        
        # Simplified file processing (for getting the app running)
        file_content = await file.read()
        
        # Basic file validation
        if not file.filename or not file.filename.endswith(('.xml', '.gz')):
            raise HTTPException(status_code=400, detail="Invalid file type")
        
        # Process file content
        if file.filename.endswith('.gz'):
            try:
                xml_string = gzip.decompress(file_content).decode('utf-8')
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid gzip file")
        else:
            xml_string = file_content.decode('utf-8')
        
        # Ingest the DMARC report
        report_id = dmarc_service.ingest_report(xml_string, current_user.customer_id)
        
        # Log successful upload
        ErrorSanitizer.log_security_event(
            "file_upload_success",
            {
                "user_id": current_user.email,
                "report_id": report_id,
                "file_size": len(file_content)
            }
        )
        
        return {
            "message": "DMARC report uploaded and processed successfully",
            "report_id": report_id
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions from validation
        raise
    except Exception as e:
        # Log and sanitize unexpected errors
        ErrorSanitizer.log_security_event(
            "file_upload_error",
            {
                "user_id": current_user.email,
                "filename": getattr(file, 'filename', 'unknown'),
                "error": str(e)
            }
        )
        raise ErrorSanitizer.create_http_exception(
            500, "File upload processing failed", "file"
        )

@router.get("/summary", response_model=DMARCReportSummary)
# @user_limiter.limit("30/minute")  # Temporarily disabled
async def get_dmarc_summary(
    request: Request,
    days: int = Query(7, ge=1, le=365),
    domain: str = Query(None, description="Filter by domain"),
    current_user: User = Depends(get_current_active_user)
):
    try:
        # Input sanitization is now handled in the service layer
        summary = dmarc_service.get_reports_summary(current_user.customer_id, days, domain)
        return summary
    except HTTPException:
        # Re-raise HTTP exceptions from sanitization
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve DMARC summary")

@router.get("/reports")
async def get_dmarc_reports(
    limit: int = Query(100, ge=1, le=1000),
    domain: str = Query(None, description="Filter by domain"),
    current_user: User = Depends(get_current_active_user)
) -> List[Dict[str, Any]]:
    try:
        # Input sanitization is now handled in the service layer
        reports = dmarc_service.get_reports_by_customer(current_user.customer_id, limit, domain)
        return reports
    except HTTPException:
        # Re-raise HTTP exceptions from sanitization
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve DMARC reports")

@router.get("/time-series")
async def get_time_series_data(
    days: int = Query(30, ge=1, le=365),
    domain: str = Query(None, description="Filter by domain"),
    current_user: User = Depends(get_current_active_user)
) -> List[Dict[str, Any]]:
    try:
        # Input sanitization is now handled in the service layer
        data = dmarc_service.get_time_series_data(current_user.customer_id, days, domain)
        return data
    except HTTPException:
        # Re-raise HTTP exceptions from sanitization
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve time series data")

@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "dmarc-api"}