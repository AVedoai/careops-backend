from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import date
from app.database import get_db
from app.api.deps import get_current_workspace, get_current_owner
from app.schemas.service import ServiceResponse, ServiceCreate, ServiceUpdate
from app.services.booking_service import BookingService
from app.models.workspace import Workspace
from app.models.user import User

router = APIRouter()
booking_service = BookingService()

@router.get("/", response_model=List[ServiceResponse])
async def list_services(
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db)
):
    """List services"""
    return await booking_service.list_services(db, workspace.id)

@router.post("/", response_model=ServiceResponse)
async def create_service(
    service_data: ServiceCreate,
    workspace: Workspace = Depends(get_current_workspace),
    current_user: User = Depends(get_current_owner),
    db: Session = Depends(get_db)
):
    """Create service"""
    return await booking_service.create_service(db, workspace.id, service_data)

@router.get("/{service_id}", response_model=ServiceResponse)
async def get_service(
    service_id: int,
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db)
):
    """Get service details"""
    return await booking_service.get_service(db, service_id, workspace.id)

@router.put("/{service_id}", response_model=ServiceResponse)
async def update_service(
    service_id: int,
    service_data: ServiceUpdate,
    workspace: Workspace = Depends(get_current_workspace),
    current_user: User = Depends(get_current_owner),
    db: Session = Depends(get_db)
):
    """Update service"""
    return await booking_service.update_service(db, service_id, workspace.id, service_data)

@router.delete("/{service_id}")
async def delete_service(
    service_id: int,
    workspace: Workspace = Depends(get_current_workspace),
    current_user: User = Depends(get_current_owner),
    db: Session = Depends(get_db)
):
    """Delete service"""
    await booking_service.delete_service(db, service_id, workspace.id)
    return {"message": "Service deleted successfully"}

@router.get("/{service_id}/availability")
async def get_availability(
    service_id: int,
    booking_date: date = Query(...),
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get available time slots for a service on a specific date"""
    return await booking_service.get_availability(db, service_id, workspace.id, booking_date)