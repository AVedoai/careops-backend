from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime, Date, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
from enum import Enum

class FormType(str, Enum):
    CUSTOM = "CUSTOM"
    DOCUMENT = "DOCUMENT"  # Legacy PDF forms
    EXTERNAL_LINK = "EXTERNAL_LINK"  # Google Forms, Typeform, etc.

class SubmissionStatus(str, Enum):
    NEW = "NEW"
    REVIEWED = "REVIEWED" 
    CONTACTED = "CONTACTED"
    CONVERTED = "CONVERTED"

class LeadStatus(str, Enum):
    NEW = "NEW"
    CONTACTED = "CONTACTED"
    QUALIFIED = "QUALIFIED"
    CONVERTED = "CONVERTED"
    LOST = "LOST"

class Form(Base):
    __tablename__ = "forms"
    
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    type = Column(String, default=FormType.DOCUMENT)  # CUSTOM, DOCUMENT, EXTERNAL_LINK
    
    # For document forms (legacy)
    file_url = Column(String, nullable=True)
    
    # For external forms (Google Forms, Typeform, etc.)
    external_url = Column(String, nullable=True)
    
    # For custom form builder
    fields = Column(JSON, nullable=True)  # Form field configuration
    settings = Column(JSON, nullable=True)  # Form settings (notifications, redirects, etc.)
    
    is_active = Column(Boolean, default=True)
    is_published = Column(Boolean, default=False)
    share_link = Column(String, nullable=True, unique=True)  # Public shareable link
    embed_code = Column(Text, nullable=True)  # HTML embed code
    views_count = Column(Integer, default=0)
    submissions_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    workspace = relationship("Workspace", back_populates="forms")
    creator = relationship("User", foreign_keys=[created_by])
    service_forms = relationship("ServiceForm", back_populates="form", cascade="all, delete-orphan")
    custom_submissions = relationship("CustomFormSubmission", back_populates="form", cascade="all, delete-orphan")
    form_submissions = relationship("FormSubmission", back_populates="form", cascade="all, delete-orphan")

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
    """Legacy form submissions for document-based forms"""
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
    form = relationship("Form", back_populates="form_submissions")

class CustomFormSubmission(Base):
    """Submissions for custom form builder forms"""
    __tablename__ = "custom_form_submissions"
    
    id = Column(Integer, primary_key=True, index=True)
    form_id = Column(Integer, ForeignKey("forms.id"), nullable=False)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    submitted_data = Column(JSON, nullable=False)  # All form answers in JSONB
    submitter_email = Column(String, nullable=True, index=True)
    submitter_name = Column(String, nullable=True)
    submitter_phone = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    status = Column(String, default=SubmissionStatus.NEW)
    is_read = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    converted_to_booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    form = relationship("Form", back_populates="custom_submissions")
    workspace = relationship("Workspace")
    assigned_user = relationship("User", foreign_keys=[assigned_to])
    converted_booking = relationship("Booking", foreign_keys=[converted_to_booking_id])
    lead = relationship("Lead", back_populates="form_submission", uselist=False)

class Lead(Base):
    """Lead management for form submissions"""
    __tablename__ = "leads"
    
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    form_submission_id = Column(Integer, ForeignKey("custom_form_submissions.id"), nullable=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=True, index=True)
    phone = Column(String, nullable=True)
    source = Column(String, default="FORM")  # FORM, EMAIL, SMS, MANUAL
    status = Column(String, default=LeadStatus.NEW)
    score = Column(Integer, default=0)  # Lead scoring 0-100
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    last_contacted = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    workspace = relationship("Workspace")
    form_submission = relationship("CustomFormSubmission", back_populates="lead")
    assigned_user = relationship("User", foreign_keys=[assigned_to])