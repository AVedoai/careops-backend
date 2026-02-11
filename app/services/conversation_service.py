from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from typing import List, Dict, Any
from datetime import datetime
from app.models.conversation import Conversation
from app.models.message import Message, MessageType, MessageDirection
from app.models.contact import Contact
from app.schemas.conversation import MessageSend, ConversationDetail
from app.utils.exceptions import NotFoundException, ValidationException


class ConversationService:
    async def list_conversations(
        self,
        db: Session,
        workspace_id: int,
        skip: int = 0,
        limit: int = 100,
        status: str = "active"
    ) -> List[Conversation]:
        """List conversations for workspace"""
        query = db.query(Conversation).options(
            joinedload(Conversation.contact)
        ).filter(
            Conversation.workspace_id == workspace_id
        )
        
        if status != "all":
            query = query.filter(Conversation.status == status)
        
        return query.order_by(desc(Conversation.last_message_at)).offset(skip).limit(limit).all()
    
    async def get_conversation_detail(
        self,
        db: Session,
        conversation_id: int,
        workspace_id: int
    ) -> ConversationDetail:
        """Get conversation with messages"""
        conversation = db.query(Conversation).options(
            joinedload(Conversation.contact),
            joinedload(Conversation.messages).joinedload(Message.sent_by_user)
        ).filter(
            Conversation.id == conversation_id,
            Conversation.workspace_id == workspace_id
        ).first()
        
        if not conversation:
            raise NotFoundException("Conversation not found")
        
        # Mark as read
        if conversation.unread_count > 0:
            conversation.unread_count = 0
            db.commit()
        
        # Convert to response format
        return ConversationDetail(
            id=conversation.id,
            contact=conversation.contact,
            status=conversation.status,
            automation_paused=conversation.automation_paused,
            unread_count=conversation.unread_count,
            last_message_at=conversation.last_message_at,
            messages=sorted(conversation.messages, key=lambda m: m.created_at),
            created_at=conversation.created_at
        )
    
    async def send_message(
        self,
        db: Session,
        conversation_id: int,
        workspace_id: int,
        message_data: MessageSend,
        user_id: int
    ) -> Dict[str, Any]:
        """Send message in conversation"""
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.workspace_id == workspace_id
        ).first()
        
        if not conversation:
            raise NotFoundException("Conversation not found")
        
        # Determine message type based on contact's preferred channel
        contact = db.query(Contact).filter(Contact.id == conversation.contact_id).first()
        message_type = MessageType.EMAIL if contact.preferred_channel == "email" else MessageType.SMS
        
        # Create message record
        message = Message(
            conversation_id=conversation_id,
            type=message_type,
            direction=MessageDirection.OUTBOUND,
            subject=message_data.subject if message_type == MessageType.EMAIL else None,
            content=message_data.content,
            is_automated=False,
            sent_by_user_id=user_id,
            status="queued"  # Will be updated when actually sent
        )
        
        db.add(message)
        db.flush()  # Get message ID
        
        # Update conversation
        conversation.last_message_at = datetime.utcnow()
        conversation.automation_paused = True  # Pause automation when staff replies
        
        db.commit()
        db.refresh(message)
        
        # Queue actual message sending task
        # from app.tasks.email_tasks import send_message_task
        # send_message_task.delay(message.id)
        
        return {
            "message_id": message.id,
            "status": "queued",
            "message": "Message queued for sending"
        }
    
    async def pause_automation(
        self,
        db: Session,
        conversation_id: int,
        workspace_id: int
    ) -> Dict[str, Any]:
        """Pause automation for conversation"""
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.workspace_id == workspace_id
        ).first()
        
        if not conversation:
            raise NotFoundException("Conversation not found")
        
        conversation.automation_paused = True
        db.commit()
        
        return {"message": "Automation paused for this conversation"}
    
    async def get_unread_count(self, db: Session, workspace_id: int) -> Dict[str, Any]:
        """Get total unread message count"""
        total_unread = db.query(
            db.func.sum(Conversation.unread_count)
        ).filter(
            Conversation.workspace_id == workspace_id,
            Conversation.status == "active"
        ).scalar() or 0
        
        unread_conversations = db.query(Conversation).filter(
            Conversation.workspace_id == workspace_id,
            Conversation.status == "active",
            Conversation.unread_count > 0
        ).count()
        
        return {
            "total_unread_messages": int(total_unread),
            "unread_conversations": unread_conversations
        }