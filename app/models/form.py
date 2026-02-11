from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime, Date
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Form(Base):
    __tablename__ = "forms"
    
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    file_url = Column(String, nullable=False)  # URL to PDF/document
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    workspace = relationship("Workspace", back_populates="forms")
    service_forms = relationship("ServiceForm", back_populates="form", cascade="all, delete-orphan")

class ServiceForm(Base):
    """Links forms to services (many-to-many)"""
    __tablename__ = "service_forms"
    
    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)
    form_id = Column(Integer, ForeignKey("forms.id"), nullable=False)
    order = Column(Integer, default=0)  # Order in which forms should be sent
    
    # Relationships
    service = relationship("Service", back_populates="service_forms")
    form = relationship("Form", back_populates="service_forms")

class FormSubmission(Base):
    __tablename__ = "form_submissions"
    
    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=False)
    form_id = Column(Integer, ForeignKey("forms.id"), nullable=False)
    
    status = Column(String, default="pending")  # pending, completed, overdue
    submission_url = Column(String, nullable=True)  # URL where customer can fill form
    completed_url = Column(String, nullable=True)  # URL of completed form
    due_date = Column(Date, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    reminder_sent_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    booking = relationship("Booking", back_populates="form_submissions")