from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.database import get_db
from app.schemas.contact import ContactFormSubmission
from app.schemas.booking import PublicBookingCreate, BookingResponse
from app.services.contact_service import ContactService
from app.services.booking_service import BookingService
from app.services.workspace_service import WorkspaceService

router = APIRouter()
contact_service = ContactService()
booking_service = BookingService()
workspace_service = WorkspaceService()

@router.post("/contact-form/{workspace_slug}")
async def submit_contact_form(
    workspace_slug: str,
    form_data: ContactFormSubmission,
    db: Session = Depends(get_db)
):
    """Submit contact form (public)"""
    workspace = await workspace_service.get_workspace_by_slug(db, workspace_slug)
    if not workspace or not workspace.is_active:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    contact = await contact_service.create_contact_from_form(db, workspace.id, form_data)
    return {"success": True, "contact_id": contact.id}

@router.get("/booking/{workspace_slug}/{service_slug}")
async def get_booking_page(
    workspace_slug: str,
    service_slug: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get booking page data (public)"""
    return await booking_service.get_public_booking_data(db, workspace_slug, service_slug)

@router.post("/booking/{workspace_slug}/{service_slug}", response_model=BookingResponse)
async def create_booking(
    workspace_slug: str,
    service_slug: str,
    booking_data: PublicBookingCreate,
    db: Session = Depends(get_db)
):
    """Create booking (public)"""
    return await booking_service.create_public_booking(db, workspace_slug, service_slug, booking_data)

@router.get("/form/{submission_id}")
async def get_form_submission(
    submission_id: str,
    db: Session = Depends(get_db)
):
    """Get form to fill (public)"""
    # Implementation for form submissions
    pass

@router.post("/form/{submission_id}")
async def submit_form(
    submission_id: str,
    db: Session = Depends(get_db)
):
    """Submit completed form (public)"""
    # Implementation for form submissions
    pass