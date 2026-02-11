from pydantic import BaseModel, EmailStr
from typing import Optional

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    business_name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    workspace_id: Optional[int]
    can_manage_inbox: bool
    can_manage_bookings: bool
    can_view_forms: bool
    can_view_inventory: bool
    
    class Config:
        from_attributes = True

class StaffInvite(BaseModel):
    email: EmailStr
    full_name: str
    can_manage_inbox: bool = True
    can_manage_bookings: bool = True
    can_view_forms: bool = True
    can_view_inventory: bool = False