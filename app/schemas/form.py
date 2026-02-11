from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class FormCreate(BaseModel):
    name: str
    description: Optional[str] = None
    file_url: str

class FormResponse(BaseModel):
    id: int
    workspace_id: int
    name: str
    description: Optional[str]
    file_url: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class FormSubmissionResponse(BaseModel):
    id: int
    booking_id: int
    form_id: int
    status: str
    submission_url: Optional[str]
    due_date: datetime
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True