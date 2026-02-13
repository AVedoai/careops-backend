from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api import deps
from app.schemas.auth import Token, LoginRequest
from app.services.auth_service import AuthService

router = APIRouter()

@router.post("/login", response_model=Token)
def login(
    *,
    db: Session = Depends(deps.get_db),
    login_request: LoginRequest
):
    """Authenticate user and return token"""
    auth_service = AuthService(db)
    token = auth_service.authenticate_user(
        email=login_request.email, password=login_request.password
    )
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    return token

@router.get("/me")
def get_current_user(
    *,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_active_user)
):
    """Get current authenticated user"""
    return current_user