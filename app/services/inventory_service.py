from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime
from app.models.inventory import InventoryItem
from app.schemas.inventory import InventoryItemCreate, InventoryItemUpdate
from app.utils.exceptions import NotFoundException


class InventoryService:
    async def list_items(self, db: Session, workspace_id: int) -> List[InventoryItem]:
        """List all inventory items"""
        return db.query(InventoryItem).filter(
            InventoryItem.workspace_id == workspace_id
        ).order_by(InventoryItem.name).all()
    
    async def create_item(
        self, 
        db: Session, 
        workspace_id: int, 
        item_data: InventoryItemCreate
    ) -> InventoryItem:
        """Create inventory item"""
        item = InventoryItem(
            workspace_id=workspace_id,
            name=item_data.name,
            quantity=item_data.quantity,
            low_stock_threshold=item_data.low_stock_threshold,
            unit=item_data.unit,
            usage_per_booking=item_data.usage_per_booking
        )
        
        db.add(item)
        db.commit()
        db.refresh(item)
        
        return item
    
    async def get_item(self, db: Session, item_id: int, workspace_id: int) -> InventoryItem:
        """Get inventory item by ID"""
        item = db.query(InventoryItem).filter(
            InventoryItem.id == item_id,
            InventoryItem.workspace_id == workspace_id
        ).first()
        
        if not item:
            raise NotFoundException("Inventory item not found")
        
        return item
    
    async def update_item(
        self, 
        db: Session, 
        item_id: int, 
        workspace_id: int, 
        item_data: InventoryItemUpdate
    ) -> InventoryItem:
        """Update inventory item"""
        item = await self.get_item(db, item_id, workspace_id)
        
        # Store old quantity for comparison
        old_quantity = item.quantity
        
        # Update fields
        for field, value in item_data.dict(exclude_unset=True).items():
            setattr(item, field, value)
        
        item.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(item)
        
        # Check if we need to create/resolve low stock alert
        if old_quantity != item.quantity:
            await self._check_stock_level(db, item)
        
        return item
    
    async def delete_item(self, db: Session, item_id: int, workspace_id: int):
        """Delete inventory item"""
        item = await self.get_item(db, item_id, workspace_id)
        db.delete(item)
        db.commit()
    
    async def get_low_stock_alerts(self, db: Session, workspace_id: int) -> Dict[str, Any]:
        """Get items with low stock"""
        low_stock_items = db.query(InventoryItem).filter(
            InventoryItem.workspace_id == workspace_id,
            InventoryItem.quantity <= InventoryItem.low_stock_threshold
        ).all()
        
        return {
            "low_stock_items": low_stock_items,
            "count": len(low_stock_items)
        }
    
    async def reserve_inventory(self, db: Session, service_id: int, quantity: int = 1):
        """Reserve inventory for a booking"""
        # TODO: Implement inventory reservation logic
        # This would be called when a booking is confirmed
        pass
    
    async def release_inventory(self, db: Session, service_id: int, quantity: int = 1):
        """Release reserved inventory (e.g., when booking is cancelled)"""
        # TODO: Implement inventory release logic
        pass
    
    async def _check_stock_level(self, db: Session, item: InventoryItem):
        """Check stock level and create/resolve alerts"""
        from app.models.alert import Alert, AlertStatus, AlertSeverity
        
        # Check if item is now low stock
        if item.quantity <= item.low_stock_threshold:
            # Check if alert already exists
            existing_alert = db.query(Alert).filter(
                Alert.workspace_id == item.workspace_id,
                Alert.type == "inventory_low",
                Alert.reference_type == "inventory_item",
                Alert.reference_id == item.id,
                Alert.status == AlertStatus.ACTIVE
            ).first()
            
            if not existing_alert:
                # Create new alert
                alert = Alert(
                    workspace_id=item.workspace_id,
                    type="inventory_low",
                    status=AlertStatus.ACTIVE,
                    severity=AlertSeverity.HIGH if item.quantity == 0 else AlertSeverity.MEDIUM,
                    title=f"Low Stock: {item.name}",
                    message=f"{item.name} is running low. Current stock: {item.quantity} {item.unit}",
                    reference_type="inventory_item",
                    reference_id=item.id,
                    link=f"/inventory/{item.id}"
                )
                db.add(alert)
        else:
            # Item is no longer low stock, resolve any active alerts
            active_alerts = db.query(Alert).filter(
                Alert.workspace_id == item.workspace_id,
                Alert.type == "inventory_low",
                Alert.reference_type == "inventory_item",
                Alert.reference_id == item.id,
                Alert.status == AlertStatus.ACTIVE
            ).all()
            
            for alert in active_alerts:
                alert.status = AlertStatus.RESOLVED
                alert.resolved_at = datetime.utcnow()
        
        db.commit()