import csv
import io
from sqlalchemy.orm import Session
from app.models.submission import FormSubmission
from typing import Optional
from datetime import datetime

class ExportService:
    def __init__(self, db: Session):
        self.db = db

    def export_submissions(self, business_id: str, form_id: Optional[str] = None) -> dict:
        """Export submissions to CSV"""
        query = self.db.query(FormSubmission).filter(
            FormSubmission.business_id == business_id
        )

        if form_id:
            query = query.filter(FormSubmission.form_id == form_id)

        submissions = query.all()

        output = io.StringIO()
        fieldnames = ['id', 'created_at', 'status', 'submitter_email', 'submitter_name', 'submitter_phone']
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for submission in submissions:
            writer.writerow({
                'id': submission.id,
                'created_at': submission.created_at.isoformat(),
                'status': submission.status,
                'submitter_email': submission.submitter_email,
                'submitter_name': submission.submitter_name,
                'submitter_phone': submission.submitter_phone
            })

        return {
            "filename": f"submissions_{datetime.now().strftime('%Y%m%d')}.csv",
            "content": output.getvalue()
        }