from app.integrations.email.base import EmailIntegration
from typing import Dict, Any, Optional
import asyncio
import aiohttp
import json
from app.config import settings


class SendGridIntegration(EmailIntegration):
    """SendGrid email integration"""
    
    def __init__(self, credentials: Dict[str, Any]):
        super().__init__(credentials)
        self.api_key = credentials.get("api_key")
        
        if not self.api_key:
            raise ValueError("api_key is required for SendGrid")
        
        self.base_url = "https://api.sendgrid.com/v3"
    
    async def test_connection(self) -> bool:
        """Test SendGrid API connection"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                async with session.get(
                    f"{self.base_url}/user/profile",
                    headers=headers
                ) as response:
                    return response.status == 200
        except Exception:
            return False
    
    async def get_status(self) -> Dict[str, Any]:
        """Get SendGrid account status"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                async with session.get(
                    f"{self.base_url}/user/profile",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "status": "connected",
                            "account": data.get("username", "Unknown"),
                            "email": data.get("email", "Unknown")
                        }
                    else:
                        return {
                            "status": "error",
                            "message": f"API returned status {response.status}"
                        }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send email via SendGrid"""
        if not self._validate_email(to_email):
            return {
                "success": False,
                "error": "Invalid email address"
            }
        
        html_content, text_content = self._prepare_content(html_content, text_content)
        
        payload = {
            "personalizations": [{
                "to": [{"email": to_email}],
                "subject": subject
            }],
            "from": {"email": self.from_email},
            "content": [
                {"type": "text/plain", "value": text_content},
                {"type": "text/html", "value": html_content}
            ]
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                async with session.post(
                    f"{self.base_url}/mail/send",
                    headers=headers,
                    data=json.dumps(payload)
                ) as response:
                    
                    if response.status == 202:
                        message_id = response.headers.get("X-Message-Id", "unknown")
                        return {
                            "success": True,
                            "message_id": message_id,
                            "status": "sent"
                        }
                    else:
                        error_text = await response.text()
                        return {
                            "success": False,
                            "error": f"SendGrid API error: {response.status} - {error_text}"
                        }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to send email: {str(e)}"
            }
    
    async def send_template_email(
        self,
        to_email: str,
        template_id: str,
        template_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send email using SendGrid template"""
        if not self._validate_email(to_email):
            return {
                "success": False,
                "error": "Invalid email address"
            }
        
        payload = {
            "personalizations": [{
                "to": [{"email": to_email}],
                "dynamic_template_data": template_data
            }],
            "from": {"email": self.from_email},
            "template_id": template_id
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                async with session.post(
                    f"{self.base_url}/mail/send",
                    headers=headers,
                    data=json.dumps(payload)
                ) as response:
                    
                    if response.status == 202:
                        message_id = response.headers.get("X-Message-Id", "unknown")
                        return {
                            "success": True,
                            "message_id": message_id,
                            "status": "sent"
                        }
                    else:
                        error_text = await response.text()
                        return {
                            "success": False,
                            "error": f"SendGrid API error: {response.status} - {error_text}"
                        }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to send template email: {str(e)}"
            }