from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base

class UserRole(str, enum.Enum):
    OWNER = "owner"
    STAFF = "staff"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.STAFF, nullable=False)
    is_active = Column(Boolean, default=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=True)
    
    # Permissions for staff
    can_manage_inbox = Column(Boolean, default=True)
    can_manage_bookings = Column(Boolean, default=True)
    can_view_forms = Column(Boolean, default=True)
    can_view_inventory = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    workspace = relationship("Workspace", back_populates="users")
    sent_messages = relationship("Message", back_populates="sent_by_user")