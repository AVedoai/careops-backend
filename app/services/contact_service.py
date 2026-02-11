from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import List, Optional
from datetime import datetime
from app.models.contact import Contact
from app.models.conversation import Conversation
from app.schemas.contact import ContactCreate, ContactUpdate, ContactFormSubmission
from app.utils.exceptions import NotFoundException, ValidationException
from app.utils.validators import validate_email, validate_phone
from app.automation.engine import automation_engine
from app.websockets.manager import websocket_manager


class ContactService:
    def __init__(self):
        pass
    
    async def list_contacts(
        self, 
        db: Session, 
        workspace_id: int, 
        skip: int = 0, 
        limit: int = 100, 
        search: Optional[str] = None
    ) -> List[Contact]:
        """List contacts with optional search"""
        query = db.query(Contact).filter(Contact.workspace_id == workspace_id)
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    func.lower(Contact.full_name).contains(search_term.lower()),
                    func.lower(Contact.email).contains(search_term.lower()),
                    Contact.phone.contains(search_term)
                )
            )
        
        return query.order_by(Contact.created_at.desc()).offset(skip).limit(limit).all()
    
    async def create_contact(self, db: Session, workspace_id: int, contact_data: ContactCreate) -> Contact:
        """Create a new contact"""
        # Validate email if provided
        if contact_data.email and not validate_email(contact_data.email):
            raise ValidationException("Invalid email format")
        
        # Validate phone if provided
        if contact_data.phone and not validate_phone(contact_data.phone):
            raise ValidationException("Invalid phone format")
        
        # Check for existing contact with same email
        if contact_data.email:
            existing = db.query(Contact).filter(
                Contact.workspace_id == workspace_id,
                Contact.email == contact_data.email
            ).first()
            if existing:
                return existing  # Return existing contact
        
        contact = Contact(
            workspace_id=workspace_id,
            full_name=contact_data.full_name,
            email=contact_data.email,
            phone=contact_data.phone,
            preferred_channel=contact_data.preferred_channel or "email"
        )
        
        db.add(contact)
        db.flush()  # Get contact ID
        
        # Create conversation automatically
        conversation = Conversation(
            contact_id=contact.id,
            workspace_id=workspace_id,
            status="active",
            automation_paused=False,
            unread_count=0,
            last_message_at=datetime.utcnow()
        )
        
        db.add(conversation)
        db.commit()
        db.refresh(contact)
        
        return contact
    
    async def create_contact_from_form(
        self, 
        db: Session, 
        workspace_id: int, 
        form_data: ContactFormSubmission
    ) -> Contact:
        """Create contact from public form submission"""
        contact_data = ContactCreate(
            full_name=form_data.full_name,
            email=form_data.email,
            phone=form_data.phone,
            preferred_channel="email"
        )
        
        contact = await self.create_contact(db, workspace_id, contact_data)
        
        # Add initial message from form
        if hasattr(form_data, 'message') and form_data.message:
            from app.models.message import Message, MessageType, MessageDirection
            
            # Get the conversation for this contact
            conversation = db.query(Conversation).filter(
                Conversation.contact_id == contact.id
            ).first()
            
            if conversation:
                message = Message(
                    conversation_id=conversation.id,
                    type=MessageType.EMAIL,
                    direction=MessageDirection.INBOUND,
                    content=form_data.message,
                    is_automated=False,
                    status="received"
                )
                
                db.add(message)
                
                # Update conversation
                conversation.last_message_at = datetime.utcnow()
                conversation.unread_count += 1
                
                db.commit()
        
        # Trigger automation: contact_created event
        await automation_engine.trigger_event("contact_created", {
            "contact_id": contact.id,
            "workspace_id": workspace_id
        })
        
        # Emit WebSocket event
        await websocket_manager.emit_new_contact(workspace_id, {
            "id": contact.id,
            "full_name": contact.full_name,
            "email": contact.email,
            "phone": contact.phone,
            "created_at": contact.created_at.isoformat()
        })
        
        return contact
    
    async def get_contact(self, db: Session, contact_id: int, workspace_id: int) -> Contact:
        """Get contact by ID"""
        contact = db.query(Contact).filter(
            Contact.id == contact_id,
            Contact.workspace_id == workspace_id
        ).first()
        
        if not contact:
            raise NotFoundException("Contact not found")
        
        return contact
    
    async def update_contact(
        self, 
        db: Session, 
        contact_id: int, 
        workspace_id: int, 
        contact_data: ContactUpdate
    ) -> Contact:
        """Update contact"""
        contact = await self.get_contact(db, contact_id, workspace_id)
        
        # Validate email if being updated
        if contact_data.email and not validate_email(contact_data.email):
            raise ValidationException("Invalid email format")
        
        # Validate phone if being updated
        if contact_data.phone and not validate_phone(contact_data.phone):
            raise ValidationException("Invalid phone format")
        
        # Update fields
        for field, value in contact_data.dict(exclude_unset=True).items():
            setattr(contact, field, value)
        
        contact.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(contact)
        
        return contact
    
    async def delete_contact(self, db: Session, contact_id: int, workspace_id: int):
        """Delete contact and associated data"""
        contact = await self.get_contact(db, contact_id, workspace_id)
        
        # Delete associated conversation and messages (CASCADE should handle this)
        db.delete(contact)
        db.commit()