from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Workspace(Base):
    __tablename__ = "workspaces"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=False)
    address = Column(Text, nullable=True)
    timezone = Column(String, default="UTC")
    contact_email = Column(String, nullable=False)
    contact_phone = Column(String, nullable=True)
    
    # Onboarding status
    is_active = Column(Boolean, default=False)
    onboarding_completed = Column(Boolean, default=False)
    onboarding_step = Column(Integer, default=1)  # Track current step
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = relationship("User", back_populates="workspace")
    contacts = relationship("Contact", back_populates="workspace", cascade="all, delete-orphan")
    services = relationship("Service", back_populates="workspace", cascade="all, delete-orphan")
    integrations = relationship("Integration", back_populates="workspace", cascade="all, delete-orphan")
    forms = relationship("Form", back_populates="workspace", cascade="all, delete-orphan")
    inventory_items = relationship("InventoryItem", back_populates="workspace", cascade="all, delete-orphan")
    automation_rules = relationship("AutomationRule", back_populates="workspace", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="workspace", cascade="all, delete-orphan")