from pydantic import BaseModel, EmailStr
from typing import Optional

class WorkspaceUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    timezone: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None

class WorkspaceResponse(BaseModel):
    id: int
    name: str
    slug: str
    address: Optional[str]
    timezone: str
    contact_email: str
    contact_phone: Optional[str]
    is_active: bool
    onboarding_completed: bool
    onboarding_step: int
    
    class Config:
        from_attributes = True

class OnboardingStepUpdate(BaseModel):
    step: int
    data: dict