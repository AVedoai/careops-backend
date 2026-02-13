from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=72, description="Password must be 6-72 characters long")
    full_name: str = Field(..., min_length=1, max_length=100, description="Full name is required")
    business_name: str = Field(..., min_length=1, max_length=100, description="Business name is required")
    
    @field_validator('password')
    def validate_password(cls, v):
        if len(v.encode('utf-8')) > 72:
            raise ValueError('Password is too long. Maximum length is 72 bytes.')
        return v

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