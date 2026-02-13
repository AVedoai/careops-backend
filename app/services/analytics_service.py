from sqlalchemy.orm import Session
from app.models.form import Form
from app.models.submission import FormSubmission
from app.schemas.analytics import AnalyticsResponse
from datetime import datetime, timedelta

class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    def get_analytics(self, business_id: str) -> AnalyticsResponse:
        """Get analytics for the business"""
        total_forms = self.db.query(Form).filter(Form.business_id == business_id).count()
        total_submissions = self.db.query(FormSubmission).filter(
            FormSubmission.business_id == business_id
        ).count()

        last_30_days = datetime.now() - timedelta(days=30)
        recent_submissions = self.db.query(FormSubmission).filter(
            FormSubmission.business_id == business_id,
            FormSubmission.created_at >= last_30_days
        ).count()

        return AnalyticsResponse(
            total_forms=total_forms,
            total_submissions=total_submissions,
            recent_submissions=recent_submissions
        )