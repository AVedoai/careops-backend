from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.api.deps import get_current_workspace, check_inbox_permission
from app.schemas.contact import ContactResponse, ContactCreate, ContactUpdate
from app.services.contact_service import ContactService
from app.models.workspace import Workspace
from app.models.user import User

router = APIRouter()
contact_service = ContactService()

@router.get("/", response_model=List[ContactResponse])
async def list_contacts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    workspace: Workspace = Depends(get_current_workspace),
    current_user: User = Depends(check_inbox_permission),
    db: Session = Depends(get_db)
):
    """List contacts"""
    return await contact_service.list_contacts(db, workspace.id, skip, limit, search)

@router.post("/", response_model=ContactResponse)
async def create_contact(
    contact_data: ContactCreate,
    workspace: Workspace = Depends(get_current_workspace),
    current_user: User = Depends(check_inbox_permission),
    db: Session = Depends(get_db)
):
    """Create contact"""
    return await contact_service.create_contact(db, workspace.id, contact_data)

@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(
    contact_id: int,
    workspace: Workspace = Depends(get_current_workspace),
    current_user: User = Depends(check_inbox_permission),
    db: Session = Depends(get_db)
):
    """Get contact details"""
    return await contact_service.get_contact(db, contact_id, workspace.id)

@router.put("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: int,
    contact_data: ContactUpdate,
    workspace: Workspace = Depends(get_current_workspace),
    current_user: User = Depends(check_inbox_permission),
    db: Session = Depends(get_db)
):
    """Update contact"""
    return await contact_service.update_contact(db, contact_id, workspace.id, contact_data)

@router.delete("/{contact_id}")
async def delete_contact(
    contact_id: int,
    workspace: Workspace = Depends(get_current_workspace),
    current_user: User = Depends(check_inbox_permission),
    db: Session = Depends(get_db)
):
    """Delete contact"""
    await contact_service.delete_contact(db, contact_id, workspace.id)
    return {"message": "Contact deleted successfully"}