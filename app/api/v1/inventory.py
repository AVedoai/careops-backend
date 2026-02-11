from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.database import get_db
from app.api.deps import get_current_workspace, get_current_owner
from app.schemas.inventory import InventoryItemResponse, InventoryItemCreate, InventoryItemUpdate
from app.services.inventory_service import InventoryService
from app.models.workspace import Workspace
from app.models.user import User

router = APIRouter()
inventory_service = InventoryService()

@router.get("/", response_model=List[InventoryItemResponse])
async def list_inventory(
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db)
):
    """List inventory items"""
    return await inventory_service.list_items(db, workspace.id)

@router.post("/", response_model=InventoryItemResponse)
async def add_inventory_item(
    item_data: InventoryItemCreate,
    workspace: Workspace = Depends(get_current_workspace),
    current_user: User = Depends(get_current_owner),
    db: Session = Depends(get_db)
):
    """Add inventory item"""
    return await inventory_service.create_item(db, workspace.id, item_data)

@router.get("/alerts")
async def get_low_stock_alerts(
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get low stock alerts"""
    return await inventory_service.get_low_stock_alerts(db, workspace.id)

@router.get("/{item_id}", response_model=InventoryItemResponse)
async def get_inventory_item(
    item_id: int,
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db)
):
    """Get inventory item details"""
    return await inventory_service.get_item(db, item_id, workspace.id)

@router.put("/{item_id}", response_model=InventoryItemResponse)
async def update_inventory_item(
    item_id: int,
    item_data: InventoryItemUpdate,
    workspace: Workspace = Depends(get_current_workspace),
    current_user: User = Depends(get_current_owner),
    db: Session = Depends(get_db)
):
    """Update item quantity"""
    return await inventory_service.update_item(db, item_id, workspace.id, item_data)

@router.delete("/{item_id}")
async def delete_inventory_item(
    item_id: int,
    workspace: Workspace = Depends(get_current_workspace),
    current_user: User = Depends(get_current_owner),
    db: Session = Depends(get_db)
):
    """Delete inventory item"""
    await inventory_service.delete_item(db, item_id, workspace.id)
    return {"message": "Inventory item deleted successfully"}