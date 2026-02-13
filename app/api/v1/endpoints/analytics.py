from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api import deps
from app.services.analytics_service import AnalyticsService
from app.schemas.analytics import AnalyticsResponse

router = APIRouter()

@router.get("/", response_model=AnalyticsResponse)
def get_analytics(
    *,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_active_user)
):
    """Get analytics for the business"""
    service = AnalyticsService(db)
    return service.get_analytics(current_user.business_id)