from fastapi import APIRouter, Depends, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.api.deps import get_current_workspace, get_current_owner
from app.schemas.form import FormResponse, FormCreate, FormSubmissionResponse
from app.services.form_service import FormService
from app.models.workspace import Workspace
from app.models.user import User

router = APIRouter()
form_service = FormService()

@router.get("/", response_model=List[FormResponse])
async def list_forms(
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db)
):
    """List forms"""
    return await form_service.list_forms(db, workspace.id)

@router.post("/", response_model=FormResponse)
async def upload_form(
    name: str,
    description: str = "",
    file: UploadFile = File(...),
    workspace: Workspace = Depends(get_current_workspace),
    current_user: User = Depends(get_current_owner),
    db: Session = Depends(get_db)
):
    """Upload form document"""
    form_data = FormCreate(name=name, description=description)
    return await form_service.upload_form(db, workspace.id, form_data, file)

@router.get("/{form_id}", response_model=FormResponse)
async def get_form(
    form_id: int,
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db)
):
    """Get form details"""
    return await form_service.get_form(db, form_id, workspace.id)

@router.delete("/{form_id}")
async def delete_form(
    form_id: int,
    workspace: Workspace = Depends(get_current_workspace),
    current_user: User = Depends(get_current_owner),
    db: Session = Depends(get_db)
):
    """Delete form"""
    await form_service.delete_form(db, form_id, workspace.id)
    return {"message": "Form deleted successfully"}

@router.get("/submissions", response_model=List[FormSubmissionResponse])
async def list_submissions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: str = Query("all"),
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db)
):
    """List form submissions"""
    return await form_service.list_submissions(db, workspace.id, skip, limit, status)

@router.put("/submissions/{submission_id}")
async def update_submission_status(
    submission_id: int,
    status: str,
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db)
):
    """Update submission status"""
    return await form_service.update_submission_status(db, submission_id, workspace.id, status)