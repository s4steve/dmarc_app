from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, Request
from typing import List, Dict, Any
import re
import zlib
from ..models.user import User
from ..models.dmarc import DMARCReportSummary
from ..services.dmarc_service import dmarc_service
from ..utils.sanitizer import InputSanitizer
from ..utils.error_sanitizer import ErrorSanitizer
from ..middleware.rate_limiter import user_limiter
from .auth import get_current_active_user

router = APIRouter()

MAX_UPLOAD_BYTES = 10 * 1024 * 1024        # compressed or raw upload
MAX_XML_BYTES = 50 * 1024 * 1024           # after decompression
_DOCTYPE = re.compile(r'<!DOCTYPE', re.IGNORECASE)

def _decode_report(filename: str, content: bytes) -> str:
    """Turn an uploaded .xml or .xml.gz into XML text, with bomb and XXE guards"""
    if filename.endswith('.gz'):
        try:
            # wbits 16+MAX_WBITS = gzip framing; max_length caps output so a gzip bomb can't exhaust memory
            d = zlib.decompressobj(16 + zlib.MAX_WBITS)
            content = d.decompress(content, MAX_XML_BYTES)
        except zlib.error:
            raise HTTPException(status_code=400, detail="Invalid gzip file")
        if d.unconsumed_tail:
            raise HTTPException(status_code=413, detail="Decompressed report too large")
    try:
        xml_string = content.decode('utf-8')
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Report must be UTF-8 XML")
    # DMARC aggregate reports never carry a DTD; refusing one blocks XXE and entity expansion outright
    if _DOCTYPE.search(xml_string):
        raise HTTPException(status_code=400, detail="DTDs are not allowed in reports")
    return xml_string

@router.post("/upload-report")
@user_limiter.limit("5/minute")
async def upload_dmarc_report(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    filename = (file.filename or "").lower()
    if not filename.endswith(('.xml', '.gz')):
        raise HTTPException(status_code=400, detail="Invalid file type")

    file_content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(file_content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File too large")

    xml_string = _decode_report(filename, file_content)
    try:
        report_id = dmarc_service.ingest_report(xml_string, current_user.customer_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Could not parse DMARC report")

    ErrorSanitizer.log_security_event(
        "file_upload_success",
        {"user_id": current_user.email, "report_id": report_id, "file_size": len(file_content)}
    )
    return {
        "message": "DMARC report uploaded and processed successfully",
        "report_id": report_id
    }

@router.get("/summary", response_model=DMARCReportSummary)
@user_limiter.limit("30/minute")
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