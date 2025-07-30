"""
Session activity tracking middleware
"""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from ..services.session_service import session_service
import logging

logger = logging.getLogger("security")

class SessionActivityMiddleware(BaseHTTPMiddleware):
    """Middleware to track session activity and update session information"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Only track activity for authenticated requests
        if hasattr(request.state, 'token') and request.state.token:
            try:
                # Get client information
                client_ip = self._get_client_ip(request)
                user_agent = request.headers.get("user-agent", "Unknown")
                
                # Update session activity
                session_service.update_session_activity(
                    request.state.token,
                    client_ip,
                    user_agent
                )
                
            except Exception as e:
                logger.warning(f"Failed to update session activity: {e}")
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """
        Get the real client IP address considering proxies
        """
        # Check for common proxy headers
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Take the first IP in case of multiple proxies
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip.strip()
        
        # Fall back to direct connection
        if hasattr(request.client, 'host'):
            return request.client.host
        
        return "unknown"