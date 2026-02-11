from celery import current_app
from app.tasks.celery_app import celery_app
from app.database import get_db
from app.models.form import FormSubmission
from app.models.booking import Booking
from app.models.alert import Alert, AlertStatus, AlertSeverity
from app.tasks.email_tasks import send_template_email_task
from app.tasks.sms_tasks import send_template_sms_task
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def send_booking_forms(self, booking_id: int):
    """Send forms to customer after booking"""
    db = next(get_db())
    
    try:
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            logger.error(f"Booking {booking_id} not found")
            return {"status": "failed", "error": "Booking not found"}
        
        # Check if there are forms to send
        form_submissions = db.query(FormSubmission).filter(
            FormSubmission.booking_id == booking_id
        ).all()
        
        if not form_submissions:
            logger.info(f"No forms to send for booking {booking_id}")
            return {"status": "skipped", "reason": "No forms assigned"}
        
        contact = booking.contact
        
        # Generate forms link (placeholder)
        forms_link = f"https://app.example.com/forms/booking/{booking_id}"
        
        template_data = {
            "contact_name": contact.full_name,
            "service_name": booking.service.name,
            "forms_link": forms_link,
            "booking_date": booking.booking_date.strftime("%B %d, %Y")
        }
        
        results = []
        
        # Send via preferred channel
        if contact.email and contact.preferred_channel == "email":
            email_result = send_template_email_task.delay(
                booking.workspace_id,
                contact.email,
                "booking_forms",
                template_data
            )
            results.append({"type": "email", "task_id": email_result.id})
        
        elif contact.phone and contact.preferred_channel == "sms":
            sms_result = send_template_sms_task.delay(
                booking.workspace_id,
                contact.phone,
                "form_reminder",
                template_data
            )
            results.append({"type": "sms", "task_id": sms_result.id})
        
        # Update booking
        booking.forms_sent_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Forms sent for booking {booking_id}")
        return {"status": "success", "results": results, "forms_count": len(form_submissions)}
        
    except Exception as e:
        logger.error(f"Error in send_booking_forms: {str(e)}")
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()


@celery_app.task(bind=True)
def check_overdue_forms(self):
    """Check for overdue form submissions and create alerts"""
    db = next(get_db())
    
    try:
        today = date.today()
        
        # Find overdue form submissions
        overdue_submissions = db.query(FormSubmission).join(Booking).filter(
            FormSubmission.due_date < today,
            FormSubmission.status == "pending"
        ).all()
        
        alerts_created = 0
        
        for submission in overdue_submissions:
            try:
                # Update submission status
                submission.status = "overdue"
                
                # Check if alert already exists
                existing_alert = db.query(Alert).filter(
                    Alert.workspace_id == submission.booking.workspace_id,
                    Alert.type == "form_overdue",
                    Alert.reference_type == "form_submission",
                    Alert.reference_id == submission.id,
                    Alert.status == AlertStatus.ACTIVE
                ).first()
                
                if not existing_alert:
                    # Create alert
                    alert = Alert(
                        workspace_id=submission.booking.workspace_id,
                        type="form_overdue",
                        status=AlertStatus.ACTIVE,
                        severity=AlertSeverity.MEDIUM,
                        title="Form Overdue",
                        message=f"Form '{submission.form.name}' is overdue for {submission.booking.contact.full_name}",
                        reference_type="form_submission",
                        reference_id=submission.id,
                        link=f"/forms/submissions/{submission.id}"
                    )
                    db.add(alert)
                    alerts_created += 1
                
            except Exception as e:
                logger.error(f"Failed to process overdue form {submission.id}: {str(e)}")
                continue
        
        db.commit()
        
        logger.info(f"Processed {len(overdue_submissions)} overdue forms, created {alerts_created} alerts")
        return {
            "status": "success",
            "overdue_forms": len(overdue_submissions),
            "alerts_created": alerts_created
        }
        
    except Exception as e:
        logger.error(f"Error in check_overdue_forms: {str(e)}")
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()


@celery_app.task(bind=True)
def send_form_reminder(self, submission_id: int):
    """Send reminder for pending form submission"""
    db = next(get_db())
    
    try:
        submission = db.query(FormSubmission).filter(
            FormSubmission.id == submission_id
        ).first()
        
        if not submission:
            logger.error(f"Form submission {submission_id} not found")
            return {"status": "failed", "error": "Submission not found"}
        
        if submission.status != "pending":
            logger.info(f"Form submission {submission_id} is no longer pending")
            return {"status": "skipped", "reason": "Submission not pending"}
        
        contact = submission.booking.contact
        
        # Generate forms link (placeholder)
        forms_link = f"https://app.example.com/forms/submission/{submission.id}"
        
        template_data = {
            "contact_name": contact.full_name,
            "form_name": submission.form.name,
            "forms_link": forms_link,
            "due_date": submission.due_date.strftime("%B %d, %Y")
        }
        
        results = []
        
        # Send via preferred channel
        if contact.email and contact.preferred_channel == "email":
            email_result = send_template_email_task.delay(
                submission.booking.workspace_id,
                contact.email,
                "form_reminder",
                template_data
            )
            results.append({"type": "email", "task_id": email_result.id})
        
        elif contact.phone and contact.preferred_channel == "sms":
            sms_result = send_template_sms_task.delay(
                submission.booking.workspace_id,
                contact.phone,
                "form_reminder",
                template_data
            )
            results.append({"type": "sms", "task_id": sms_result.id})
        
        # Update submission
        submission.reminder_sent_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Form reminder sent for submission {submission_id}")
        return {"status": "success", "results": results}
        
    except Exception as e:
        logger.error(f"Error in send_form_reminder: {str(e)}")
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()