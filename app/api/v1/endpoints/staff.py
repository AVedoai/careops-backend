from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api import deps
from app.schemas.staff import StaffCreate, StaffResponse
from app.services.staff_service import StaffService
from typing import List

router = APIRouter()

@router.get("/", response_model=List[StaffResponse])
def list_staff(
    *,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_active_user)
):
    """List all staff members"""
    service = StaffService(db)
    return service.list_staff(current_user.business_id)

@router.post("/", response_model=StaffResponse, status_code=status.HTTP_201_CREATED)
def create_staff(
    *,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_active_user),
    staff_in: StaffCreate
):
    """Create a new staff member"""
    service = StaffService(db)
    return service.create_staff(current_user.business_id, staff_in)

@router.delete("/{staff_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_staff(
    *,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_active_user),
    staff_id: str
):
    """Delete a staff member"""
    service = StaffService(db)
    service.delete_staff(current_user.business_id, staff_id)
    return None