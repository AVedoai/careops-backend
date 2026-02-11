from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class InventoryItemCreate(BaseModel):
    name: str
    quantity: int
    low_stock_threshold: int = 5
    unit: str = "units"
    usage_per_booking: int = 1

class InventoryItemUpdate(BaseModel):
    quantity: Optional[int] = None
    low_stock_threshold: Optional[int] = None

class InventoryItemResponse(BaseModel):
    id: int
    workspace_id: int
    name: str
    quantity: int
    low_stock_threshold: int
    unit: str
    usage_per_booking: int
    created_at: datetime
    
    class Config:
        from_attributes = True