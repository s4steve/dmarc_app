import hashlib
import logging
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse
from ..core.config import settings

logger = logging.getLogger("security")

# IP-keyed limiter for unauthenticated endpoints (login)
limiter = Limiter(key_func=get_remote_address, storage_uri=settings.REDIS_URL)

async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Custom rate limit exceeded handler"""
    retry_after = getattr(exc, 'retry_after', 60)
    client_ip = request.client.host if request.client else "unknown"
    logger.warning(
        f"Rate limit exceeded for IP {client_ip} "
        f"on path {request.url.path} - retry after {retry_after}s"
    )
    return JSONResponse(
        status_code=429,
        content={
            "error": "rate_limit_exceeded",
            "detail": "Too many requests. Please try again later.",
            "retry_after": retry_after
        },
        headers={"Retry-After": str(retry_after)}
    )

def get_authenticated_user_key(request: Request):
    """Key on IP plus a hash of the bearer token, so each session gets its own bucket"""
    client_ip = get_remote_address(request)
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
        return f"{client_ip}:{hashlib.sha256(token.encode()).hexdigest()[:16]}"
    return client_ip

user_limiter = Limiter(key_func=get_authenticated_user_key, storage_uri=settings.REDIS_URL)
