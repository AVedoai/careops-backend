from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class MessageCreate(BaseModel):
    content: str
    type: str = "email"  # email or sms

class MessageSend(BaseModel):
    content: str
    subject: Optional[str] = None  # For emails
    type: Optional[str] = None  # Auto-determined from contact preferences

class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    type: str
    direction: str
    subject: Optional[str]
    content: str
    is_automated: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class ConversationResponse(BaseModel):
    id: int
    contact_id: int
    workspace_id: int
    status: str
    automation_paused: bool
    unread_count: int
    last_message_at: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True

class ConversationDetail(ConversationResponse):
    pass

class ConversationWithMessages(ConversationResponse):
    messages: List[MessageResponse]
    
    class Config:
        from_attributes = True