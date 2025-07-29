from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, Request
from typing import List, Dict, Any
import gzip
from ..models.user import User
from ..models.dmarc import DMARCReportSummary
from ..services.dmarc_service import dmarc_service
from ..services.file_security_service import file_security_service
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
        
        # Step 1: Comprehensive file validation
        file_content = await file.read()
        validation_result = file_security_service.validate_upload(file, current_user.email)
        
        # Step 2: Process validated file safely
        xml_string, processing_id = file_security_service.process_validated_file(
            file_content, validation_result, current_user.email
        )
        
        # Step 3: Ingest the validated DMARC report
        report_id = dmarc_service.ingest_report(xml_string, current_user.customer_id)
        
        # Log successful upload
        ErrorSanitizer.log_security_event(
            "file_upload_success",
            {
                "user_id": current_user.email,
                "processing_id": processing_id,
                "report_id": report_id,
                "file_hash": validation_result["file_hash"],
                "file_size": validation_result["file_size"]
            }
        )
        
        return {
            "message": "DMARC report uploaded and processed successfully",
            "report_id": report_id,
            "processing_id": processing_id,
            "file_hash": validation_result["file_hash"][:16],  # Partial hash for tracking
            "processed_size": validation_result["decompressed_size"]
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
@user_limiter.limit("30/minute")  # Reasonable limit for summary requests
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