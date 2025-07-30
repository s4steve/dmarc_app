"""
Security Headers Middleware for comprehensive HTTP security
"""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict, Optional
from ..core.config import settings

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add comprehensive security headers to all responses
    """
    
    def __init__(self, app, config: Optional[Dict] = None):
        super().__init__(app)
        self.config = config or {}
        
        # Default security headers configuration
        self.default_headers = {
            # Prevent MIME type sniffing
            "X-Content-Type-Options": "nosniff",
            
            # Enable XSS protection
            "X-XSS-Protection": "1; mode=block",
            
            # Prevent clickjacking attacks
            "X-Frame-Options": "DENY",
            
            # Control referrer information
            "Referrer-Policy": "strict-origin-when-cross-origin",
            
            # Prevent loading over HTTP when HTTPS is available
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
            
            # Content Security Policy - restrictive default
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' https:; "
                "connect-src 'self'; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self';"
            ),
            
            # Permissions Policy (formerly Feature Policy)
            "Permissions-Policy": (
                "camera=(), "
                "microphone=(), "
                "geolocation=(), "
                "payment=(), "
                "usb=(), "
                "magnetometer=(), "
                "gyroscope=(), "
                "accelerometer=(), "
                "ambient-light-sensor=(), "
                "autoplay=(), "
                "display-capture=(), "
                "document-domain=(), "
                "encrypted-media=(), "
                "fullscreen=(), "
                "picture-in-picture=()"
            ),
            
            # Prevent DNS prefetching (privacy)
            "X-DNS-Prefetch-Control": "off",
            
            # Disable download of executable content
            "X-Download-Options": "noopen",
            
            # Prevent Flash/PDF from loading
            "X-Permitted-Cross-Domain-Policies": "none",
            
            # Cache control for sensitive pages
            "Cache-Control": "no-cache, no-store, must-revalidate, private",
            "Pragma": "no-cache",
            "Expires": "0"
        }
        
        # Merge with custom config if provided
        self.headers = {**self.default_headers, **self.config}
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add security headers to all responses
        for header_name, header_value in self.headers.items():
            # Don't override existing headers unless explicitly configured
            if header_name not in response.headers or self.config.get(header_name):
                response.headers[header_name] = header_value
        
        # Special handling for API documentation endpoints
        if request.url.path in ["/docs", "/redoc", "/openapi.json"]:
            # Relax CSP for documentation
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "img-src 'self' data: https:; "
                "font-src 'self' https: data:; "
                "connect-src 'self';"
            )
        
        # Remove server information for security
        if "server" in response.headers:
            del response.headers["server"]
        
        # Add custom server header (optional obfuscation)
        response.headers["Server"] = "DMARC-Analytics/1.0"
        
        return response

def get_security_headers_config() -> Dict:
    """
    Get security headers configuration based on environment
    """
    config = {}
    
    # Production-specific configurations
    if getattr(settings, 'ENVIRONMENT', 'development') == 'production':
        config.update({
            # Stricter CSP for production
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self'; "
                "style-src 'self'; "
                "img-src 'self' data: https:; "
                "font-src 'self'; "
                "connect-src 'self'; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self';"
            ),
            
            # Enforce HTTPS in production
            "Strict-Transport-Security": "max-age=63072000; includeSubDomains; preload"
        })
    
    # Development-specific configurations
    else:
        config.update({
            # More relaxed for development
            "Strict-Transport-Security": "max-age=0",  # Disable HSTS in dev
        })
    
    return config