from celery import current_app
from app.tasks.celery_app import celery_app
from app.database import get_db
from app.models.automation_rule import AutomationRule
from app.tasks.email_tasks import send_template_email_task
from app.tasks.sms_tasks import send_template_sms_task
from app.tasks.booking_tasks import send_booking_confirmation, schedule_booking_reminder
from app.tasks.form_tasks import send_booking_forms
from app.tasks.inventory_tasks import reserve_inventory_for_booking
from datetime import datetime, timedelta
import logging
import json

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def trigger_automation_event(self, event_type: str, workspace_id: int, data: dict):
    """Trigger automation rules based on an event"""
    db = next(get_db())
    
    try:
        # Get active automation rules for this event type
        rules = db.query(AutomationRule).filter(
            AutomationRule.workspace_id == workspace_id,
            AutomationRule.event_type == event_type,
            AutomationRule.is_active == True
        ).all()
        
        executed_rules = []
        
        for rule in rules:
            try:
                result = await _execute_automation_rule(rule, data)
                
                # Update rule execution tracking
                rule.execution_count += 1
                rule.last_executed_at = datetime.utcnow()
                
                executed_rules.append({
                    "rule_id": rule.id,
                    "rule_name": rule.name,
                    "action_type": rule.action_type,
                    "result": result
                })
                
                logger.info(f"Executed automation rule {rule.id}: {rule.name}")
                
            except Exception as e:
                logger.error(f"Failed to execute automation rule {rule.id}: {str(e)}")
                executed_rules.append({
                    "rule_id": rule.id,
                    "rule_name": rule.name,
                    "action_type": rule.action_type,
                    "error": str(e)
                })
        
        db.commit()
        
        logger.info(f"Triggered {len(executed_rules)} automation rules for event '{event_type}'")
        return {
            "status": "success",
            "event_type": event_type,
            "rules_executed": len(executed_rules),
            "results": executed_rules
        }
        
    except Exception as e:
        logger.error(f"Error in trigger_automation_event: {str(e)}")
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()


async def _execute_automation_rule(rule: AutomationRule, data: dict):
    """Execute a single automation rule"""
    action_type = rule.action_type
    config = rule.config or {}
    
    if action_type == "send_email":
        return await _execute_send_email_action(rule, data, config)
    
    elif action_type == "send_sms":
        return await _execute_send_sms_action(rule, data, config)
    
    elif action_type == "schedule_reminder":
        return await _execute_schedule_reminder_action(rule, data, config)
    
    elif action_type == "create_alert":
        return await _execute_create_alert_action(rule, data, config)
    
    elif action_type == "send_booking_confirmation":
        return await _execute_booking_confirmation_action(rule, data, config)
    
    elif action_type == "send_booking_forms":
        return await _execute_booking_forms_action(rule, data, config)
    
    elif action_type == "reserve_inventory":
        return await _execute_reserve_inventory_action(rule, data, config)
    
    else:
        raise ValueError(f"Unknown action type: {action_type}")


async def _execute_send_email_action(rule: AutomationRule, data: dict, config: dict):
    """Execute send email action"""
    template_type = config.get("template", "welcome_email")
    delay_minutes = config.get("delay_minutes", 0)
    
    if "contact_id" in data:
        # Get contact email and send template email
        # This would need to be implemented based on your contact model
        pass
    
    return {"action": "send_email", "template": template_type, "delay": delay_minutes}


async def _execute_send_sms_action(rule: AutomationRule, data: dict, config: dict):
    """Execute send SMS action"""
    template_type = config.get("template", "welcome_sms")
    delay_minutes = config.get("delay_minutes", 0)
    
    # Implementation for SMS sending
    return {"action": "send_sms", "template": template_type, "delay": delay_minutes}


async def _execute_schedule_reminder_action(rule: AutomationRule, data: dict, config: dict):
    """Execute schedule reminder action"""
    hours_before = config.get("hours_before", 24)
    
    if "booking_id" in data:
        booking_id = data["booking_id"]
        
        # Calculate reminder time (hours before booking)
        # This would need booking date/time from database
        # For now, schedule 24 hours from now as example
        reminder_time = datetime.utcnow() + timedelta(hours=hours_before)
        
        send_booking_reminder.apply_async(
            args=[booking_id],
            eta=reminder_time
        )
        
        return {
            "action": "schedule_reminder",
            "booking_id": booking_id,
            "scheduled_for": reminder_time.isoformat()
        }
    
    return {"action": "schedule_reminder", "error": "No booking_id provided"}


async def _execute_create_alert_action(rule: AutomationRule, data: dict, config: dict):
    """Execute create alert action"""
    from app.models.alert import Alert, AlertStatus, AlertSeverity
    from app.database import get_db
    
    db = next(get_db())
    
    try:
        severity = config.get("severity", "medium")
        title_template = config.get("title", "New Alert")
        message_template = config.get("message", "An event occurred that requires attention.")
        
        # Simple template substitution
        title = title_template.format(**data)
        message = message_template.format(**data)
        
        alert = Alert(
            workspace_id=rule.workspace_id,
            type="automation_triggered",
            status=AlertStatus.ACTIVE,
            severity=getattr(AlertSeverity, severity.upper(), AlertSeverity.MEDIUM),
            title=title,
            message=message
        )
        
        db.add(alert)
        db.commit()
        
        return {"action": "create_alert", "alert_id": alert.id}
        
    finally:
        db.close()


async def _execute_booking_confirmation_action(rule: AutomationRule, data: dict, config: dict):
    """Execute booking confirmation action"""
    if "booking_id" in data:
        booking_id = data["booking_id"]
        delay_minutes = config.get("delay_minutes", 0)
        
        if delay_minutes > 0:
            send_booking_confirmation.apply_async(
                args=[booking_id],
                countdown=delay_minutes * 60
            )
        else:
            send_booking_confirmation.delay(booking_id)
        
        return {"action": "booking_confirmation", "booking_id": booking_id}
    
    return {"action": "booking_confirmation", "error": "No booking_id provided"}


async def _execute_booking_forms_action(rule: AutomationRule, data: dict, config: dict):
    """Execute send booking forms action"""
    if "booking_id" in data:
        booking_id = data["booking_id"]
        delay_minutes = config.get("delay_minutes", 5)
        
        send_booking_forms.apply_async(
            args=[booking_id],
            countdown=delay_minutes * 60
        )
        
        return {"action": "booking_forms", "booking_id": booking_id}
    
    return {"action": "booking_forms", "error": "No booking_id provided"}


async def _execute_reserve_inventory_action(rule: AutomationRule, data: dict, config: dict):
    """Execute reserve inventory action"""
    if "booking_id" in data:
        booking_id = data["booking_id"]
        
        reserve_inventory_for_booking.delay(booking_id)
        
        return {"action": "reserve_inventory", "booking_id": booking_id}
    
    return {"action": "reserve_inventory", "error": "No booking_id provided"}


@celery_app.task(bind=True)
def contact_created_event(self, contact_id: int, workspace_id: int):
    """Handle contact created event"""
    return trigger_automation_event.delay(
        "contact_created",
        workspace_id,
        {"contact_id": contact_id, "workspace_id": workspace_id}
    )


@celery_app.task(bind=True)
def booking_created_event(self, booking_id: int, workspace_id: int):
    """Handle booking created event"""
    return trigger_automation_event.delay(
        "booking_created",
        workspace_id,
        {"booking_id": booking_id, "workspace_id": workspace_id}
    )