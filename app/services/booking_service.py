from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func, extract
from typing import List, Optional, Dict, Any
from datetime import datetime, date, time, timedelta
from app.models.booking import Booking, BookingStatus
from app.models.service import Service
from app.models.contact import Contact
from app.models.workspace import Workspace
from app.schemas.booking import BookingCreate, BookingUpdate, PublicBookingCreate
from app.schemas.service import ServiceCreate, ServiceUpdate
from app.utils.exceptions import NotFoundException, ValidationException
from app.services.contact_service import ContactService
from app.automation.engine import automation_engine
from app.websockets.manager import websocket_manager


class BookingService:
    def __init__(self):
        self.contact_service = ContactService()
    
    # Service management methods
    async def list_services(self, db: Session, workspace_id: int) -> List[Service]:
        """List all services for workspace"""
        return db.query(Service).filter(
            Service.workspace_id == workspace_id
        ).order_by(Service.name).all()
    
    async def create_service(self, db: Session, workspace_id: int, service_data: ServiceCreate) -> Service:
        """Create new service"""
        # Generate slug from name
        slug = service_data.name.lower().replace(" ", "-").replace("_", "-")
        
        # Ensure unique slug
        existing = db.query(Service).filter(
            Service.workspace_id == workspace_id,
            Service.slug == slug
        ).first()
        
        counter = 1
        original_slug = slug
        while existing:
            slug = f"{original_slug}-{counter}"
            existing = db.query(Service).filter(
                Service.workspace_id == workspace_id,
                Service.slug == slug
            ).first()
            counter += 1
        
        service = Service(
            workspace_id=workspace_id,
            name=service_data.name,
            slug=slug,
            description=service_data.description,
            duration_minutes=service_data.duration_minutes,
            location=service_data.location,
            availability=service_data.availability or {},
            is_active=True
        )
        
        db.add(service)
        db.commit()
        db.refresh(service)
        
        return service
    
    async def get_service(self, db: Session, service_id: int, workspace_id: int) -> Service:
        """Get service by ID"""
        service = db.query(Service).filter(
            Service.id == service_id,
            Service.workspace_id == workspace_id
        ).first()
        
        if not service:
            raise NotFoundException("Service not found")
        
        return service
    
    async def get_service_by_slug(self, db: Session, slug: str, workspace_id: int) -> Service:
        """Get service by slug"""
        service = db.query(Service).filter(
            Service.slug == slug,
            Service.workspace_id == workspace_id,
            Service.is_active == True
        ).first()
        
        if not service:
            raise NotFoundException("Service not found")
        
        return service
    
    async def update_service(
        self, 
        db: Session, 
        service_id: int, 
        workspace_id: int, 
        service_data: ServiceUpdate
    ) -> Service:
        """Update service"""
        service = await self.get_service(db, service_id, workspace_id)
        
        for field, value in service_data.dict(exclude_unset=True).items():
            setattr(service, field, value)
        
        db.commit()
        db.refresh(service)
        
        return service
    
    async def delete_service(self, db: Session, service_id: int, workspace_id: int):
        """Delete service (soft delete by marking inactive)"""
        service = await self.get_service(db, service_id, workspace_id)
        service.is_active = False
        db.commit()
    
    # Booking management methods
    async def list_bookings(
        self,
        db: Session,
        workspace_id: int,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> List[Booking]:
        """List bookings with filters"""
        query = db.query(Booking).options(
            joinedload(Booking.contact),
            joinedload(Booking.service)
        ).filter(
            Booking.workspace_id == workspace_id
        )
        
        if status:
            query = query.filter(Booking.status == status)
        
        if date_from:
            query = query.filter(Booking.booking_date >= date_from)
        
        if date_to:
            query = query.filter(Booking.booking_date <= date_to)
        
        return query.order_by(
            Booking.booking_date.desc(),
            Booking.booking_time.desc()
        ).offset(skip).limit(limit).all()
    
    async def create_booking(self, db: Session, workspace_id: int, booking_data: BookingCreate) -> Booking:
        """Create internal booking"""
        # Validate service exists
        service = await self.get_service(db, booking_data.service_id, workspace_id)
        
        # Validate contact exists
        contact = db.query(Contact).filter(
            Contact.id == booking_data.contact_id,
            Contact.workspace_id == workspace_id
        ).first()
        
        if not contact:
            raise NotFoundException("Contact not found")
        
        # Check availability
        if not await self._check_availability(db, service.id, booking_data.booking_date, booking_data.booking_time):
            raise ValidationException("Time slot not available")
        
        booking = Booking(
            workspace_id=workspace_id,
            contact_id=booking_data.contact_id,
            service_id=booking_data.service_id,
            booking_date=booking_data.booking_date,
            booking_time=booking_data.booking_time,
            status=BookingStatus.CONFIRMED,
            notes=booking_data.notes
        )
        
        db.add(booking)
        db.commit()
        db.refresh(booking)
        
        return booking
    
    async def create_public_booking(
        self, 
        db: Session, 
        workspace_slug: str, 
        service_slug: str, 
        booking_data: PublicBookingCreate
    ) -> Booking:
        """Create booking from public booking page"""
        # Get workspace
        workspace = db.query(Workspace).filter(
            Workspace.slug == workspace_slug,
            Workspace.is_active == True
        ).first()
        
        if not workspace:
            raise NotFoundException("Workspace not found")
        
        # Get service
        service = await self.get_service_by_slug(db, service_slug, workspace.id)
        
        # Create or get contact
        from app.schemas.contact import ContactCreate
        contact_data = ContactCreate(
            full_name=booking_data.full_name,
            email=booking_data.email,
            phone=booking_data.phone
        )
        
        contact = await self.contact_service.create_contact(db, workspace.id, contact_data)
        
        # Check availability
        if not await self._check_availability(db, service.id, booking_data.booking_date, booking_data.booking_time):
            raise ValidationException("Time slot not available")
        
        booking = Booking(
            workspace_id=workspace.id,
            contact_id=contact.id,
            service_id=service.id,
            booking_date=booking_data.booking_date,
            booking_time=booking_data.booking_time,
            status=BookingStatus.CONFIRMED,
            notes=booking_data.notes
        )
        
        db.add(booking)
        db.commit()
        db.refresh(booking)
        
        # Trigger automation: booking_created
        await automation_engine.trigger_event("booking_created", {
            "booking_id": booking.id,
            "workspace_id": workspace.id,
            "contact_id": contact.id
        })
        
        # Emit WebSocket event
        await websocket_manager.emit_new_booking(workspace.id, {
            "id": booking.id,
            "contact": {"id": contact.id, "full_name": contact.full_name},
            "service": {"id": service.id, "name": service.name},
            "booking_date": booking.booking_date.isoformat(),
            "booking_time": booking.booking_time.strftime("%H:%M"),
            "status": booking.status,
            "created_at": booking.created_at.isoformat()
        })
        
        return booking
    
    async def get_booking(self, db: Session, booking_id: int, workspace_id: int) -> Booking:
        """Get booking by ID"""
        booking = db.query(Booking).options(
            joinedload(Booking.contact),
            joinedload(Booking.service)
        ).filter(
            Booking.id == booking_id,
            Booking.workspace_id == workspace_id
        ).first()
        
        if not booking:
            raise NotFoundException("Booking not found")
        
        return booking
    
    async def update_booking(
        self, 
        db: Session, 
        booking_id: int, 
        workspace_id: int, 
        booking_data: BookingUpdate
    ) -> Booking:
        """Update booking"""
        booking = await self.get_booking(db, booking_id, workspace_id)
        
        # If date/time is being changed, check availability
        if (booking_data.booking_date and booking_data.booking_date != booking.booking_date) or \
           (booking_data.booking_time and booking_data.booking_time != booking.booking_time):
            
            new_date = booking_data.booking_date or booking.booking_date
            new_time = booking_data.booking_time or booking.booking_time
            
            # Exclude current booking from availability check
            if not await self._check_availability(db, booking.service_id, new_date, new_time, exclude_booking_id=booking.id):
                raise ValidationException("New time slot not available")
        
        # Update fields
        for field, value in booking_data.dict(exclude_unset=True).items():
            setattr(booking, field, value)
        
        booking.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(booking)
        
        return booking
    
    async def cancel_booking(self, db: Session, booking_id: int, workspace_id: int):
        """Cancel booking"""
        booking = await self.get_booking(db, booking_id, workspace_id)
        booking.status = BookingStatus.CANCELLED
        booking.updated_at = datetime.utcnow()
        db.commit()
    
    async def get_todays_bookings(self, db: Session, workspace_id: int) -> List[Booking]:
        """Get today's bookings"""
        today = date.today()
        return await self.list_bookings(
            db, workspace_id, 0, 100, None, today, today
        )
    
    async def get_upcoming_bookings(self, db: Session, workspace_id: int, days: int = 7) -> List[Booking]:
        """Get upcoming bookings (next N days)"""
        today = date.today()
        end_date = today + timedelta(days=days)
        return await self.list_bookings(
            db, workspace_id, 0, 100, "confirmed", today, end_date
        )
    
    async def get_public_booking_data(
        self, 
        db: Session, 
        workspace_slug: str, 
        service_slug: str
    ) -> Dict[str, Any]:
        """Get data needed for public booking page"""
        workspace = db.query(Workspace).filter(
            Workspace.slug == workspace_slug,
            Workspace.is_active == True
        ).first()
        
        if not workspace:
            raise NotFoundException("Workspace not found")
        
        service = await self.get_service_by_slug(db, service_slug, workspace.id)
        
        return {
            "workspace": {
                "name": workspace.name,
                "slug": workspace.slug
            },
            "service": {
                "id": service.id,
                "name": service.name,
                "description": service.description,
                "duration_minutes": service.duration_minutes,
                "location": service.location,
                "availability": service.availability
            }
        }
    
    async def get_availability(
        self, 
        db: Session, 
        service_id: int, 
        workspace_id: int, 
        booking_date: date
    ) -> Dict[str, Any]:
        """Get available time slots for a service on a date"""
        service = await self.get_service(db, service_id, workspace_id)
        
        # Get day of week (0 = Monday, 6 = Sunday)
        day_name = booking_date.strftime("%A").lower()
        
        # Get availability for this day
        day_availability = service.availability.get(day_name, [])
        
        if not day_availability:
            return {"available_slots": []}
        
        # Get existing bookings for this date
        existing_bookings = db.query(Booking.booking_time).filter(
            Booking.service_id == service_id,
            Booking.booking_date == booking_date,
            Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.PENDING])
        ).all()
        
        booked_times = {booking.booking_time for booking in existing_bookings}
        
        # Generate available slots
        available_slots = []
        
        for time_range in day_availability:
            start_str, end_str = time_range.split("-")
            start_time = datetime.strptime(start_str, "%H:%M").time()
            end_time = datetime.strptime(end_str, "%H:%M").time()
            
            current = datetime.combine(booking_date, start_time)
            end = datetime.combine(booking_date, end_time)
            
            while current < end:
                slot_time = current.time()
                
                # Check if slot is not booked
                if slot_time not in booked_times:
                    # Check if enough time before end of availability
                    slot_end = current + timedelta(minutes=service.duration_minutes)
                    if slot_end.time() <= end_time:
                        available_slots.append(slot_time.strftime("%H:%M"))
                
                current += timedelta(minutes=30)  # 30-minute intervals
        
        return {
            "available_slots": available_slots,
            "service_duration": service.duration_minutes
        }
    
    async def _check_availability(
        self, 
        db: Session, 
        service_id: int, 
        booking_date: date, 
        booking_time: time,
        exclude_booking_id: Optional[int] = None
    ) -> bool:
        """Check if a time slot is available"""
        query = db.query(Booking).filter(
            Booking.service_id == service_id,
            Booking.booking_date == booking_date,
            Booking.booking_time == booking_time,
            Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.PENDING])
        )
        
        if exclude_booking_id:
            query = query.filter(Booking.id != exclude_booking_id)
        
        existing = query.first()
        return existing is None