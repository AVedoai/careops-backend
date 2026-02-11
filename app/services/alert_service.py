from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app.models.alert import Alert, AlertStatus
from app.schemas.alert import AlertSeverity, AlertCreate
from app.utils.exceptions import NotFoundException


class AlertService:
    async def list_alerts(
        self,
        db: Session,
        workspace_id: int,
        skip: int = 0,
        limit: int = 100,
        status: str = "active",
        severity: str = "all"
    ) -> List[Alert]:
        """List alerts with filters"""
        query = db.query(Alert).filter(
            Alert.workspace_id == workspace_id
        )
        
        if status != "all":
            query = query.filter(Alert.status == status)
        
        if severity != "all":
            query = query.filter(Alert.severity == severity)
        
        return query.order_by(
            Alert.severity.desc(),
            Alert.created_at.desc()
        ).offset(skip).limit(limit).all()
    
    async def get_alert(self, db: Session, alert_id: int, workspace_id: int) -> Alert:
        """Get alert by ID"""
        alert = db.query(Alert).filter(
            Alert.id == alert_id,
            Alert.workspace_id == workspace_id
        ).first()
        
        if not alert:
            raise NotFoundException("Alert not found")
        
        return alert
    
    async def dismiss_alert(self, db: Session, alert_id: int, workspace_id: int):
        """Dismiss alert"""
        alert = await self.get_alert(db, alert_id, workspace_id)
        
        if alert.status == AlertStatus.ACTIVE:
            alert.status = AlertStatus.DISMISSED
            alert.dismissed_at = datetime.utcnow()
            db.commit()
    
    async def resolve_alert(self, db: Session, alert_id: int, workspace_id: int):
        """Resolve alert"""
        alert = await self.get_alert(db, alert_id, workspace_id)
        
        if alert.status == AlertStatus.ACTIVE:
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.utcnow()
            db.commit()
    
    async def create_alert(
        self,
        db: Session,
        workspace_id: int,
        alert_type: str,
        title: str,
        message: str,
        severity: str = "medium",
        reference_type: str = None,
        reference_id: int = None,
        link: str = None
    ) -> Alert:
        """Create new alert"""
        alert = Alert(
            workspace_id=workspace_id,
            type=alert_type,
            status=AlertStatus.ACTIVE,
            severity=severity,
            title=title,
            message=message,
            reference_type=reference_type,
            reference_id=reference_id,
            link=link
        )
        
        db.add(alert)
        db.commit()
        db.refresh(alert)
        
        return alert
    
    async def get_critical_alerts_count(self, db: Session, workspace_id: int) -> int:
        """Get count of critical/high severity active alerts"""
        return db.query(Alert).filter(
            Alert.workspace_id == workspace_id,
            Alert.status == AlertStatus.ACTIVE,
            Alert.severity.in_([AlertSeverity.HIGH, AlertSeverity.CRITICAL])
        ).count()