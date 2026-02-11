from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime, Text, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base

class AlertType(str, enum.Enum):
    INVENTORY_LOW = "inventory_low"
    FORM_OVERDUE = "form_overdue"
    BOOKING_UNCONFIRMED = "booking_unconfirmed"
    MESSAGE_UNANSWERED = "message_unanswered"
    SYSTEM_ERROR = "system_error"

class AlertStatus(str, enum.Enum):
    ACTIVE = "active"
    DISMISSED = "dismissed"
    RESOLVED = "resolved"

class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    
    type = Column(Enum(AlertType), nullable=False)
    status = Column(Enum(AlertStatus), default=AlertStatus.ACTIVE, nullable=False)
    severity = Column(String, default="medium")  # low, medium, high, critical
    
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    link = Column(String, nullable=True)  # Link to relevant page
    
    # Reference to related entity
    reference_type = Column(String, nullable=True)  # booking, inventory_item, form_submission
    reference_id = Column(Integer, nullable=True)
    
    dismissed_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    workspace = relationship("Workspace", back_populates="alerts")