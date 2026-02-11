from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Date, Time, Enum, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base

class BookingStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"

class Booking(Base):
    __tablename__ = "bookings"
    
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)
    
    booking_date = Column(Date, nullable=False, index=True)
    booking_time = Column(Time, nullable=False)
    status = Column(Enum(BookingStatus), default=BookingStatus.CONFIRMED, nullable=False)
    notes = Column(Text, nullable=True)
    
    # Tracking
    confirmation_sent_at = Column(DateTime, nullable=True)
    reminder_sent_at = Column(DateTime, nullable=True)
    forms_sent_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    contact = relationship("Contact", back_populates="bookings")
    service = relationship("Service", back_populates="bookings")
    form_submissions = relationship("FormSubmission", back_populates="booking", cascade="all, delete-orphan")