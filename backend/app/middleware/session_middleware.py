"""
Session activity tracking middleware
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from ..services.session_service import session_service
import logging

logger = logging.getLogger("security")

class SessionActivityMiddleware(BaseHTTPMiddleware):
    """Record last-access time, IP and user agent for authenticated requests"""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        token = getattr(request.state, "token", None)
        email = getattr(request.state, "user_email", None)
        if token and email:
            try:
                # ponytail: direct peer IP only; X-Forwarded-For is client-controlled.
                # Use uvicorn --proxy-headers --forwarded-allow-ips when behind a trusted proxy.
                client_ip = request.client.host if request.client else None
                session_service.update_session_activity(
                    email, token, client_ip, request.headers.get("user-agent", "Unknown")[:200]
                )
            except Exception as e:
                logger.warning(f"Failed to update session activity: {e}")
        return response
