from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime
from app.models.integration import Integration
from app.schemas.integration import IntegrationCreate, IntegrationUpdate
from app.utils.exceptions import NotFoundException, ValidationException
import json


class IntegrationService:
    async def list_integrations(self, db: Session, workspace_id: int) -> List[Integration]:
        """List all integrations for workspace"""
        return db.query(Integration).filter(
            Integration.workspace_id == workspace_id
        ).order_by(Integration.type, Integration.provider).all()
    
    async def create_integration(
        self, 
        db: Session, 
        workspace_id: int, 
        integration_data: IntegrationCreate
    ) -> Integration:
        """Create new integration"""
        # Validate integration type and provider
        valid_types = ["email", "sms", "calendar"]
        valid_providers = {
            "email": ["sendgrid", "mailgun"],
            "sms": ["twilio"],
            "calendar": ["google"]
        }
        
        if integration_data.type not in valid_types:
            raise ValidationException(f"Invalid integration type: {integration_data.type}")
        
        if integration_data.provider not in valid_providers[integration_data.type]:
            raise ValidationException(f"Invalid provider for {integration_data.type}: {integration_data.provider}")
        
        # Check if integration already exists
        existing = db.query(Integration).filter(
            Integration.workspace_id == workspace_id,
            Integration.type == integration_data.type,
            Integration.provider == integration_data.provider
        ).first()
        
        if existing:
            raise ValidationException(f"{integration_data.provider} {integration_data.type} integration already exists")
        
        # TODO: Encrypt credentials before storing
        integration = Integration(
            workspace_id=workspace_id,
            type=integration_data.type,
            provider=integration_data.provider,
            credentials=integration_data.credentials,
            is_active=True
        )
        
        db.add(integration)
        db.commit()
        db.refresh(integration)
        
        return integration
    
    async def get_integration(self, db: Session, integration_id: int, workspace_id: int) -> Integration:
        """Get integration by ID"""
        integration = db.query(Integration).filter(
            Integration.id == integration_id,
            Integration.workspace_id == workspace_id
        ).first()
        
        if not integration:
            raise NotFoundException("Integration not found")
        
        return integration
    
    async def update_integration(
        self, 
        db: Session, 
        integration_id: int, 
        workspace_id: int, 
        integration_data: IntegrationUpdate
    ) -> Integration:
        """Update integration"""
        integration = await self.get_integration(db, integration_id, workspace_id)
        
        # Update credentials if provided
        if integration_data.credentials:
            # TODO: Encrypt new credentials
            integration.credentials = integration_data.credentials
        
        if integration_data.is_active is not None:
            integration.is_active = integration_data.is_active
        
        integration.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(integration)
        
        return integration
    
    async def delete_integration(self, db: Session, integration_id: int, workspace_id: int):
        """Delete integration"""
        integration = await self.get_integration(db, integration_id, workspace_id)
        db.delete(integration)
        db.commit()
    
    async def test_integration(
        self, 
        db: Session, 
        integration_id: int, 
        workspace_id: int
    ) -> Dict[str, Any]:
        """Test integration connection"""
        integration = await self.get_integration(db, integration_id, workspace_id)
        
        try:
            if integration.type == "email":
                success = await self._test_email_integration(integration)
            elif integration.type == "sms":
                success = await self._test_sms_integration(integration)
            elif integration.type == "calendar":
                success = await self._test_calendar_integration(integration)
            else:
                raise ValidationException(f"Testing not implemented for {integration.type}")
            
            # Update test status
            integration.test_status = "success" if success else "failed"
            integration.last_tested_at = datetime.utcnow()
            db.commit()
            
            return {
                "success": success,
                "message": "Integration test successful" if success else "Integration test failed",
                "tested_at": integration.last_tested_at
            }
            
        except Exception as e:
            integration.test_status = "failed"
            integration.last_tested_at = datetime.utcnow()
            db.commit()
            
            return {
                "success": False,
                "message": f"Integration test failed: {str(e)}",
                "tested_at": integration.last_tested_at
            }
    
    async def get_email_integration(self, db: Session, workspace_id: int) -> Integration:
        """Get active email integration for workspace"""
        integration = db.query(Integration).filter(
            Integration.workspace_id == workspace_id,
            Integration.type == "email",
            Integration.is_active == True
        ).first()
        
        if not integration:
            raise NotFoundException("No active email integration found")
        
        return integration
    
    async def get_sms_integration(self, db: Session, workspace_id: int) -> Integration:
        """Get active SMS integration for workspace"""
        integration = db.query(Integration).filter(
            Integration.workspace_id == workspace_id,
            Integration.type == "sms",
            Integration.is_active == True
        ).first()
        
        if not integration:
            raise NotFoundException("No active SMS integration found")
        
        return integration
    
    async def _test_email_integration(self, integration: Integration) -> bool:
        """Test email integration"""
        try:
            if integration.provider == "sendgrid":
                # TODO: Test SendGrid connection
                api_key = integration.credentials.get("api_key")
                from_email = integration.credentials.get("from_email")
                
                if not api_key or not from_email:
                    return False
                
                # Simulate successful test for now
                return True
            
            elif integration.provider == "mailgun":
                # TODO: Test Mailgun connection
                return True
            
            return False
            
        except Exception:
            return False
    
    async def _test_sms_integration(self, integration: Integration) -> bool:
        """Test SMS integration"""
        try:
            if integration.provider == "twilio":
                # TODO: Test Twilio connection
                account_sid = integration.credentials.get("account_sid")
                auth_token = integration.credentials.get("auth_token")
                phone_number = integration.credentials.get("phone_number")
                
                if not all([account_sid, auth_token, phone_number]):
                    return False
                
                # Simulate successful test for now
                return True
            
            return False
            
        except Exception:
            return False
    
    async def _test_calendar_integration(self, integration: Integration) -> bool:
        """Test calendar integration"""
        try:
            if integration.provider == "google":
                # TODO: Test Google Calendar connection
                return True
            
            return False
            
        except Exception:
            return False