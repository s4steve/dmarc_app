from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import redis.asyncio as redis
from ..core.config import settings

# Create Redis connection for rate limiting
def get_redis_connection():
    """Get Redis connection for rate limiting"""
    try:
        return redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
    except Exception:
        # Fallback to memory-based rate limiting if Redis is not available
        return None

# Create limiter instance
def get_rate_limiter():
    """Create rate limiter with Redis backend or in-memory fallback"""
    redis_url = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
    
    try:
        # Try Redis backend first
        limiter = Limiter(
            key_func=get_remote_address,
            storage_uri=redis_url,
            default_limits=["100/hour"]  # Default global limit
        )
        return limiter
    except Exception:
        # Fallback to in-memory rate limiting
        from slowapi.middleware import SlowAPIMiddleware
        limiter = Limiter(
            key_func=get_remote_address,
            default_limits=["100/hour"]
        )
        return limiter

# Initialize the limiter
limiter = get_rate_limiter()

async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Custom rate limit exceeded handler"""
    response_data = {
        "error": "rate_limit_exceeded",
        "detail": "Too many requests. Please try again later.",
        "retry_after": getattr(exc, 'retry_after', 60)  # Default to 60 seconds if not available
    }
    
    # Log the rate limit violation for security monitoring
    import logging
    logger = logging.getLogger("security")
    retry_after = getattr(exc, 'retry_after', 60)
    logger.warning(
        f"Rate limit exceeded for IP {request.client.host} "
        f"on path {request.url.path} - retry after {retry_after}s"
    )
    
    return JSONResponse(
        status_code=429,
        content=response_data,
        headers={"Retry-After": str(retry_after)}
    )

def get_authenticated_user_key(request: Request):
    """
    Rate limiting key function that considers both IP and authenticated user
    This provides more granular rate limiting for authenticated requests
    """
    client_ip = get_remote_address(request)
    
    # Try to get user info from Authorization header
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.startswith("Bearer "):
        # For authenticated requests, use a combination of IP and token hash
        token = auth_header.split(" ")[1]
        # Use first 8 characters of token for rate limiting key
        user_identifier = token[:8] if len(token) >= 8 else token
        return f"{client_ip}:{user_identifier}"
    
    # For unauthenticated requests, use just IP
    return client_ip

# Create user-based limiter for authenticated endpoints
try:
    user_limiter = Limiter(
        key_func=get_authenticated_user_key,
        storage_uri=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}",
        default_limits=["200/hour"]  # Higher limit for authenticated users
    )
except Exception:
    # Fallback to in-memory rate limiting if Redis is not available
    user_limiter = Limiter(
        key_func=get_authenticated_user_key,
        default_limits=["200/hour"]
    )