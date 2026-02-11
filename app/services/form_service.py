from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi import UploadFile, HTTPException
from datetime import datetime, date
import uuid
import requests
import os
from app.models.form import Form, FormSubmission
from app.schemas.form import FormCreate
from app.utils.exceptions import NotFoundException, ValidationException


class FormService:
    async def list_forms(self, db: Session, workspace_id: int) -> List[Form]:
        """List all forms for workspace"""
        return db.query(Form).filter(
            Form.workspace_id == workspace_id,
            Form.is_active == True
        ).order_by(Form.name).all()
    
    async def upload_form(
        self, 
        db: Session, 
        workspace_id: int, 
        form_data: FormCreate, 
        file: UploadFile
    ) -> Form:
        """Upload form document"""
        try:
            # Generate unique filename
            file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'pdf'
            unique_filename = f"{uuid.uuid4()}.{file_extension}"
            
            # Upload to Supabase storage
            file_url = await self._upload_to_supabase(file, unique_filename)
            
            form = Form(
                workspace_id=workspace_id,
                name=form_data.name,
                description=form_data.description,
                file_url=file_url,
                is_active=True
            )
            
            db.add(form)
            db.commit()
            db.refresh(form)
            
            return form
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")
    
    async def _upload_to_supabase(self, file: UploadFile, filename: str) -> str:
        """Upload file to Supabase storage"""
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
        bucket = os.getenv("FILE_STORAGE_BUCKET", "forms")
        
        if not supabase_url or not supabase_key:
            # Fallback for development
            return f"https://storage.example.com/forms/{filename}"
        
        # Read file content
        content = await file.read()
        
        # Upload to Supabase
        upload_url = f"{supabase_url}/storage/v1/object/{bucket}/{filename}"
        headers = {
            "Authorization": f"Bearer {supabase_key}",
            "Content-Type": file.content_type or "application/pdf"
        }
        
        response = requests.post(upload_url, headers=headers, data=content)
        
        if response.status_code == 200:
            return f"{supabase_url}/storage/v1/object/public/{bucket}/{filename}"
        else:
            raise Exception(f"Supabase upload failed: {response.text}")
    
    async def get_form(self, db: Session, form_id: int, workspace_id: int) -> Form:
        """Get form by ID"""
        form = db.query(Form).filter(
            Form.id == form_id,
            Form.workspace_id == workspace_id
        ).first()
        
        if not form:
            raise NotFoundException("Form not found")
        
        return form
    
    async def delete_form(self, db: Session, form_id: int, workspace_id: int):
        """Delete form (soft delete)"""
        form = await self.get_form(db, form_id, workspace_id)
        form.is_active = False
        db.commit()
    
    async def list_submissions(
        self,
        db: Session,
        workspace_id: int,
        skip: int = 0,
        limit: int = 100,
        status: str = "all"
    ) -> List[FormSubmission]:
        """List form submissions"""
        from app.models.booking import Booking
        
        query = db.query(FormSubmission).join(Booking).filter(
            Booking.workspace_id == workspace_id
        )
        
        if status != "all":
            query = query.filter(FormSubmission.status == status)
        
        return query.order_by(FormSubmission.created_at.desc()).offset(skip).limit(limit).all()
    
    async def update_submission_status(
        self,
        db: Session,
        submission_id: int,
        workspace_id: int,
        status: str
    ):
        """Update form submission status"""
        from app.models.booking import Booking
        
        submission = db.query(FormSubmission).join(Booking).filter(
            FormSubmission.id == submission_id,
            Booking.workspace_id == workspace_id
        ).first()
        
        if not submission:
            raise NotFoundException("Form submission not found")
        
        valid_statuses = ["pending", "completed", "overdue"]
        if status not in valid_statuses:
            raise ValidationException(f"Invalid status. Must be one of: {valid_statuses}")
        
        submission.status = status
        if status == "completed":
            submission.completed_at = datetime.utcnow()
        
        db.commit()
        
        return {"message": "Submission status updated"}