from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date, time, datetime

class BookingCreate(BaseModel):
    service_id: int
    booking_date: date
    booking_time: time
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    notes: Optional[str] = None

class PublicBookingCreate(BaseModel):
    service_slug: str  # Using service slug instead of ID for public API
    booking_date: date
    booking_time: time
    full_name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    notes: Optional[str] = None

class BookingUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None

class BookingResponse(BaseModel):
    id: int
    workspace_id: int
    contact_id: int
    service_id: int
    booking_date: date
    booking_time: time
    status: str
    notes: Optional[str]
    confirmation_sent_at: Optional[datetime]
    reminder_sent_at: Optional[datetime]
    forms_sent_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True