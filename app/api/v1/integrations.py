from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.database import get_db
from app.api.deps import get_current_workspace, get_current_owner
from app.schemas.integration import IntegrationResponse, IntegrationCreate, IntegrationUpdate
from app.services.integration_service import IntegrationService
from app.models.workspace import Workspace
from app.models.user import User

router = APIRouter()
integration_service = IntegrationService()

@router.get("/", response_model=List[IntegrationResponse])
async def list_integrations(
    workspace: Workspace = Depends(get_current_workspace),
    current_user: User = Depends(get_current_owner),
    db: Session = Depends(get_db)
):
    """List integrations"""
    return await integration_service.list_integrations(db, workspace.id)

@router.post("/", response_model=IntegrationResponse)
async def add_integration(
    integration_data: IntegrationCreate,
    workspace: Workspace = Depends(get_current_workspace),
    current_user: User = Depends(get_current_owner),
    db: Session = Depends(get_db)
):
    """Add integration"""
    return await integration_service.create_integration(db, workspace.id, integration_data)

@router.put("/{integration_id}", response_model=IntegrationResponse)
async def update_integration(
    integration_id: int,
    integration_data: IntegrationUpdate,
    workspace: Workspace = Depends(get_current_workspace),
    current_user: User = Depends(get_current_owner),
    db: Session = Depends(get_db)
):
    """Update integration"""
    return await integration_service.update_integration(db, integration_id, workspace.id, integration_data)

@router.delete("/{integration_id}")
async def remove_integration(
    integration_id: int,
    workspace: Workspace = Depends(get_current_workspace),
    current_user: User = Depends(get_current_owner),
    db: Session = Depends(get_db)
):
    """Remove integration"""
    await integration_service.delete_integration(db, integration_id, workspace.id)
    return {"message": "Integration removed successfully"}

@router.post("/{integration_id}/test")
async def test_integration(
    integration_id: int,
    workspace: Workspace = Depends(get_current_workspace),
    current_user: User = Depends(get_current_owner),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Test integration connection"""
    return await integration_service.test_integration(db, integration_id, workspace.id)