from sqlalchemy.orm import Session
from sqlalchemy import func, case
from typing import Dict, Any
from datetime import datetime, date
from app.models.workspace import Workspace
from app.models.user import User
from app.models.contact import Contact
from app.models.conversation import Conversation
from app.models.booking import Booking, BookingStatus
from app.models.form import FormSubmission
from app.models.inventory import InventoryItem
from app.models.alert import Alert, AlertStatus
from app.schemas.workspace import WorkspaceUpdate
from app.utils.exceptions import NotFoundException, ValidationException


class WorkspaceService:
    async def get_workspace_by_slug(self, db: Session, slug: str) -> Workspace:
        """Get workspace by slug"""
        workspace = db.query(Workspace).filter(Workspace.slug == slug).first()
        if not workspace:
            raise NotFoundException("Workspace not found")
        return workspace
    
    async def update_workspace(self, db: Session, workspace_id: int, workspace_data: WorkspaceUpdate) -> Workspace:
        """Update workspace settings"""
        workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
        if not workspace:
            raise NotFoundException("Workspace not found")
        
        # Update fields
        for field, value in workspace_data.dict(exclude_unset=True).items():
            setattr(workspace, field, value)
        
        workspace.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(workspace)
        
        return workspace
    
    async def activate_workspace(self, db: Session, workspace_id: int) -> Dict[str, Any]:
        """Activate workspace after onboarding completion"""
        workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
        if not workspace:
            raise NotFoundException("Workspace not found")
        
        if not workspace.onboarding_completed:
            raise ValidationException("Onboarding must be completed first")
        
        workspace.is_active = True
        workspace.updated_at = datetime.utcnow()
        db.commit()
        
        return {"message": "Workspace activated successfully"}
    
    async def get_onboarding_status(self, db: Session, workspace_id: int) -> Dict[str, Any]:
        """Get onboarding progress"""
        workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
        if not workspace:
            raise NotFoundException("Workspace not found")
        
        return {
            "current_step": workspace.onboarding_step,
            "completed": workspace.onboarding_completed,
            "is_active": workspace.is_active
        }
    
    async def update_onboarding_step(self, db: Session, workspace_id: int, step: int) -> Dict[str, Any]:
        """Update onboarding step"""
        workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
        if not workspace:
            raise NotFoundException("Workspace not found")
        
        if step < 1 or step > 5:  # Assuming 5 onboarding steps
            raise ValidationException("Invalid step number")
        
        workspace.onboarding_step = step
        workspace.updated_at = datetime.utcnow()
        
        if step == 5:  # Final step
            workspace.onboarding_completed = True
        
        db.commit()
        
        return {"current_step": step, "completed": workspace.onboarding_completed}
    
    async def complete_onboarding(self, db: Session, workspace_id: int) -> Dict[str, Any]:
        """Complete onboarding process"""
        workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
        if not workspace:
            raise NotFoundException("Workspace not found")
        
        workspace.onboarding_completed = True
        workspace.onboarding_step = 5
        workspace.updated_at = datetime.utcnow()
        db.commit()
        
        return {"message": "Onboarding completed successfully"}
    
    async def get_dashboard_data(self, db: Session, workspace_id: int) -> Dict[str, Any]:
        """Get dashboard statistics and data"""
        today = date.today()
        
        # Today's bookings
        todays_bookings = db.query(
            func.count(Booking.id).label('total'),
            func.sum(case([(Booking.status == BookingStatus.CONFIRMED, 1)], else_=0)).label('confirmed'),
            func.sum(case([(Booking.status == BookingStatus.COMPLETED, 1)], else_=0)).label('completed'),
            func.sum(case([(Booking.status == BookingStatus.CANCELLED, 1)], else_=0)).label('cancelled')
        ).filter(
            Booking.workspace_id == workspace_id,
            func.date(Booking.booking_date) == today
        ).first()
        
        # Conversation stats
        conversation_stats = db.query(
            func.count(Conversation.id).label('total'),
            func.sum(case([(Conversation.status == 'active', 1)], else_=0)).label('active'),
            func.sum(case([(Conversation.unread_count > 0, 1)], else_=0)).label('unread')
        ).filter(
            Conversation.workspace_id == workspace_id
        ).first()
        
        # Form submission stats
        form_stats = db.query(
            func.count(FormSubmission.id).label('total'),
            func.sum(case([(FormSubmission.status == 'pending', 1)], else_=0)).label('pending'),
            func.sum(case([(FormSubmission.status == 'overdue', 1)], else_=0)).label('overdue'),
            func.sum(case([(FormSubmission.status == 'completed', 1)], else_=0)).label('completed')
        ).join(Booking).filter(
            Booking.workspace_id == workspace_id
        ).first()
        
        # Inventory alerts
        low_stock_items = db.query(InventoryItem).filter(
            InventoryItem.workspace_id == workspace_id,
            InventoryItem.quantity <= InventoryItem.low_stock_threshold
        ).count()
        
        # Critical alerts
        critical_alerts = db.query(Alert).filter(
            Alert.workspace_id == workspace_id,
            Alert.status == AlertStatus.ACTIVE,
            Alert.severity.in_(['high', 'critical'])
        ).count()
        
        # Recent contacts
        new_contacts_today = db.query(Contact).filter(
            Contact.workspace_id == workspace_id,
            func.date(Contact.created_at) == today
        ).count()
        
        return {
            "bookings": {
                "today": {
                    "total": todays_bookings.total or 0,
                    "confirmed": todays_bookings.confirmed or 0,
                    "completed": todays_bookings.completed or 0,
                    "cancelled": todays_bookings.cancelled or 0
                }
            },
            "conversations": {
                "total": conversation_stats.total or 0,
                "active": conversation_stats.active or 0,
                "unread": conversation_stats.unread or 0
            },
            "forms": {
                "total": form_stats.total or 0,
                "pending": form_stats.pending or 0,
                "overdue": form_stats.overdue or 0,
                "completed": form_stats.completed or 0
            },
            "alerts": {
                "low_stock_items": low_stock_items,
                "critical_alerts": critical_alerts
            },
            "contacts": {
                "new_today": new_contacts_today
            }
        }