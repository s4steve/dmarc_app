from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ..models.user import UserLogin, Token, User
from ..services.user_service import user_service
from ..services.session_service import session_service
from ..core.security import create_access_token, verify_token, _unauthorized
from ..middleware.rate_limiter import limiter, user_limiter

router = APIRouter()
security = HTTPBearer()

@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
async def login(request: Request, user_credentials: UserLogin):
    user = await user_service.authenticate_user(user_credentials.email, user_credentials.password)
    if not user or not user.is_active:
        raise _unauthorized("Incorrect email or password")
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    payload = verify_token(credentials.credentials)
    email = payload.get("sub")
    # Look the user up on every request so role changes and deactivation apply immediately
    user = await user_service.get_user_by_email(email) if email else None
    if not user:
        raise _unauthorized()
    # Store token in request state for session activity tracking
    request.state.token = credentials.credentials
    request.state.user_email = user.email
    return User(**user.model_dump(exclude={"hashed_password"}))

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise _unauthorized()
    return current_user

def require_admin(current_user: User = Depends(get_current_active_user)) -> User:
    if current_user.role not in ["admin", "system_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

def require_system_admin(current_user: User = Depends(get_current_active_user)) -> User:
    if current_user.role != "system_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="System administrator access required"
        )
    return current_user

@router.post("/logout")
@limiter.limit("10/minute")
async def logout(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: User = Depends(get_current_active_user)
):
    session_service.blacklist_token(credentials.credentials, current_user.email, "logout")
    return {"message": "Successfully logged out"}

@router.post("/logout-all")
@limiter.limit("5/minute")
async def logout_all_sessions(
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    session_service.invalidate_all_user_sessions(current_user.email, "logout_all")
    return {"message": "Successfully logged out from all sessions"}

@router.get("/sessions")
@user_limiter.limit("20/minute")
async def get_active_sessions(
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    sessions = [
        {
            "created_at": s.get("created_at"),
            "last_accessed": s.get("last_accessed"),
            "ip_address": s.get("ip_address") or "Unknown",
            "user_agent": (s.get("user_agent") or "Unknown")[:100]
        }
        for s in session_service.get_user_sessions(current_user.email)
    ]
    return {"active_sessions": sessions, "total_count": len(sessions)}
