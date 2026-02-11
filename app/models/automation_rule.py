from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, JSON, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class AutomationRule(Base):
    __tablename__ = "automation_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    
    name = Column(String, nullable=False)
    event_type = Column(String, nullable=False)  # contact_created, booking_created, etc
    action_type = Column(String, nullable=False)  # send_email, send_sms, create_alert
    
    # Configuration for the action (template, timing, etc)
    config = Column(JSON, nullable=False, default={})
    
    is_active = Column(Boolean, default=True)
    execution_count = Column(Integer, default=0)
    last_executed_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    workspace = relationship("Workspace", back_populates="automation_rules")