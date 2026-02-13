from sqlalchemy.orm import Session
from app.models.staff import Staff
from app.schemas.staff import StaffCreate, StaffResponse
from typing import List

class StaffService:
    def __init__(self, db: Session):
        self.db = db

    def list_staff(self, business_id: str) -> List[StaffResponse]:
        """List all staff members for a business"""
        staff = self.db.query(Staff).filter(Staff.business_id == business_id).all()
        return staff

    def create_staff(self, business_id: str, staff_in: StaffCreate) -> StaffResponse:
        """Create a new staff member"""
        staff = Staff(
            business_id=business_id,
            name=staff_in.name,
            email=staff_in.email,
            role=staff_in.role
        )
        self.db.add(staff)
        self.db.commit()
        self.db.refresh(staff)
        return staff

    def delete_staff(self, business_id: str, staff_id: str):
        """Delete a staff member"""
        staff = self.db.query(Staff).filter(
            Staff.business_id == business_id, Staff.id == staff_id
        ).first()
        if staff:
            self.db.delete(staff)
            self.db.commit()