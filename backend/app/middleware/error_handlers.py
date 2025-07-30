"""
Global exception handlers with error sanitization
"""
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from ..utils.error_sanitizer import ErrorSanitizer
import logging

logger = logging.getLogger("security")

async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle all uncaught exceptions with proper sanitization
    """
    
    # Log the actual error for debugging
    logger.error(f"Unhandled exception on {request.method} {request.url}: {type(exc).__name__}: {str(exc)}")
    
    # Get client information for security logging
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    # Log security event
    ErrorSanitizer.log_security_event(
        "unhandled_exception",
        {
            "exception_type": type(exc).__name__,
            "path": str(request.url.path),
            "method": request.method,
            "client_ip": client_ip,
            "user_agent": user_agent[:100] if user_agent else "unknown"
        }
    )
    
    # Sanitize the error
    sanitized_error = ErrorSanitizer.sanitize_exception(exc, "internal")
    
    return JSONResponse(
        status_code=500,
        content=sanitized_error
    )

async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handle HTTP exceptions with sanitization
    """
    
    # Log security-relevant HTTP errors
    if exc.status_code in [401, 403, 429]:
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        ErrorSanitizer.log_security_event(
            f"http_{exc.status_code}",
            {
                "path": str(request.url.path),
                "method": request.method,
                "client_ip": client_ip,
                "user_agent": user_agent[:100] if user_agent else "unknown",
                "original_detail": str(exc.detail)
            }
        )
    
    # Determine error type based on status code
    error_type = "internal"
    if exc.status_code == 400:
        error_type = "validation"
    elif exc.status_code == 401:
        error_type = "authentication"
    elif exc.status_code == 403:
        error_type = "authorization"
    elif exc.status_code == 429:
        error_type = "rate_limit"
    elif exc.status_code >= 500:
        error_type = "internal"
    
    # Sanitize the error message
    sanitized_detail = ErrorSanitizer.sanitize_error_message(str(exc.detail), error_type)
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": error_type,
            "message": sanitized_detail,
            "status_code": exc.status_code
        },
        headers=getattr(exc, 'headers', None)
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handle validation errors with sanitization
    """
    
    # Log validation errors for security monitoring
    client_ip = request.client.host if request.client else "unknown"
    
    ErrorSanitizer.log_security_event(
        "validation_error",
        {
            "path": str(request.url.path),
            "method": request.method,
            "client_ip": client_ip,
            "error_count": len(exc.errors()),
            "error_types": [error.get("type") for error in exc.errors()]
        }
    )
    
    # In production, don't expose detailed validation errors
    from ..core.config import settings
    if getattr(settings, 'ENVIRONMENT', 'development') == 'production':
        return JSONResponse(
            status_code=422,
            content={
                "error": "validation",
                "message": "The provided data is invalid.",
                "status_code": 422
            }
        )
    
    # In development, provide sanitized validation details
    sanitized_errors = []
    for error in exc.errors():
        sanitized_error = {
            "field": error.get("loc", ["unknown"])[-1],  # Get last field name
            "message": ErrorSanitizer.sanitize_error_message(error.get("msg", "Invalid value"), "validation"),
            "type": error.get("type", "unknown")
        }
        sanitized_errors.append(sanitized_error)
    
    return JSONResponse(
        status_code=422,
        content={
            "error": "validation",
            "message": "Validation errors occurred",
            "details": sanitized_errors,
            "status_code": 422
        }
    )

async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    Handle Starlette HTTP exceptions
    """
    
    # Convert to FastAPI HTTPException for consistent handling
    fastapi_exc = HTTPException(status_code=exc.status_code, detail=exc.detail)
    return await http_exception_handler(request, fastapi_exc)