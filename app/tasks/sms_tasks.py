from celery import current_app
from app.tasks.celery_app import celery_app
from app.database import get_db
from app.models.message import Message
from app.models.contact import Contact
from app.models.workspace import Workspace
from app.integrations.sms.twilio import TwilioIntegration
from app.services.integration_service import IntegrationService
import logging

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def send_sms_task(self, message_id: int):
    """Send SMS message"""
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
        
        if not contact.phone:
            logger.error(f"Contact {contact.id} has no phone number")
            message.status = "failed"
            db.commit()
            return {"status": "failed", "error": "No phone number"}
        
        # Get SMS integration
        try:
            sms_integration = await integration_service.get_sms_integration(db, workspace.id)
        except Exception as e:
            logger.error(f"No SMS integration found for workspace {workspace.id}: {str(e)}")
            message.status = "failed"
            db.commit()
            return {"status": "failed", "error": "No SMS integration configured"}
        
        # Create integration instance
        if sms_integration.provider == "twilio":
            sms_client = TwilioIntegration(sms_integration.credentials)
        else:
            logger.error(f"Unsupported SMS provider: {sms_integration.provider}")
            message.status = "failed"
            db.commit()
            return {"status": "failed", "error": "Unsupported SMS provider"}
        
        # Send SMS
        result = await sms_client.send_sms(
            to_phone=contact.phone,
            message=message.content
        )
        
        if result["success"]:
            message.status = "sent"
            message.external_id = result.get("message_sid")
            logger.info(f"SMS sent successfully: {message_id}")
        else:
            message.status = "failed"
            logger.error(f"Failed to send SMS: {result.get('error')}")
        
        db.commit()
        return result
        
    except Exception as e:
        logger.error(f"Error in send_sms_task: {str(e)}")
        if 'message' in locals():
            message.status = "failed"
            db.commit()
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()


@celery_app.task(bind=True)
def send_template_sms_task(self, workspace_id: int, to_phone: str, template_type: str, template_data: dict):
    """Send templated SMS"""
    db = next(get_db())
    integration_service = IntegrationService()
    
    try:
        # Get SMS integration
        sms_integration = await integration_service.get_sms_integration(db, workspace_id)
        
        # Create integration instance
        if sms_integration.provider == "twilio":
            sms_client = TwilioIntegration(sms_integration.credentials)
        else:
            logger.error(f"Unsupported SMS provider: {sms_integration.provider}")
            return {"status": "failed", "error": "Unsupported SMS provider"}
        
        # Get template content
        message_content = _get_sms_template(template_type, template_data)
        
        # Send SMS
        result = await sms_client.send_sms(
            to_phone=to_phone,
            message=message_content
        )
        
        logger.info(f"Template SMS '{template_type}' sent to {to_phone}: {result['success']}")
        return result
        
    except Exception as e:
        logger.error(f"Error in send_template_sms_task: {str(e)}")
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()


def _get_sms_template(template_type: str, template_data: dict) -> str:
    """Get SMS template content"""
    templates = {
        "welcome_sms": f"Hi {template_data.get('contact_name', 'there')}! Thanks for reaching out to {template_data.get('workspace_name', 'us')}. We'll get back to you soon!",
        "booking_confirmation": f"Hi {template_data.get('contact_name')}! Your {template_data.get('service_name')} appointment on {template_data.get('booking_date')} at {template_data.get('booking_time')} is confirmed. See you then!",
        "booking_reminder": f"Reminder: You have a {template_data.get('service_name')} appointment tomorrow at {template_data.get('booking_time')}. Please let us know if you need to reschedule.",
        "form_reminder": f"Hi {template_data.get('contact_name')}! Please complete your forms before your appointment: {template_data.get('forms_link', 'Contact us for the link')}"
    }
    
    return templates.get(template_type, "You have a new notification.")