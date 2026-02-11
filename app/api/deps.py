from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models.user import User, UserRole
from app.models.workspace import Workspace
from app.utils.security import decode_access_token
from app.utils.exceptions import UnauthorizedException, ForbiddenException

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if payload is None:
        raise UnauthorizedException("Invalid authentication credentials")
    
    user_id: int = payload.get("sub")
    if user_id is None:
        raise UnauthorizedException("Invalid authentication credentials")
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.is_active:
        raise UnauthorizedException("User not found or inactive")
    
    return user

def get_current_owner(current_user: User = Depends(get_current_user)) -> User:
    """Require owner role"""
    if current_user.role != UserRole.OWNER:
        raise ForbiddenException("Owner permission required")
    return current_user

def get_current_workspace(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Workspace:
    """Get current user's workspace"""
    if not current_user.workspace_id:
        raise ForbiddenException("No workspace associated")
    
    workspace = db.query(Workspace).filter(Workspace.id == current_user.workspace_id).first()
    if not workspace:
        raise ForbiddenException("Workspace not found")
    
    return workspace

def check_inbox_permission(current_user: User = Depends(get_current_user)):
    """Check if user can manage inbox"""
    if current_user.role == UserRole.OWNER:
        return current_user
    if not current_user.can_manage_inbox:
        raise ForbiddenException("Inbox permission required")
    return current_user

def check_booking_permission(current_user: User = Depends(get_current_user)):
    """Check if user can manage bookings"""
    if current_user.role == UserRole.OWNER:
        return current_user
    if not current_user.can_manage_bookings:
        raise ForbiddenException("Booking permission required")
    return current_user