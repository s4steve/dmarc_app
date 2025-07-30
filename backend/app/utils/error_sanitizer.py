"""
Error message sanitization utilities to prevent information disclosure
"""
import re
import traceback
from typing import Any, Dict, Optional
from fastapi import HTTPException
from ..core.config import settings
import logging

logger = logging.getLogger("security")

class ErrorSanitizer:
    """Utility class for sanitizing error messages and preventing information disclosure"""
    
    # Patterns that should be removed from error messages
    SENSITIVE_PATTERNS = [
        # Database connection strings
        r'postgresql://[^@]+@[^/]+/\w+',
        r'mysql://[^@]+@[^/]+/\w+',
        r'mongodb://[^@]+@[^/]+/\w+',
        
        # File paths
        r'/[a-zA-Z0-9_\-/\.]+\.py',
        r'\\[a-zA-Z0-9_\-\\\.]+\.py',
        r'/home/[^/]+/[^\s]+',
        r'/var/[^\s]+',
        r'/etc/[^\s]+',
        
        # IP addresses and internal hostnames
        r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
        r'\b[a-zA-Z0-9\-]+\.internal\b',
        r'\blocalhost\b',
        
        # Stack trace information
        r'File "[^"]+", line \d+',
        r'Traceback \(most recent call last\):',
        
        # Database table/column names
        r'table "[^"]+"',
        r'column "[^"]+"',
        r'constraint "[^"]+"',
        
        # Environment variables
        r'[A-Z_]+_KEY=[^\s]+',
        r'[A-Z_]+_PASSWORD=[^\s]+',
        r'[A-Z_]+_TOKEN=[^\s]+',
        
        # Version information
        r'Python \d+\.\d+\.\d+',
        r'FastAPI \d+\.\d+\.\d+',
        r'postgresql \d+\.\d+',
        
        # Memory addresses
        r'0x[a-fA-F0-9]+',
        
        # JWT tokens (partial)
        r'eyJ[a-zA-Z0-9\-_]+\.[a-zA-Z0-9\-_]+',
        
        # Internal service names
        r'elasticsearch-[a-zA-Z0-9\-]+',
        r'redis-[a-zA-Z0-9\-]+',
        r'dmarc-[a-zA-Z0-9\-]+',
    ]
    
    # Generic error messages for different error types
    GENERIC_MESSAGES = {
        "database": "A database error occurred. Please try again later.",
        "authentication": "Authentication failed. Please check your credentials.",
        "authorization": "You don't have permission to access this resource.",
        "validation": "The provided data is invalid.",
        "network": "A network error occurred. Please try again later.",
        "file": "A file processing error occurred.",
        "elasticsearch": "A search service error occurred. Please try again later.",
        "redis": "A caching service error occurred. Please try again later.",
        "internal": "An internal server error occurred. Please try again later.",
        "rate_limit": "Too many requests. Please slow down and try again later.",
        "timeout": "The request timed out. Please try again later.",
    }
    
    @classmethod
    def sanitize_error_message(cls, error_message: str, error_type: str = "internal") -> str:
        """
        Sanitize an error message to remove sensitive information
        
        Args:
            error_message: Original error message
            error_type: Type of error for generic message selection
            
        Returns:
            Sanitized error message
        """
        if not error_message:
            return cls.GENERIC_MESSAGES.get(error_type, cls.GENERIC_MESSAGES["internal"])
        
        # In production, use generic messages for most errors
        if getattr(settings, 'ENVIRONMENT', 'development') == 'production':
            return cls.GENERIC_MESSAGES.get(error_type, cls.GENERIC_MESSAGES["internal"])
        
        # In development, sanitize but keep some detail
        sanitized = error_message
        
        # Remove sensitive patterns
        for pattern in cls.SENSITIVE_PATTERNS:
            sanitized = re.sub(pattern, '[REDACTED]', sanitized, flags=re.IGNORECASE)
        
        # Limit message length
        if len(sanitized) > 200:
            sanitized = sanitized[:200] + "... [TRUNCATED]"
        
        return sanitized
    
    @classmethod
    def sanitize_exception(cls, exc: Exception, error_type: str = "internal") -> Dict[str, Any]:
        """
        Sanitize an exception and return safe error information
        
        Args:
            exc: Exception to sanitize
            error_type: Type of error for categorization
            
        Returns:
            Dictionary with sanitized error information
        """
        # Log the full error for debugging (but not to user)
        logger.error(f"Exception occurred: {type(exc).__name__}: {str(exc)}")
        if hasattr(exc, '__traceback__'):
            logger.debug("Full traceback:", exc_info=exc)
        
        # Determine error category
        exc_name = type(exc).__name__.lower()
        if any(db_term in exc_name for db_term in ['database', 'sql', 'connection']):
            error_type = "database"
        elif 'auth' in exc_name or 'permission' in exc_name:
            error_type = "authentication"
        elif 'validation' in exc_name or 'value' in exc_name:
            error_type = "validation"
        elif 'timeout' in exc_name:
            error_type = "timeout"
        elif 'network' in exc_name or 'connection' in exc_name:
            error_type = "network"
        
        # Create sanitized response
        sanitized_message = cls.sanitize_error_message(str(exc), error_type)
        
        return {
            "error": error_type,
            "message": sanitized_message,
            "type": type(exc).__name__ if getattr(settings, 'ENVIRONMENT', 'development') != 'production' else "ServerError"
        }
    
    @classmethod
    def create_http_exception(cls, 
                             status_code: int, 
                             detail: str, 
                             error_type: str = "internal",
                             headers: Optional[Dict[str, str]] = None) -> HTTPException:
        """
        Create an HTTPException with sanitized error message
        
        Args:
            status_code: HTTP status code
            detail: Error detail
            error_type: Type of error
            headers: Optional headers
            
        Returns:
            HTTPException with sanitized message
        """
        sanitized_detail = cls.sanitize_error_message(detail, error_type)
        
        return HTTPException(
            status_code=status_code,
            detail=sanitized_detail,
            headers=headers
        )
    
    @classmethod
    def log_security_event(cls, event_type: str, details: Dict[str, Any], user_id: Optional[str] = None):
        """
        Log security-related events for monitoring
        
        Args:
            event_type: Type of security event
            details: Event details
            user_id: Optional user ID
        """
        log_entry = {
            "event_type": event_type,
            "timestamp": logging.Formatter().formatTime(logging.LogRecord(
                name="security", level=logging.INFO, pathname="", lineno=0,
                msg="", args=(), exc_info=None
            )),
            "user_id": user_id,
            "details": details
        }
        
        # Log to security logger
        logger.warning(f"Security Event: {event_type}", extra=log_entry)
        
        # In production, this could also send to SIEM/monitoring system
        if getattr(settings, 'ENVIRONMENT', 'development') == 'production':
            # Example: send to monitoring service
            pass