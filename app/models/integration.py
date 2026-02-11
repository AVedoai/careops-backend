from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, JSON, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Integration(Base):
    __tablename__ = "integrations"
    
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    type = Column(String, nullable=False)  # email, sms, calendar
    provider = Column(String, nullable=False)  # sendgrid, twilio, google
    credentials = Column(JSON, nullable=False)  # Encrypted credentials
    is_active = Column(Boolean, default=True)
    last_tested_at = Column(DateTime, nullable=True)
    test_status = Column(String, nullable=True)  # success, failed
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    workspace = relationship("Workspace", back_populates="integrations")