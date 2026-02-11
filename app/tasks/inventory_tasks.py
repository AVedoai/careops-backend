from celery import current_app
from app.tasks.celery_app import celery_app
from app.database import get_db
from app.models.inventory import InventoryItem
from app.models.alert import Alert, AlertStatus, AlertSeverity
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def check_low_inventory(self):
    """Check for low inventory items and create alerts"""
    db = next(get_db())
    
    try:
        # Find low inventory items
        low_stock_items = db.query(InventoryItem).filter(
            InventoryItem.quantity <= InventoryItem.low_stock_threshold
        ).all()
        
        alerts_created = 0
        
        for item in low_stock_items:
            try:
                # Check if alert already exists
                existing_alert = db.query(Alert).filter(
                    Alert.workspace_id == item.workspace_id,
                    Alert.type == "inventory_low",
                    Alert.reference_type == "inventory_item",
                    Alert.reference_id == item.id,
                    Alert.status == AlertStatus.ACTIVE
                ).first()
                
                if not existing_alert:
                    # Determine severity based on stock level
                    if item.quantity == 0:
                        severity = AlertSeverity.CRITICAL
                        title = f"Out of Stock: {item.name}"
                        message = f"{item.name} is completely out of stock!"
                    else:
                        severity = AlertSeverity.HIGH
                        title = f"Low Stock: {item.name}"
                        message = f"{item.name} is running low. Current stock: {item.quantity} {item.unit}"
                    
                    # Create alert
                    alert = Alert(
                        workspace_id=item.workspace_id,
                        type="inventory_low",
                        status=AlertStatus.ACTIVE,
                        severity=severity,
                        title=title,
                        message=message,
                        reference_type="inventory_item",
                        reference_id=item.id,
                        link=f"/inventory/{item.id}"
                    )
                    db.add(alert)
                    alerts_created += 1
                    
                    logger.info(f"Created low stock alert for inventory item {item.id}: {item.name}")
                
            except Exception as e:
                logger.error(f"Failed to process inventory item {item.id}: {str(e)}")
                continue
        
        db.commit()
        
        logger.info(f"Processed {len(low_stock_items)} low stock items, created {alerts_created} alerts")
        return {
            "status": "success",
            "low_stock_items": len(low_stock_items),
            "alerts_created": alerts_created
        }
        
    except Exception as e:
        logger.error(f"Error in check_low_inventory: {str(e)}")
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()


@celery_app.task(bind=True)
def reserve_inventory_for_booking(self, booking_id: int):
    """Reserve inventory items for a booking"""
    db = next(get_db())
    
    try:
        from app.models.booking import Booking
        from app.models.service import Service
        from app.models.service_inventory import ServiceInventory  # If implementing this feature
        
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            logger.error(f"Booking {booking_id} not found")
            return {"status": "failed", "error": "Booking not found"}
        
        service = booking.service
        
        # Note: This would require a ServiceInventory relationship table
        # to map which inventory items are used by each service
        # For now, we'll implement a basic version
        
        # Get inventory items that might need to be reserved
        # This is a simplified implementation
        inventory_items = db.query(InventoryItem).filter(
            InventoryItem.workspace_id == booking.workspace_id,
            InventoryItem.usage_per_booking > 0
        ).all()
        
        reserved_items = []
        
        for item in inventory_items:
            if item.quantity >= item.usage_per_booking:
                # Reserve the item
                item.quantity -= item.usage_per_booking
                reserved_items.append({
                    "item_id": item.id,
                    "name": item.name,
                    "quantity_reserved": item.usage_per_booking,
                    "remaining_stock": item.quantity
                })
                
                # Check if item is now low stock
                if item.quantity <= item.low_stock_threshold:
                    check_low_inventory.delay()
        
        db.commit()
        
        logger.info(f"Reserved inventory for booking {booking_id}: {len(reserved_items)} items")
        return {
            "status": "success",
            "booking_id": booking_id,
            "reserved_items": reserved_items
        }
        
    except Exception as e:
        logger.error(f"Error in reserve_inventory_for_booking: {str(e)}")
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()


@celery_app.task(bind=True)
def release_inventory_for_booking(self, booking_id: int):
    """Release reserved inventory when booking is cancelled"""
    db = next(get_db())
    
    try:
        from app.models.booking import Booking
        
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            logger.error(f"Booking {booking_id} not found")
            return {"status": "failed", "error": "Booking not found"}
        
        # Get inventory items that were reserved for this service
        inventory_items = db.query(InventoryItem).filter(
            InventoryItem.workspace_id == booking.workspace_id,
            InventoryItem.usage_per_booking > 0
        ).all()
        
        released_items = []
        
        for item in inventory_items:
            # Release the reserved quantity
            item.quantity += item.usage_per_booking
            released_items.append({
                "item_id": item.id,
                "name": item.name,
                "quantity_released": item.usage_per_booking,
                "new_stock": item.quantity
            })
        
        db.commit()
        
        logger.info(f"Released inventory for cancelled booking {booking_id}: {len(released_items)} items")
        return {
            "status": "success",
            "booking_id": booking_id,
            "released_items": released_items
        }
        
    except Exception as e:
        logger.error(f"Error in release_inventory_for_booking: {str(e)}")
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()