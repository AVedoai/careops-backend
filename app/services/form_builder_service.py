from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, UploadFile
from app.models.form import Form, CustomFormSubmission, Lead, FormType, SubmissionStatus
from app.models.workspace import Workspace
from app.schemas.form import (
    FormCreateCustom, FormCreateExternal, FormCreateDocument, 
    FormUpdate, FormResponse, FormSubmissionCreate, FormSubmissionUpdate,
    CustomFormSubmissionResponse, PublicFormResponse, FormAnalytics
)
import uuid
import secrets
from datetime import datetime, timedelta
import json

class FormBuilderService:
    """Service for custom form builder operations"""
    
    def __init__(self):
        self.share_link_prefix = "/f/"
    
    async def create_custom_form(
        self, db: Session, workspace_id: int, user_id: int, form_data: FormCreateCustom
    ) -> FormResponse:
        """Create a new custom form with field builder"""
        share_link = self._generate_share_link()
        embed_code = self._generate_embed_code(share_link)
        
        db_form = Form(
            workspace_id=workspace_id,
            created_by=user_id,
            name=form_data.name,
            description=form_data.description,
            type=FormType.CUSTOM,
            fields=[field.dict() for field in form_data.fields],
            settings=form_data.settings.dict(),
            share_link=share_link,
            embed_code=embed_code,
            is_published=False
        )
        
        db.add(db_form)
        db.commit()
        db.refresh(db_form)
        
        return FormResponse.from_orm(db_form)
    
    async def create_external_form(
        self, db: Session, workspace_id: int, user_id: int, form_data: FormCreateExternal
    ) -> FormResponse:
        """Create a form that links to external service (Google Forms, Typeform, etc.)"""
        db_form = Form(
            workspace_id=workspace_id,
            created_by=user_id,
            name=form_data.name,
            description=form_data.description,
            type=FormType.EXTERNAL_LINK,
            external_url=form_data.external_url,
            is_published=True  # External forms are immediately "published"
        )
        
        db.add(db_form)
        db.commit()
        db.refresh(db_form)
        
        return FormResponse.from_orm(db_form)
    
    async def create_document_form(
        self, db: Session, workspace_id: int, user_id: int, 
        form_data: FormCreateDocument, file: UploadFile
    ) -> FormResponse:
        """Create a document-based form (legacy support)"""
        # Upload file to storage (implement based on your storage solution)
        file_url = await self._upload_file(file)
        
        db_form = Form(
            workspace_id=workspace_id,
            created_by=user_id,
            name=form_data.name,
            description=form_data.description,
            type=FormType.DOCUMENT,
            file_url=file_url,
            is_published=True
        )
        
        db.add(db_form)
        db.commit()
        db.refresh(db_form)
        
        return FormResponse.from_orm(db_form)
    
    async def get_form(self, db: Session, form_id: int, workspace_id: int) -> FormResponse:
        """Get form by ID"""
        db_form = db.query(Form).filter(
            and_(Form.id == form_id, Form.workspace_id == workspace_id)
        ).first()
        
        if not db_form:
            raise HTTPException(status_code=404, detail="Form not found")
        
        return FormResponse.from_orm(db_form)
    
    async def get_public_form(self, db: Session, share_link: str) -> PublicFormResponse:
        """Get form by public share link (no auth required)"""
        db_form = db.query(Form).filter(
            and_(
                Form.share_link == share_link,
                Form.is_published == True,
                Form.is_active == True
            )
        ).first()
        
        if not db_form:
            raise HTTPException(status_code=404, detail="Form not found or not published")
        
        # Increment view count
        db_form.views_count += 1
        db.commit()
        
        # Get workspace name for branding
        workspace = db.query(Workspace).filter(Workspace.id == db_form.workspace_id).first()
        
        return PublicFormResponse(
            id=db_form.id,
            name=db_form.name,
            description=db_form.description,
            fields=db_form.fields or [],
            settings=db_form.settings or {},
            workspace_name=workspace.name if workspace else None
        )
    
    async def update_form(
        self, db: Session, form_id: int, workspace_id: int, form_data: FormUpdate
    ) -> FormResponse:
        """Update form"""
        db_form = db.query(Form).filter(
            and_(Form.id == form_id, Form.workspace_id == workspace_id)
        ).first()
        
        if not db_form:
            raise HTTPException(status_code=404, detail="Form not found")
        
        update_data = form_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if field == "fields" and value:
                value = [field.dict() if hasattr(field, 'dict') else field for field in value]
            elif field == "settings" and value:
                value = value.dict() if hasattr(value, 'dict') else value
            setattr(db_form, field, value)
        
        db.commit()
        db.refresh(db_form)
        
        return FormResponse.from_orm(db_form)
    
    async def publish_form(self, db: Session, form_id: int, workspace_id: int) -> FormResponse:
        """Publish or unpublish form"""
        db_form = db.query(Form).filter(
            and_(Form.id == form_id, Form.workspace_id == workspace_id)
        ).first()
        
        if not db_form:
            raise HTTPException(status_code=404, detail="Form not found")
        
        db_form.is_published = not db_form.is_published
        
        # Generate share link if publishing for first time
        if db_form.is_published and not db_form.share_link:
            db_form.share_link = self._generate_share_link()
            db_form.embed_code = self._generate_embed_code(db_form.share_link)
        
        db.commit()
        db.refresh(db_form)
        
        return FormResponse.from_orm(db_form)
    
    async def duplicate_form(
        self, db: Session, form_id: int, workspace_id: int, user_id: int
    ) -> FormResponse:
        """Duplicate a form"""
        original_form = db.query(Form).filter(
            and_(Form.id == form_id, Form.workspace_id == workspace_id)
        ).first()
        
        if not original_form:
            raise HTTPException(status_code=404, detail="Form not found")
        
        # Create duplicate
        duplicate_form = Form(
            workspace_id=workspace_id,
            created_by=user_id,
            name=f"{original_form.name} (Copy)",
            description=original_form.description,
            type=original_form.type,
            fields=original_form.fields,
            settings=original_form.settings,
            external_url=original_form.external_url,
            file_url=original_form.file_url,
            is_published=False  # Duplicates start unpublished
        )
        
        if original_form.type == FormType.CUSTOM:
            duplicate_form.share_link = self._generate_share_link()
            duplicate_form.embed_code = self._generate_embed_code(duplicate_form.share_link)
        
        db.add(duplicate_form)
        db.commit()
        db.refresh(duplicate_form)
        
        return FormResponse.from_orm(duplicate_form)
    
    async def delete_form(self, db: Session, form_id: int, workspace_id: int) -> bool:
        """Delete form"""
        db_form = db.query(Form).filter(
            and_(Form.id == form_id, Form.workspace_id == workspace_id)
        ).first()
        
        if not db_form:
            raise HTTPException(status_code=404, detail="Form not found")
        
        db.delete(db_form)
        db.commit()
        
        return True
    
    async def list_forms(
        self, db: Session, workspace_id: int, 
        page: int = 1, per_page: int = 20, 
        form_type: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[FormResponse]:
        """List forms with pagination and filtering"""
        query = db.query(Form).filter(Form.workspace_id == workspace_id)
        
        if form_type:
            query = query.filter(Form.type == form_type)
        
        if search:
            query = query.filter(
                or_(
                    Form.name.ilike(f"%{search}%"),
                    Form.description.ilike(f"%{search}%")
                )
            )
        
        query = query.order_by(Form.created_at.desc())
        
        # Pagination
        offset = (page - 1) * per_page
        forms = query.offset(offset).limit(per_page).all()
        
        return [FormResponse.from_orm(form) for form in forms]
    
    async def get_form_analytics(
        self, db: Session, form_id: int, workspace_id: int
    ) -> FormAnalytics:
        """Get form analytics"""
        db_form = db.query(Form).filter(
            and_(Form.id == form_id, Form.workspace_id == workspace_id)
        ).first()
        
        if not db_form:
            raise HTTPException(status_code=404, detail="Form not found")
        
        completion_rate = 0
        if db_form.views_count > 0:
            completion_rate = (db_form.submissions_count / db_form.views_count) * 100
        
        return FormAnalytics(
            form_id=form_id,
            views=db_form.views_count,
            submissions=db_form.submissions_count,
            completion_rate=completion_rate
        )
    
    # Submission Methods
    async def submit_form(
        self, db: Session, share_link: str, 
        submission_data: FormSubmissionCreate,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> CustomFormSubmissionResponse:
        """Submit form response (public endpoint)"""
        
        # Get form
        db_form = db.query(Form).filter(
            and_(
                Form.share_link == share_link,
                Form.is_published == True,
                Form.is_active == True
            )
        ).first()
        
        if not db_form:
            raise HTTPException(status_code=404, detail="Form not found")
        
        # Validate submission data against form fields
        if db_form.fields:
            self._validate_submission_data(db_form.fields, submission_data.submitted_data)
        
        # Create submission
        db_submission = CustomFormSubmission(
            form_id=db_form.id,
            workspace_id=db_form.workspace_id,
            submitted_data=submission_data.submitted_data,
            submitter_email=submission_data.submitter_email,
            submitter_name=submission_data.submitter_name,
            submitter_phone=submission_data.submitter_phone,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        db.add(db_submission)
        
        # Update form submission count
        db_form.submissions_count += 1
        
        # Create lead if email provided
        if submission_data.submitter_email:
            lead = Lead(
                workspace_id=db_form.workspace_id,
                form_submission_id=None,  # Will be set after submission is created
                name=submission_data.submitter_name or "Unknown",
                email=submission_data.submitter_email,
                phone=submission_data.submitter_phone,
                source="FORM"
            )
            db.add(lead)
        
        db.commit()
        db.refresh(db_submission)
        
        # Update lead with submission ID
        if submission_data.submitter_email:
            lead.form_submission_id = db_submission.id
            db.commit()
        
        return CustomFormSubmissionResponse.from_orm(db_submission)
    
    async def list_submissions(
        self, db: Session, workspace_id: int,
        page: int = 1, per_page: int = 20,
        form_id: Optional[int] = None,
        status: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[CustomFormSubmissionResponse]:
        """List form submissions"""
        query = db.query(CustomFormSubmission).filter(
            CustomFormSubmission.workspace_id == workspace_id
        )
        
        if form_id:
            query = query.filter(CustomFormSubmission.form_id == form_id)
        
        if status:
            query = query.filter(CustomFormSubmission.status == status)
        
        if search:
            query = query.filter(
                or_(
                    CustomFormSubmission.submitter_name.ilike(f"%{search}%"),
                    CustomFormSubmission.submitter_email.ilike(f"%{search}%"),
                    CustomFormSubmission.submitter_phone.ilike(f"%{search}%")
                )
            )
        
        query = query.order_by(CustomFormSubmission.created_at.desc())
        
        # Pagination
        offset = (page - 1) * per_page
        submissions = query.offset(offset).limit(per_page).all()
        
        return [CustomFormSubmissionResponse.from_orm(sub) for sub in submissions]
    
    async def get_submission(
        self, db: Session, submission_id: int, workspace_id: int
    ) -> CustomFormSubmissionResponse:
        """Get submission details"""
        submission = db.query(CustomFormSubmission).filter(
            and_(
                CustomFormSubmission.id == submission_id,
                CustomFormSubmission.workspace_id == workspace_id
            )
        ).first()
        
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")
        
        return CustomFormSubmissionResponse.from_orm(submission)
    
    async def update_submission(
        self, db: Session, submission_id: int, workspace_id: int,
        update_data: FormSubmissionUpdate
    ) -> CustomFormSubmissionResponse:
        """Update submission status, notes, etc."""
        submission = db.query(CustomFormSubmission).filter(
            and_(
                CustomFormSubmission.id == submission_id,
                CustomFormSubmission.workspace_id == workspace_id
            )
        ).first()
        
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")
        
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(submission, field, value)
        
        db.commit()
        db.refresh(submission)
        
        return CustomFormSubmissionResponse.from_orm(submission)
    
    # Helper Methods
    def _generate_share_link(self) -> str:
        """Generate unique share link"""
        return f"{self.share_link_prefix}{secrets.token_urlsafe(8)}"
    
    def _generate_embed_code(self, share_link: str) -> str:
        """Generate HTML embed code"""
        return f'<iframe src="https://your-domain.com{share_link}" width="100%" height="600" frameborder="0"></iframe>'
    
    async def _upload_file(self, file: UploadFile) -> str:
        """Upload file to storage - implement based on your storage solution"""
        # This is a placeholder - implement with your actual file storage
        return f"https://your-storage.com/uploads/{file.filename}"
    
    def _validate_submission_data(self, fields: List[Dict], submitted_data: Dict[str, Any]):
        """Validate submitted data against form fields"""
        required_fields = [field['id'] for field in fields if field.get('required', False)]
        
        for field_id in required_fields:
            if field_id not in submitted_data or not submitted_data[field_id]:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Required field '{field_id}' is missing"
                )