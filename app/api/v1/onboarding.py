from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.database import get_db
from app.api.deps import get_current_owner
from app.services.workspace_service import WorkspaceService
from app.models.user import User

router = APIRouter()
workspace_service = WorkspaceService()

@router.get("/status")
async def get_onboarding_status(
    current_user: User = Depends(get_current_owner),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get onboarding progress"""
    return await workspace_service.get_onboarding_status(db, current_user.workspace_id)

@router.put("/step")
async def update_onboarding_step(
    step: int,
    current_user: User = Depends(get_current_owner),
    db: Session = Depends(get_db)
):
    """Update onboarding step"""
    return await workspace_service.update_onboarding_step(db, current_user.workspace_id, step)

@router.post("/complete")
async def complete_onboarding(
    current_user: User = Depends(get_current_owner),
    db: Session = Depends(get_db)
):
    """Complete onboarding"""
    return await workspace_service.complete_onboarding(db, current_user.workspace_id)