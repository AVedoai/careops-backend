from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
from datetime import datetime

class ContactCreate(BaseModel):
    full_name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    message: Optional[str] = None
    preferred_channel: str = "email"

class ContactUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    preferred_channel: Optional[str] = None

class ContactFormSubmission(BaseModel):
    full_name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    message: Optional[str] = None

class ContactFormSubmissionAdvanced(BaseModel):
    form_id: int
    data: Dict[str, Any]
    contact_id: Optional[int] = None

class ContactResponse(BaseModel):
    id: int
    workspace_id: int
    full_name: str
    email: Optional[str]
    phone: Optional[str]
    preferred_channel: str
    created_at: datetime
    
    class Config:
        from_attributes = True