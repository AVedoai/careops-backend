from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.database import get_db
from app.api.deps import get_current_workspace, check_inbox_permission
from app.schemas.conversation import ConversationResponse, ConversationDetail, MessageSend
from app.services.conversation_service import ConversationService
from app.models.workspace import Workspace
from app.models.user import User

router = APIRouter()
conversation_service = ConversationService()

@router.get("/", response_model=List[ConversationResponse])
async def list_conversations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: str = Query("active"),
    workspace: Workspace = Depends(get_current_workspace),
    current_user: User = Depends(check_inbox_permission),
    db: Session = Depends(get_db)
):
    """List conversations"""
    return await conversation_service.list_conversations(db, workspace.id, skip, limit, status)

@router.get("/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: int,
    workspace: Workspace = Depends(get_current_workspace),
    current_user: User = Depends(check_inbox_permission),
    db: Session = Depends(get_db)
):
    """Get conversation with messages"""
    return await conversation_service.get_conversation_detail(db, conversation_id, workspace.id)

@router.post("/{conversation_id}/messages")
async def send_message(
    conversation_id: int,
    message_data: MessageSend,
    workspace: Workspace = Depends(get_current_workspace),
    current_user: User = Depends(check_inbox_permission),
    db: Session = Depends(get_db)
):
    """Send message"""
    return await conversation_service.send_message(db, conversation_id, workspace.id, message_data, current_user.id)

@router.put("/{conversation_id}/pause-automation")
async def pause_automation(
    conversation_id: int,
    workspace: Workspace = Depends(get_current_workspace),
    current_user: User = Depends(check_inbox_permission),
    db: Session = Depends(get_db)
):
    """Pause automation for conversation"""
    return await conversation_service.pause_automation(db, conversation_id, workspace.id)

@router.get("/unread", response_model=Dict[str, Any])
async def get_unread_count(
    workspace: Workspace = Depends(get_current_workspace),
    current_user: User = Depends(check_inbox_permission),
    db: Session = Depends(get_db)
):
    """Get unread message count"""
    return await conversation_service.get_unread_count(db, workspace.id)