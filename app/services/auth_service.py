from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.user import User, UserRole
from app.models.workspace import Workspace
from app.schemas.auth import UserRegister, UserLogin, Token
from app.utils.security import get_password_hash, verify_password, create_access_token
from app.utils.exceptions import UnauthorizedException, ValidationException
from app.utils.validators import validate_email
from datetime import datetime, timedelta
from typing import Optional


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    async def register_user(self, db: Session, user_data: UserRegister) -> Token:
        """Register new business owner with workspace"""
        
        # Validate email
        if not validate_email(user_data.email):
            raise ValidationException("Invalid email format")
        
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise ValidationException("Email already registered")
        
        try:
            # Create workspace first
            workspace_slug = user_data.business_name.lower().replace(" ", "-").replace("_", "-")
            # Ensure unique slug
            existing_workspace = db.query(Workspace).filter(Workspace.slug == workspace_slug).first()
            counter = 1
            original_slug = workspace_slug
            while existing_workspace:
                workspace_slug = f"{original_slug}-{counter}"
                existing_workspace = db.query(Workspace).filter(Workspace.slug == workspace_slug).first()
                counter += 1
            
            workspace = Workspace(
                name=user_data.business_name,
                slug=workspace_slug,
                contact_email=user_data.email,
                is_active=False,  # Requires onboarding
                onboarding_completed=False,
                onboarding_step=1
            )
            db.add(workspace)
            db.flush()  # Get workspace ID
            
            # Create owner user
            hashed_password = get_password_hash(user_data.password)
            user = User(
                email=user_data.email,
                hashed_password=hashed_password,
                full_name=user_data.full_name,
                role=UserRole.OWNER,
                workspace_id=workspace.id,
                is_active=True,
                can_manage_inbox=True,
                can_manage_bookings=True,
                can_view_forms=True,
                can_view_inventory=True
            )
            db.add(user)
            db.commit()
            
            # Create access token
            access_token = create_access_token(data={"sub": str(user.id)})
            
            return Token(access_token=access_token, token_type="bearer")
            
        except IntegrityError as e:
            db.rollback()
            raise ValidationException("Email already registered")
        except Exception as e:
            db.rollback()
            raise ValidationException(f"Registration failed: {str(e)}")
    
    async def authenticate_user(self, db: Session, user_data: UserLogin) -> Token:
        """Authenticate user and return token"""
        
        user = db.query(User).filter(User.email == user_data.email).first()
        
        if not user or not user.is_active:
            raise UnauthorizedException("Invalid credentials")
        
        if not verify_password(user_data.password, user.hashed_password):
            raise UnauthorizedException("Invalid credentials")
        
        # Create access token
        access_token = create_access_token(data={"sub": str(user.id)})
        
        return Token(access_token=access_token, token_type="bearer")
    
    async def refresh_token(self, db: Session, user: User) -> Token:
        """Refresh access token"""
        
        if not user or not user.is_active:
            raise UnauthorizedException("User not active")
        
        # Create new access token
        access_token = create_access_token(data={"sub": str(user.id)})
        
        return Token(access_token=access_token, token_type="bearer")
    
    def authenticate_user(self, email: str, password: str) -> Optional[Token]:
        """Authenticate user and return token"""
        user = self.db.query(User).filter(User.email == email).first()
        if not user or not verify_password(password, user.hashed_password):
            return None

        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        return Token(access_token=access_token, token_type="bearer")