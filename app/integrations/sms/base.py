from app.integrations.base import BaseSMSIntegration
from typing import Dict, Any
import re


class SMSIntegration(BaseSMSIntegration):
    """Base SMS integration with common functionality"""
    
    def __init__(self, credentials: Dict[str, Any]):
        super().__init__(credentials)
        self.phone_number = credentials.get("phone_number")
        
        if not self.phone_number:
            raise ValueError("phone_number is required in credentials")
    
    def _validate_phone(self, phone: str) -> bool:
        """Simple phone validation"""
        # Remove all non-digit characters except +
        clean_phone = re.sub(r'[^+\d]', '', phone)
        
        # Check if it starts with + and has 10-15 digits
        if re.match(r'^\+\d{10,15}$', clean_phone):
            return True
        
        # Check if it's a 10-digit US number
        if re.match(r'^\d{10}$', clean_phone):
            return True
        
        return False
    
    def _normalize_phone(self, phone: str) -> str:
        """Normalize phone number format"""
        # Remove all non-digit characters except +
        clean_phone = re.sub(r'[^+\d]', '', phone)
        
        # If it's 10 digits, assume US number and add +1
        if re.match(r'^\d{10}$', clean_phone):
            clean_phone = f"+1{clean_phone}"
        
        # If it doesn't start with +, add it
        if not clean_phone.startswith('+'):
            clean_phone = f"+{clean_phone}"
        
        return clean_phone