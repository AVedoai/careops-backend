from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base

class MessageType(str, enum.Enum):
    EMAIL = "email"
    SMS = "sms"

class MessageDirection(str, enum.Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    type = Column(Enum(MessageType), nullable=False)
    direction = Column(Enum(MessageDirection), nullable=False)
    subject = Column(String, nullable=True)  # For emails
    content = Column(Text, nullable=False)
    is_automated = Column(Boolean, default=False)
    sent_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    external_id = Column(String, nullable=True)  # SendGrid/Twilio message ID
    status = Column(String, default="sent")  # sent, delivered, failed
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    sent_by_user = relationship("User", back_populates="sent_messages")