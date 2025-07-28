from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from ..models.user import User, UserCreate, UserUpdate
from ..services.user_service import user_service
from .auth import get_current_active_user, require_admin

router = APIRouter()

@router.post("/", response_model=User)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_admin)
):
    existing_user = await user_service.get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="User with this email already exists"
        )
    
    if current_user.role != "system_admin":
        user_data.customer_id = current_user.customer_id
    
    try:
        new_user = await user_service.create_user(user_data)
        return new_user
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/me", response_model=User)
async def get_current_user_profile(current_user: User = Depends(get_current_active_user)):
    return current_user

@router.get("/", response_model=List[User])
async def get_users(
    current_user: User = Depends(require_admin)
):
    try:
        if current_user.role == "system_admin":
            users = await user_service.get_users_by_customer("")
        else:
            users = await user_service.get_users_by_customer(current_user.customer_id)
        return users
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{user_id}", response_model=User)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: User = Depends(require_admin)
):
    user_to_update = await user_service.get_user_by_id(user_id)
    if not user_to_update:
        raise HTTPException(status_code=404, detail="User not found")
    
    if current_user.role != "system_admin" and user_to_update.customer_id != current_user.customer_id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    try:
        updated_user = await user_service.update_user(user_id, user_update)
        if not updated_user:
            raise HTTPException(status_code=404, detail="User not found")
        return updated_user
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(require_admin)
):
    user_to_delete = await user_service.get_user_by_id(user_id)
    if not user_to_delete:
        raise HTTPException(status_code=404, detail="User not found")
    
    if current_user.role != "system_admin" and user_to_delete.customer_id != current_user.customer_id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    if user_to_delete.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    try:
        success = await user_service.delete_user(user_id)
        if not success:
            raise HTTPException(status_code=404, detail="User not found")
        return {"message": "User deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))