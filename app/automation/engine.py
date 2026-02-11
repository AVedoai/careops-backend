from sqlalchemy.orm import Session
from typing import Dict, Any, List
from datetime import datetime
import logging
from app.models.automation_rule import AutomationRule
from app.database import get_db


logger = logging.getLogger(__name__)


class AutomationEngine:
    """Central automation engine for event processing"""
    
    async def trigger_event(self, event_type: str, data: Dict[str, Any]):
        """Trigger automation based on event type"""
        logger.info(f"Triggering automation for event: {event_type}")
        
        db = next(get_db())
        try:
            # Get active automation rules for this event
            rules = db.query(AutomationRule).filter(
                AutomationRule.event_type == event_type,
                AutomationRule.is_active == True
            ).all()
            
            logger.info(f"Found {len(rules)} active rules for event {event_type}")
            
            for rule in rules:
                try:
                    await self._execute_rule(db, rule, data)
                    
                    # Update execution tracking
                    rule.execution_count += 1
                    rule.last_executed_at = datetime.utcnow()
                    db.commit()
                    
                except Exception as e:
                    logger.error(f"Failed to execute rule {rule.id}: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error in automation engine: {str(e)}")
        finally:
            db.close()
    
    async def _execute_rule(self, db: Session, rule: AutomationRule, data: Dict[str, Any]):
        """Execute a single automation rule"""
        logger.info(f"Executing rule {rule.id}: {rule.name}")
        
        if rule.action_type == "send_email":
            await self._handle_send_email(rule, data)
        
        elif rule.action_type == "send_sms":
            await self._handle_send_sms(rule, data)
        
        elif rule.action_type == "create_alert":
            await self._handle_create_alert(db, rule, data)
        
        elif rule.action_type == "schedule_reminder":
            await self._handle_schedule_reminder(rule, data)
        
        else:
            logger.warning(f"Unknown action type: {rule.action_type}")
    
    async def _handle_send_email(self, rule: AutomationRule, data: Dict[str, Any]):
        """Handle email sending automation"""
        from app.tasks.email_tasks import send_template_email_task
        
        config = rule.config or {}
        workspace_id = data.get("workspace_id")
        
        # Get recipient email based on event data
        to_email = None
        if "contact_id" in data:
            db = next(get_db())
            try:
                from app.models.contact import Contact
                contact = db.query(Contact).filter(Contact.id == data["contact_id"]).first()
                if contact and contact.email:
                    to_email = contact.email
            finally:
                db.close()
        
        if to_email:
            # Queue email task
            template_type = config.get("template", "default")
            delay_minutes = config.get("delay_minutes", 0)
            
            if delay_minutes > 0:
                from datetime import timedelta
                eta = datetime.utcnow() + timedelta(minutes=delay_minutes)
                send_template_email_task.apply_async(
                    args=[workspace_id, to_email, template_type, data],
                    eta=eta
                )
            else:
                send_template_email_task.delay(workspace_id, to_email, template_type, data)
            
            logger.info(f"Email task queued for {to_email}")
    
    async def _handle_send_sms(self, rule: AutomationRule, data: Dict[str, Any]):
        """Handle SMS sending automation"""
        from app.tasks.sms_tasks import send_template_sms_task
        
        config = rule.config or {}
        workspace_id = data.get("workspace_id")
        
        # Get recipient phone based on event data
        to_phone = None
        if "contact_id" in data:
            db = next(get_db())
            try:
                from app.models.contact import Contact
                contact = db.query(Contact).filter(Contact.id == data["contact_id"]).first()
                if contact and contact.phone:
                    to_phone = contact.phone
            finally:
                db.close()
        
        if to_phone:
            # Queue SMS task
            template_type = config.get("template", "default")
            delay_minutes = config.get("delay_minutes", 0)
            
            if delay_minutes > 0:
                from datetime import timedelta
                eta = datetime.utcnow() + timedelta(minutes=delay_minutes)
                send_template_sms_task.apply_async(
                    args=[workspace_id, to_phone, template_type, data],
                    eta=eta
                )
            else:
                send_template_sms_task.delay(workspace_id, to_phone, template_type, data)
            
            logger.info(f"SMS task queued for {to_phone}")
    
    async def _handle_create_alert(self, db: Session, rule: AutomationRule, data: Dict[str, Any]):
        """Handle alert creation automation"""
        from app.models.alert import Alert, AlertSeverity, AlertStatus
        
        config = rule.config or {}
        workspace_id = data.get("workspace_id")
        
        # Create alert based on config
        alert = Alert(
            workspace_id=workspace_id,
            type=config.get("alert_type", "automation"),
            status=AlertStatus.ACTIVE,
            severity=AlertSeverity(config.get("severity", "medium")),
            title=config.get("title", f"Automation Alert: {rule.name}"),
            message=config.get("message", f"Alert triggered by {rule.name}"),
            reference_type=data.get("reference_type"),
            reference_id=data.get("reference_id")
        )
        
        db.add(alert)
        db.commit()
        
        logger.info(f"Alert created: {alert.title}")
    
    async def _handle_schedule_reminder(self, rule: AutomationRule, data: Dict[str, Any]):
        """Handle reminder scheduling automation"""
        from app.tasks.booking_tasks import send_booking_reminder
        from datetime import timedelta
        
        config = rule.config or {}
        hours_before = config.get("hours_before", 24)
        
        if "booking_id" in data:
            booking_id = data["booking_id"]
            
            # Get booking details to calculate reminder time
            db = next(get_db())
            try:
                from app.models.booking import Booking
                booking = db.query(Booking).filter(Booking.id == booking_id).first()
                
                if booking:
                    # Calculate reminder time
                    booking_datetime = datetime.combine(booking.booking_date, booking.booking_time)
                    reminder_time = booking_datetime - timedelta(hours=hours_before)
                    
                    # Only schedule if reminder is in the future
                    if reminder_time > datetime.utcnow():
                        send_booking_reminder.apply_async(
                            args=[booking_id],
                            eta=reminder_time
                        )
                        logger.info(f"Reminder scheduled for booking {booking_id} at {reminder_time}")
            finally:
                db.close()


# Global automation engine instance
automation_engine = AutomationEngine()