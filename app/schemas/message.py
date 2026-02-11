from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class MessageType(str, Enum):
    EMAIL = "email"
    SMS = "sms"


class MessageDirection(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class MessageBase(BaseModel):
    type: MessageType
    direction: MessageDirection
    subject: Optional[str] = None  # For emails
    content: str = Field(..., min_length=1)
    is_automated: bool = False


class MessageSend(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)
    subject: Optional[str] = Field(None, max_length=200)  # For emails
    type: Optional[MessageType] = None  # Auto-determined from contact preferences


class MessageResponse(MessageBase):
    id: int
    conversation_id: int
    sent_by_user_id: Optional[int] = None
    external_id: Optional[str] = None  # SendGrid/Twilio message ID
    status: str = "sent"
    created_at: datetime
    
    # Optional user info for display
    sent_by_user: Optional[dict] = None
    
    class Config:
        from_attributes = True