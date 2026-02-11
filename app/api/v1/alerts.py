from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.api.deps import get_current_workspace
from app.schemas.alert import AlertResponse
from app.services.alert_service import AlertService
from app.models.workspace import Workspace
from app.models.user import User

router = APIRouter()
alert_service = AlertService()

@router.get("/", response_model=List[AlertResponse])
async def list_alerts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: str = Query("active"),
    severity: str = Query("all"),
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db)
):
    """List alerts"""
    return await alert_service.list_alerts(db, workspace.id, skip, limit, status, severity)

@router.put("/{alert_id}/dismiss")
async def dismiss_alert(
    alert_id: int,
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db)
):
    """Dismiss alert"""
    await alert_service.dismiss_alert(db, alert_id, workspace.id)
    return {"message": "Alert dismissed"}

@router.put("/{alert_id}/resolve")
async def resolve_alert(
    alert_id: int,
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db)
):
    """Resolve alert"""
    await alert_service.resolve_alert(db, alert_id, workspace.id)
    return {"message": "Alert resolved"}