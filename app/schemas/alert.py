from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class AlertStatus(str, Enum):
    ACTIVE = "active"
    DISMISSED = "dismissed"
    RESOLVED = "resolved"


class AlertSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertBase(BaseModel):
    type: str = Field(..., min_length=1, max_length=100)
    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1)
    severity: AlertSeverity = AlertSeverity.MEDIUM
    link: Optional[str] = None
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None


class AlertCreate(AlertBase):
    pass


class AlertResponse(AlertBase):
    id: int
    workspace_id: int
    status: AlertStatus
    dismissed_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True