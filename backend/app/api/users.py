from fastapi import APIRouter, Depends, HTTPException
from typing import List
from ..models.user import User, UserCreate, UserUpdate, UserRole
from ..services.user_service import user_service
from .auth import get_current_active_user, require_admin

router = APIRouter()

def _check_can_manage(current_user: User, target: User) -> None:
    """Tenant admins may only manage non-system-admin users in their own customer"""
    if current_user.role == UserRole.SYSTEM_ADMIN:
        return
    if target.customer_id != current_user.customer_id or target.role == UserRole.SYSTEM_ADMIN:
        raise HTTPException(status_code=403, detail="Not enough permissions")

def _check_can_assign(current_user: User, role) -> None:
    if role == UserRole.SYSTEM_ADMIN and current_user.role != UserRole.SYSTEM_ADMIN:
        raise HTTPException(status_code=403, detail="Not enough permissions")

@router.post("/", response_model=User)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_admin)
):
    _check_can_assign(current_user, user_data.role)
    if await user_service.get_user_by_email(user_data.email):
        raise HTTPException(status_code=400, detail="User with this email already exists")
    if current_user.role != UserRole.SYSTEM_ADMIN:
        user_data.customer_id = current_user.customer_id
    return await user_service.create_user(user_data)

@router.get("/me", response_model=User)
async def get_current_user_profile(current_user: User = Depends(get_current_active_user)):
    return current_user

@router.get("/", response_model=List[User])
async def get_users(current_user: User = Depends(require_admin)):
    if current_user.role == UserRole.SYSTEM_ADMIN:
        return await user_service.get_users_by_customer("")
    return await user_service.get_users_by_customer(current_user.customer_id)

@router.put("/{user_id}", response_model=User)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: User = Depends(require_admin)
):
    user_to_update = await user_service.get_user_by_id(user_id)
    if not user_to_update:
        raise HTTPException(status_code=404, detail="User not found")
    _check_can_manage(current_user, user_to_update)
    _check_can_assign(current_user, user_update.role)
    updated_user = await user_service.update_user(user_id, user_update)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user

@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(require_admin)
):
    user_to_delete = await user_service.get_user_by_id(user_id)
    if not user_to_delete:
        raise HTTPException(status_code=404, detail="User not found")
    _check_can_manage(current_user, user_to_delete)
    if user_to_delete.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    if not await user_service.delete_user(user_id):
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}
