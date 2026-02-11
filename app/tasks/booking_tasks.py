from celery import current_app
from app.tasks.celery_app import celery_app
from app.database import get_db
from app.models.booking import Booking, BookingStatus
from app.models.contact import Contact
from app.tasks.email_tasks import send_template_email_task
from app.tasks.sms_tasks import send_template_sms_task
from datetime import datetime, timedelta, date
import logging

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def send_booking_confirmation(self, booking_id: int):
    """Send booking confirmation email/SMS"""
    db = next(get_db())
    
    try:
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            logger.error(f"Booking {booking_id} not found")
            return {"status": "failed", "error": "Booking not found"}
        
        contact = booking.contact
        service = booking.service
        
        template_data = {
            "contact_name": contact.full_name,
            "service_name": service.name,
            "booking_date": booking.booking_date.strftime("%B %d, %Y"),
            "booking_time": booking.booking_time.strftime("%I:%M %p"),
            "location": service.location or "To be confirmed",
            "workspace_name": booking.workspace.name
        }
        
        results = []
        
        # Send email if contact has email and prefers email
        if contact.email and contact.preferred_channel == "email":
            email_result = send_template_email_task.delay(
                booking.workspace_id,
                contact.email,
                "booking_confirmation",
                template_data
            )
            results.append({"type": "email", "task_id": email_result.id})
        
        # Send SMS if contact has phone and prefers SMS
        elif contact.phone and contact.preferred_channel == "sms":
            sms_result = send_template_sms_task.delay(
                booking.workspace_id,
                contact.phone,
                "booking_confirmation",
                template_data
            )
            results.append({"type": "sms", "task_id": sms_result.id})
        
        # Update booking
        booking.confirmation_sent_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Booking confirmation sent for booking {booking_id}")
        return {"status": "success", "results": results}
        
    except Exception as e:
        logger.error(f"Error in send_booking_confirmation: {str(e)}")
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()


@celery_app.task(bind=True)
def send_booking_reminder(self, booking_id: int):
    """Send booking reminder 24h before appointment"""
    db = next(get_db())
    
    try:
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            logger.error(f"Booking {booking_id} not found")
            return {"status": "failed", "error": "Booking not found"}
        
        # Check if booking is still confirmed
        if booking.status != BookingStatus.CONFIRMED:
            logger.info(f"Booking {booking_id} is no longer confirmed, skipping reminder")
            return {"status": "skipped", "reason": "Booking not confirmed"}
        
        contact = booking.contact
        service = booking.service
        
        template_data = {
            "contact_name": contact.full_name,
            "service_name": service.name,
            "booking_date": booking.booking_date.strftime("%B %d, %Y"),
            "booking_time": booking.booking_time.strftime("%I:%M %p"),
            "location": service.location or "To be confirmed"
        }
        
        results = []
        
        # Send via preferred channel
        if contact.email and contact.preferred_channel == "email":
            email_result = send_template_email_task.delay(
                booking.workspace_id,
                contact.email,
                "booking_reminder",
                template_data
            )
            results.append({"type": "email", "task_id": email_result.id})
        
        elif contact.phone and contact.preferred_channel == "sms":
            sms_result = send_template_sms_task.delay(
                booking.workspace_id,
                contact.phone,
                "booking_reminder",
                template_data
            )
            results.append({"type": "sms", "task_id": sms_result.id})
        
        # Update booking
        booking.reminder_sent_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Booking reminder sent for booking {booking_id}")
        return {"status": "success", "results": results}
        
    except Exception as e:
        logger.error(f"Error in send_booking_reminder: {str(e)}")
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()


@celery_app.task(bind=True)
def schedule_booking_reminder(self, booking_id: int, reminder_time: str):
    """Schedule booking reminder for specific time"""
    try:
        # Parse reminder time
        reminder_datetime = datetime.fromisoformat(reminder_time)
        
        # Schedule the reminder task
        send_booking_reminder.apply_async(
            args=[booking_id],
            eta=reminder_datetime
        )
        
        logger.info(f"Booking reminder scheduled for booking {booking_id} at {reminder_time}")
        return {"status": "success", "scheduled_at": reminder_time}
        
    except Exception as e:
        logger.error(f"Error in schedule_booking_reminder: {str(e)}")
        return {"status": "failed", "error": str(e)}


@celery_app.task(bind=True)
def send_daily_reminders(self):
    """Send reminders for all bookings happening tomorrow"""
    db = next(get_db())
    
    try:
        tomorrow = date.today() + timedelta(days=1)
        
        # Get all confirmed bookings for tomorrow that haven't received reminders
        bookings = db.query(Booking).filter(
            Booking.booking_date == tomorrow,
            Booking.status == BookingStatus.CONFIRMED,
            Booking.reminder_sent_at.is_(None)
        ).all()
        
        reminder_count = 0
        
        for booking in bookings:
            try:
                send_booking_reminder.delay(booking.id)
                reminder_count += 1
            except Exception as e:
                logger.error(f"Failed to schedule reminder for booking {booking.id}: {str(e)}")
        
        logger.info(f"Scheduled {reminder_count} booking reminders for {tomorrow}")
        return {"status": "success", "reminders_scheduled": reminder_count}
        
    except Exception as e:
        logger.error(f"Error in send_daily_reminders: {str(e)}")
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()