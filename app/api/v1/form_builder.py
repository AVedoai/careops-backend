from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.api.deps import get_current_workspace, get_current_owner
from app.schemas.form import (
    FormCreateCustom, FormCreateExternal, FormCreateDocument, FormUpdate,
    FormResponse, FormListResponse, PublicFormResponse,
    FormSubmissionCreate, FormSubmissionUpdate, CustomFormSubmissionResponse,
    FormSubmissionListResponse, FormAnalytics
)
from app.services.form_builder_service import FormBuilderService
from app.models.workspace import Workspace
from app.models.user import User

router = APIRouter()
form_service = FormBuilderService()

# Form Management Endpoints

@router.get("/", response_model=FormListResponse)
async def list_forms(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    form_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db)
):
    """List all forms for the workspace"""
    forms = await form_service.list_forms(
        db, workspace.id, page, per_page, form_type, search
    )
    
    total = len(forms)  # You may want to implement proper count query
    
    return FormListResponse(
        forms=forms,
        total=total,
        page=page,
        per_page=per_page
    )

@router.post("/custom", response_model=FormResponse)
async def create_custom_form(
    form_data: FormCreateCustom,
    workspace: Workspace = Depends(get_current_workspace),
    current_user: User = Depends(get_current_owner),
    db: Session = Depends(get_db)
):
    """Create a new custom form with drag & drop builder"""
    return await form_service.create_custom_form(
        db, workspace.id, current_user.id, form_data
    )

@router.post("/external", response_model=FormResponse)
async def create_external_form(
    form_data: FormCreateExternal,
    workspace: Workspace = Depends(get_current_workspace),
    current_user: User = Depends(get_current_owner),
    db: Session = Depends(get_db)
):
    """Create a form that links to external service (Google Forms, Typeform, etc.)"""
    return await form_service.create_external_form(
        db, workspace.id, current_user.id, form_data
    )

@router.post("/document", response_model=FormResponse)
async def create_document_form(
    name: str,
    description: str = "",
    file: UploadFile = File(...),
    workspace: Workspace = Depends(get_current_workspace),
    current_user: User = Depends(get_current_owner),
    db: Session = Depends(get_db)
):
    """Create a document-based form (PDF upload)"""
    form_data = FormCreateDocument(name=name, description=description)
    return await form_service.create_document_form(
        db, workspace.id, current_user.id, form_data, file
    )

@router.get("/{form_id}", response_model=FormResponse)
async def get_form(
    form_id: int,
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db)
):
    """Get form details"""
    return await form_service.get_form(db, form_id, workspace.id)

@router.put("/{form_id}", response_model=FormResponse)
async def update_form(
    form_id: int,
    form_data: FormUpdate,
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db)
):
    """Update form"""
    return await form_service.update_form(db, form_id, workspace.id, form_data)

@router.post("/{form_id}/publish", response_model=FormResponse)
async def publish_form(
    form_id: int,
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db)
):
    """Publish or unpublish form"""
    return await form_service.publish_form(db, form_id, workspace.id)

@router.post("/{form_id}/duplicate", response_model=FormResponse)
async def duplicate_form(
    form_id: int,
    workspace: Workspace = Depends(get_current_workspace),
    current_user: User = Depends(get_current_owner),
    db: Session = Depends(get_db)
):
    """Duplicate a form"""
    return await form_service.duplicate_form(db, form_id, workspace.id, current_user.id)

@router.delete("/{form_id}")
async def delete_form(
    form_id: int,
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db)
):
    """Delete form"""
    success = await form_service.delete_form(db, form_id, workspace.id)
    return {"success": success}

@router.get("/{form_id}/analytics", response_model=FormAnalytics)
async def get_form_analytics(
    form_id: int,
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db)
):
    """Get form analytics"""
    return await form_service.get_form_analytics(db, form_id, workspace.id)

# Submission Management Endpoints

@router.get("/submissions/", response_model=FormSubmissionListResponse)
async def list_submissions(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    form_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db)
):
    """List form submissions"""
    submissions = await form_service.list_submissions(
        db, workspace.id, page, per_page, form_id, status, search
    )
    
    total = len(submissions)  # Implement proper count query
    
    return FormSubmissionListResponse(
        submissions=submissions,
        total=total,
        page=page,
        per_page=per_page
    )

@router.get("/submissions/{submission_id}", response_model=CustomFormSubmissionResponse)
async def get_submission(
    submission_id: int,
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db)
):
    """Get submission details"""
    return await form_service.get_submission(db, submission_id, workspace.id)

@router.put("/submissions/{submission_id}", response_model=CustomFormSubmissionResponse)
async def update_submission(
    submission_id: int,
    update_data: FormSubmissionUpdate,
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db)
):
    """Update submission status, notes, assignment"""
    return await form_service.update_submission(
        db, submission_id, workspace.id, update_data
    )

