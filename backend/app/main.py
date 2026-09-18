from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager
import logging
from slowapi.errors import RateLimitExceeded
from .core.config import settings
from .services.elasticsearch import es_service
from .services.user_service import user_service
from .models.user import UserCreate, UserRole
from .middleware.rate_limiter import limiter, rate_limit_exceeded_handler
from .middleware.security_headers import SecurityHeadersMiddleware, get_security_headers_config
from .middleware.session_middleware import SessionActivityMiddleware
from .middleware.error_handlers import (
    general_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    starlette_http_exception_handler
)
from .api import auth, dmarc, users, services, dns, alerts, configuration, notifications, analytics, dns_scanner, domains

@asynccontextmanager
async def lifespan(app: FastAPI):
    es_service.create_indices()
    await bootstrap_admin()
    yield

async def bootstrap_admin():
    """Create the first system admin from ADMIN_EMAIL/ADMIN_PASSWORD when no users exist"""
    if not (settings.ADMIN_EMAIL and settings.ADMIN_PASSWORD):
        return
    users_index = f"{settings.ELASTICSEARCH_INDEX_PREFIX}-users"
    if es_service.client.count(index=users_index)["count"] > 0:
        return
    await user_service.create_user(UserCreate(
        email=settings.ADMIN_EMAIL,
        password=settings.ADMIN_PASSWORD,
        full_name="System Administrator",
        role=UserRole.SYSTEM_ADMIN,
        customer_id="default",
    ))
    # Make the account searchable immediately instead of after the 30s refresh interval
    es_service.client.indices.refresh(index=users_index)
    logging.getLogger("security").warning(f"Bootstrapped system admin {settings.ADMIN_EMAIL}")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Reject oversized bodies before Starlette spools them to disk.
# ponytail: trusts Content-Length; chunked bodies skip this, so cap body size at the reverse proxy too.
MAX_BODY_BYTES = 11 * 1024 * 1024

@app.middleware("http")
async def limit_body_size(request: Request, call_next):
    content_length = request.headers.get("content-length", "")
    if content_length.isdigit() and int(content_length) > MAX_BODY_BYTES:
        return JSONResponse(status_code=413, content={"detail": "Request body too large"})
    return await call_next(request)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# Add security middleware (order matters - security headers should be last)
app.add_middleware(SessionActivityMiddleware)
app.add_middleware(SecurityHeadersMiddleware, config=get_security_headers_config())

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add global exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, starlette_http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(dmarc.router, prefix=f"{settings.API_V1_STR}/dmarc", tags=["dmarc"])
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["users"])
app.include_router(services.router, prefix=f"{settings.API_V1_STR}/services", tags=["services"])
app.include_router(dns.router, prefix=f"{settings.API_V1_STR}/dns", tags=["dns"])
app.include_router(alerts.router, prefix=f"{settings.API_V1_STR}/alerts", tags=["alerts"])
app.include_router(configuration.router, prefix=f"{settings.API_V1_STR}/configuration", tags=["configuration"])
app.include_router(notifications.router, prefix=f"{settings.API_V1_STR}/notifications", tags=["notifications"])
app.include_router(analytics.router, prefix=f"{settings.API_V1_STR}/analytics", tags=["analytics"])
app.include_router(dns_scanner.router, prefix=f"{settings.API_V1_STR}/dns-scanner", tags=["dns-scanner"])
app.include_router(domains.router, prefix=f"{settings.API_V1_STR}/domains", tags=["domains"])

@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "version": settings.VERSION,
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)