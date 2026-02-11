from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.database import get_db
from app.api.deps import get_current_user, get_current_workspace, get_current_owner
from app.schemas.workspace import WorkspaceResponse, WorkspaceUpdate
from app.services.workspace_service import WorkspaceService
from app.models.user import User
from app.models.workspace import Workspace

router = APIRouter()
workspace_service = WorkspaceService()

@router.get("/me", response_model=WorkspaceResponse)
async def get_current_workspace_info(
    workspace: Workspace = Depends(get_current_workspace)
):
    """Get current workspace"""
    return workspace

@router.put("/me", response_model=WorkspaceResponse)
async def update_workspace(
    workspace_data: WorkspaceUpdate,
    current_user: User = Depends(get_current_owner),
    db: Session = Depends(get_db)
):
    """Update workspace (owner only)"""
    return await workspace_service.update_workspace(db, current_user.workspace_id, workspace_data)

@router.post("/activate")
async def activate_workspace(
    current_user: User = Depends(get_current_owner),
    db: Session = Depends(get_db)
):
    """Activate workspace after onboarding"""
    return await workspace_service.activate_workspace(db, current_user.workspace_id)

@router.get("/dashboard")
async def get_dashboard_data(
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get dashboard data"""
    return await workspace_service.get_dashboard_data(db, workspace.id)