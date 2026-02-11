from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseIntegration(ABC):
    """Base class for all integrations"""
    
    def __init__(self, credentials: Dict[str, Any]):
        self.credentials = credentials
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """Test if the integration is properly configured and accessible"""
        pass
    
    @abstractmethod
    async def get_status(self) -> Dict[str, Any]:
        """Get current status of the integration"""
        pass


class BaseEmailIntegration(BaseIntegration):
    """Base class for email integrations"""
    
    @abstractmethod
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send an email"""
        pass
    
    @abstractmethod
    async def send_template_email(
        self,
        to_email: str,
        template_id: str,
        template_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send an email using a template"""
        pass


class BaseSMSIntegration(BaseIntegration):
    """Base class for SMS integrations"""
    
    @abstractmethod
    async def send_sms(
        self,
        to_phone: str,
        message: str
    ) -> Dict[str, Any]:
        """Send an SMS message"""
        pass


class BaseCalendarIntegration(BaseIntegration):
    """Base class for calendar integrations"""
    
    @abstractmethod
    async def create_event(
        self,
        title: str,
        start_time: str,
        end_time: str,
        description: Optional[str] = None,
        attendees: Optional[list] = None
    ) -> Dict[str, Any]:
        """Create a calendar event"""
        pass
    
    @abstractmethod
    async def update_event(
        self,
        event_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Update a calendar event"""
        pass
    
    @abstractmethod
    async def delete_event(self, event_id: str) -> Dict[str, Any]:
        """Delete a calendar event"""
        pass