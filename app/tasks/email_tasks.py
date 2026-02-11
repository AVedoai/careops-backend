from celery import current_app
from app.tasks.celery_app import celery_app
from app.database import get_db
from app.models.message import Message
from app.models.contact import Contact
from app.models.workspace import Workspace
from app.integrations.email.sendgrid import SendGridIntegration
from app.services.integration_service import IntegrationService
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def send_email_task(self, message_id: int):
    """Send email message"""
    db = next(get_db())
    integration_service = IntegrationService()
    
    try:
        # Get message
        message = db.query(Message).filter(Message.id == message_id).first()
        if not message:
            logger.error(f"Message {message_id} not found")
            return {"status": "failed", "error": "Message not found"}
        
        # Get contact and workspace
        contact = db.query(Contact).filter(Contact.id == message.conversation.contact_id).first()
        workspace = db.query(Workspace).filter(Contact.workspace_id == contact.workspace_id).first()
        
        if not contact.email:
            logger.error(f"Contact {contact.id} has no email address")
            message.status = "failed"
            db.commit()
            return {"status": "failed", "error": "No email address"}
        
        # Get email integration
        try:
            email_integration = await integration_service.get_email_integration(db, workspace.id)
        except Exception as e:
            logger.error(f"No email integration found for workspace {workspace.id}: {str(e)}")
            message.status = "failed"
            db.commit()
            return {"status": "failed", "error": "No email integration configured"}
        
        # Create integration instance
        if email_integration.provider == "sendgrid":
            email_client = SendGridIntegration(email_integration.credentials)
        else:
            logger.error(f"Unsupported email provider: {email_integration.provider}")
            message.status = "failed"
            db.commit()
            return {"status": "failed", "error": "Unsupported email provider"}
        
        # Send email
        result = await email_client.send_email(
            to_email=contact.email,
            subject=message.subject or "Message from " + workspace.name,
            html_content=f"<p>{message.content}</p>",
            text_content=message.content
        )
        
        if result["success"]:
            message.status = "sent"
            message.external_id = result.get("message_id")
            logger.info(f"Email sent successfully: {message_id}")
        else:
            message.status = "failed"
            logger.error(f"Failed to send email: {result.get('error')}")
        
        db.commit()
        return result
        
    except Exception as e:
        logger.error(f"Error in send_email_task: {str(e)}")
        if 'message' in locals():
            message.status = "failed"
            db.commit()
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()


@celery_app.task(bind=True)
def send_template_email_task(self, workspace_id: int, to_email: str, template_type: str, template_data: dict):
    """Send templated email"""
    db = next(get_db())
    integration_service = IntegrationService()
    
    try:
        # Get email integration
        email_integration = await integration_service.get_email_integration(db, workspace_id)
        
        # Create integration instance
        if email_integration.provider == "sendgrid":
            email_client = SendGridIntegration(email_integration.credentials)
        else:
            logger.error(f"Unsupported email provider: {email_integration.provider}")
            return {"status": "failed", "error": "Unsupported email provider"}
        
        # Get template content based on type
        subject, html_content = _get_email_template(template_type, template_data)
        
        # Send email
        result = await email_client.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content
        )
        
        logger.info(f"Template email '{template_type}' sent to {to_email}: {result['success']}")
        return result
        
    except Exception as e:
        logger.error(f"Error in send_template_email_task: {str(e)}")
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()


def _get_email_template(template_type: str, template_data: dict) -> tuple:
    """Get email template content"""
    templates = {
        "welcome_email": {
            "subject": f"Welcome to {template_data.get('workspace_name', 'CareOps')}!",
            "html": f"""
            <h2>Thanks for reaching out!</h2>
            <p>Hi {template_data.get('contact_name', 'there')},</p>
            <p>We received your message and will get back to you soon.</p>
            <p>Best regards,<br>{template_data.get('workspace_name', 'The Team')}</p>
            """
        },
        "booking_confirmation": {
            "subject": "Booking Confirmation",
            "html": f"""
            <h2>Your appointment is confirmed!</h2>
            <p>Hi {template_data.get('contact_name', 'there')},</p>
            <p><strong>Service:</strong> {template_data.get('service_name')}</p>
            <p><strong>Date:</strong> {template_data.get('booking_date')}</p>
            <p><strong>Time:</strong> {template_data.get('booking_time')}</p>
            <p><strong>Location:</strong> {template_data.get('location', 'TBD')}</p>
            <p>We look forward to seeing you!</p>
            """
        },
        "booking_reminder": {
            "subject": "Appointment Reminder",
            "html": f"""
            <h2>Reminder: You have an appointment tomorrow</h2>
            <p>Hi {template_data.get('contact_name', 'there')},</p>
            <p>This is a friendly reminder about your upcoming appointment:</p>
            <p><strong>Service:</strong> {template_data.get('service_name')}</p>
            <p><strong>Date:</strong> {template_data.get('booking_date')}</p>
            <p><strong>Time:</strong> {template_data.get('booking_time')}</p>
            <p><strong>Location:</strong> {template_data.get('location', 'TBD')}</p>
            <p>Please let us know if you need to reschedule.</p>
            """
        },
        "booking_forms": {
            "subject": "Please complete your forms",
            "html": f"""
            <h2>Forms to Complete</h2>
            <p>Hi {template_data.get('contact_name', 'there')},</p>
            <p>Please complete the required forms before your appointment:</p>
            <p><a href="{template_data.get('forms_link', '#')}">Complete Forms</a></p>
            <p>Thank you!</p>
            """
        }
    }
    
    template = templates.get(template_type, {
        "subject": "Notification",
        "html": "<p>You have a new notification.</p>"
    })
    
    return template["subject"], template["html"]