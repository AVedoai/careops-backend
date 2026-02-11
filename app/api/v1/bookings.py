from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from app.database import get_db
from app.api.deps import get_current_workspace, check_booking_permission
from app.schemas.booking import BookingResponse, BookingCreate, BookingUpdate
from app.services.booking_service import BookingService
from app.models.workspace import Workspace
from app.models.user import User

router = APIRouter()
booking_service = BookingService()

@router.get("/", response_model=List[BookingResponse])
async def list_bookings(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    workspace: Workspace = Depends(get_current_workspace),
    current_user: User = Depends(check_booking_permission),
    db: Session = Depends(get_db)
):
    """List bookings"""
    return await booking_service.list_bookings(db, workspace.id, skip, limit, status, date_from, date_to)

@router.post("/", response_model=BookingResponse)
async def create_booking(
    booking_data: BookingCreate,
    workspace: Workspace = Depends(get_current_workspace),
    current_user: User = Depends(check_booking_permission),
    db: Session = Depends(get_db)
):
    """Create booking (internal)"""
    return await booking_service.create_booking(db, workspace.id, booking_data)

@router.get("/today", response_model=List[BookingResponse])
async def get_todays_bookings(
    workspace: Workspace = Depends(get_current_workspace),
    current_user: User = Depends(check_booking_permission),
    db: Session = Depends(get_db)
):
    """Get today's bookings"""
    return await booking_service.get_todays_bookings(db, workspace.id)

@router.get("/upcoming", response_model=List[BookingResponse])
async def get_upcoming_bookings(
    days: int = Query(7, ge=1, le=30),
    workspace: Workspace = Depends(get_current_workspace),
    current_user: User = Depends(check_booking_permission),
    db: Session = Depends(get_db)
):
    """Get upcoming bookings"""
    return await booking_service.get_upcoming_bookings(db, workspace.id, days)

@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: int,
    workspace: Workspace = Depends(get_current_workspace),
    current_user: User = Depends(check_booking_permission),
    db: Session = Depends(get_db)
):
    """Get booking details"""
    return await booking_service.get_booking(db, booking_id, workspace.id)

@router.put("/{booking_id}", response_model=BookingResponse)
async def update_booking(
    booking_id: int,
    booking_data: BookingUpdate,
    workspace: Workspace = Depends(get_current_workspace),
    current_user: User = Depends(check_booking_permission),
    db: Session = Depends(get_db)
):
    """Update booking"""
    return await booking_service.update_booking(db, booking_id, workspace.id, booking_data)

@router.delete("/{booking_id}")
async def cancel_booking(
    booking_id: int,
    workspace: Workspace = Depends(get_current_workspace),
    current_user: User = Depends(check_booking_permission),
    db: Session = Depends(get_db)
):
    """Cancel booking"""
    await booking_service.cancel_booking(db, booking_id, workspace.id)
    return {"message": "Booking cancelled successfully"}