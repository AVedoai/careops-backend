from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class ServiceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    duration_minutes: int = Field(..., gt=0, le=480)  # Max 8 hours
    location: Optional[str] = None
    availability: Optional[Dict[str, Any]] = None
    is_active: bool = True


class ServiceCreate(ServiceBase):
    pass


class ServiceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    duration_minutes: Optional[int] = Field(None, gt=0, le=480)
    location: Optional[str] = None
    availability: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class ServiceResponse(ServiceBase):
    id: int
    slug: str
    workspace_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True