@router.post("/submissions/{submission_id}/convert-to-booking")
async def convert_submission_to_booking(
    submission_id: int,
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db)
):
    """Convert form submission to booking"""
    # This will integrate with your existing booking system
    # Implementation depends on your booking service
    return {"message": "Submission converted to booking"}

# Export Endpoints

@router.get("/{form_id}/export")
async def export_form_submissions(
    form_id: int,
    format: str = Query("csv", regex="^(csv|excel|json)$"),
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db)
):
    """Export form submissions to CSV, Excel, or JSON"""
    # Implementation for exporting submissions
    return {"message": f"Exporting form {form_id} submissions as {format}"}

# Advanced Features

@router.get("/{form_id}/share-link")
async def get_share_link(
    form_id: int,
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db)
):
    """Get shareable link for form"""
    form = await form_service.get_form(db, form_id, workspace.id)
    if not form.is_published:
        raise HTTPException(status_code=400, detail="Form must be published to get share link")
    
    return {
        "share_link": form.share_link,
        "embed_code": form.embed_code,
        "full_url": f"https://your-domain.com{form.share_link}"
    }

@router.post("/{form_id}/regenerate-link")
async def regenerate_share_link(
    form_id: int,
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db)
):
    """Regenerate share link for security"""
    # Implementation to regenerate share link
    return {"message": "Share link regenerated"}

# Form Templates

@router.get("/templates")
async def list_form_templates(
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db)
):
    """List available form templates"""
    # Return predefined form templates
    templates = [
        {
            "id": "contact-form",
            "name": "Contact Form",
            "description": "Basic contact form with name, email, and message",
            "fields": [
                {"id": "name", "type": "text", "label": "Full Name", "required": True},
                {"id": "email", "type": "email", "label": "Email", "required": True},
                {"id": "message", "type": "textarea", "label": "Message", "required": True}
            ]
        },
        {
            "id": "appointment-booking",
            "name": "Appointment Booking",
            "description": "Form for booking appointments",
            "fields": [
                {"id": "name", "type": "text", "label": "Full Name", "required": True},
                {"id": "email", "type": "email", "label": "Email", "required": True},
                {"id": "phone", "type": "phone", "label": "Phone Number", "required": True},
                {"id": "service", "type": "select", "label": "Service Type", "options": ["Consultation", "Follow-up", "Emergency"], "required": True},
                {"id": "date", "type": "date", "label": "Preferred Date", "required": True},
                {"id": "time", "type": "time", "label": "Preferred Time", "required": True},
                {"id": "notes", "type": "textarea", "label": "Additional Notes"}
            ]
        },
        {
            "id": "patient-intake",
            "name": "Patient Intake Form", 
            "description": "Comprehensive patient intake form",
            "fields": [
                {"id": "personal_info", "type": "section", "label": "Personal Information"},
                {"id": "name", "type": "text", "label": "Full Name", "required": True},
                {"id": "email", "type": "email", "label": "Email", "required": True},
                {"id": "phone", "type": "phone", "label": "Phone Number", "required": True},
                {"id": "dob", "type": "date", "label": "Date of Birth", "required": True},
                {"id": "medical_info", "type": "section", "label": "Medical Information"},
                {"id": "symptoms", "type": "checkbox", "label": "Current Symptoms", "options": ["Fever", "Cough", "Headache", "Fatigue", "Nausea"]},
                {"id": "medications", "type": "textarea", "label": "Current Medications"},
                {"id": "allergies", "type": "textarea", "label": "Allergies"},
                {"id": "emergency_contact", "type": "text", "label": "Emergency Contact"},
                {"id": "documents", "type": "file", "label": "Upload Medical Records", "accept": ".pdf,.jpg,.png"}
            ]
        }
    ]
    
    return {"templates": templates}

@router.post("/from-template/{template_id}", response_model=FormResponse)
async def create_form_from_template(
    template_id: str,
    name: str,
    description: str = "",
    workspace: Workspace = Depends(get_current_workspace),
    current_user: User = Depends(get_current_owner),
    db: Session = Depends(get_db)
):
    """Create form from template"""
    # Get template and create form
    # This is a simplified implementation - you'd fetch from templates
    if template_id == "contact-form":
        fields = [
            {"id": "name", "type": "text", "label": "Full Name", "required": True, "order": 1},
            {"id": "email", "type": "email", "label": "Email", "required": True, "order": 2},
            {"id": "message", "type": "textarea", "label": "Message", "required": True, "order": 3}
        ]
    else:
        raise HTTPException(status_code=404, detail="Template not found")
    
    form_data = FormCreateCustom(
        name=name,
        description=description,
        fields=fields
    )
    
    return await form_service.create_custom_form(db, workspace.id, current_user.id, form_data)