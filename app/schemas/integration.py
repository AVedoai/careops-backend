from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class IntegrationType(str, Enum):
    SENDGRID = "sendgrid"
    TWILIO = "twilio"
    GOOGLE_CALENDAR = "google_calendar"


class IntegrationStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"


class IntegrationBase(BaseModel):
    type: IntegrationType
    display_name: str = Field(..., min_length=1, max_length=100)
    settings: Dict[str, Any] = {}
    is_active: bool = True


class IntegrationCreate(IntegrationBase):
    pass


class IntegrationUpdate(BaseModel):
    display_name: Optional[str] = Field(None, min_length=1, max_length=100)
    settings: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class IntegrationResponse(IntegrationBase):
    id: int
    workspace_id: int
    status: IntegrationStatus
    last_sync_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
from typing import Optional, Dict, Any
from datetime import datetime

class IntegrationCreate(BaseModel):
    type: str  # email, sms, calendar
    provider: str  # sendgrid, twilio, google
    credentials: Dict[str, Any]

class IntegrationResponse(BaseModel):
    id: int
    workspace_id: int
    type: str
    provider: str
    is_active: bool
    last_tested_at: Optional[datetime]
    test_status: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True