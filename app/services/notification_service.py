from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from app.models.user import User
from app.models.submission import FormSubmission
from app.schemas.notification import EmailNotification
from sqlalchemy.orm import Session
import os

class NotificationService:
    def __init__(self, db: Session):
        self.db = db
        self.mail_config = ConnectionConfig(
            MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
            MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
            MAIL_FROM=os.getenv("MAIL_FROM"),
            MAIL_PORT=587,
            MAIL_SERVER="smtp.gmail.com",
            MAIL_TLS=True,
            MAIL_SSL=False
        )

    def send_email_notification(self, notification: EmailNotification):
        """Send email notification"""
        message = MessageSchema(
            subject=notification.subject,
            recipients=notification.recipients,
            body=notification.body,
            subtype="html"
        )

        fm = FastMail(self.mail_config)
        fm.send_message(message)

    def notify_submission(self, submission_id: str):
        """Notify staff about a new submission"""
        submission = self.db.query(FormSubmission).filter(
            FormSubmission.id == submission_id
        ).first()

        if submission:
            staff = self.db.query(User).filter(User.business_id == submission.business_id).all()
            recipients = [user.email for user in staff if user.email]

            notification = EmailNotification(
                subject="New Submission Received",
                recipients=recipients,
                body=f"A new submission has been received for form {submission.form_id}."
            )
            self.send_email_notification(notification)