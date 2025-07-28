from pydantic import BaseModel, EmailStr
from typing import Optional
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    READ_ONLY = "read_only"
    SYSTEM_ADMIN = "system_admin"

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    role: UserRole = UserRole.READ_ONLY
    is_active: bool = True

class UserCreate(UserBase):
    password: str
    customer_id: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None

class UserInDB(UserBase):
    id: str
    customer_id: str
    hashed_password: str
    created_at: str
    updated_at: str

class User(UserBase):
    id: str
    customer_id: str
    created_at: str
    updated_at: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    email: Optional[str] = None
    customer_id: Optional[str] = None
    role: Optional[str] = None