from sqlalchemy import Column, Integer, String, ForeignKey, Text, JSON, Boolean
from sqlalchemy.orm import relationship
from app.database import Base

class Service(Base):
    __tablename__ = "services"
    
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    name = Column(String, nullable=False)
    slug = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    duration_minutes = Column(Integer, nullable=False)
    location = Column(String, nullable=True)
    
    # Availability stored as JSON
    # Format: {"monday": ["09:00-12:00", "13:00-17:00"], "tuesday": [], ...}
    availability = Column(JSON, nullable=False, default={})
    
    is_active = Column(Boolean, default=True)
    
    # Relationships
    workspace = relationship("Workspace", back_populates="services")
    bookings = relationship("Booking", back_populates="service", cascade="all, delete-orphan")
    service_forms = relationship("ServiceForm", back_populates="service", cascade="all, delete-orphan")