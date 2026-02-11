from app.integrations.sms.base import SMSIntegration
from typing import Dict, Any
import asyncio
import aiohttp
import json
from base64 import b64encode


class TwilioIntegration(SMSIntegration):
    """Twilio SMS integration"""
    
    def __init__(self, credentials: Dict[str, Any]):
        super().__init__(credentials)
        self.account_sid = credentials.get("account_sid")
        self.auth_token = credentials.get("auth_token")
        
        if not self.account_sid or not self.auth_token:
            raise ValueError("account_sid and auth_token are required for Twilio")
        
        self.base_url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}"
    
    def _get_auth_header(self) -> str:
        """Get Basic Auth header for Twilio API"""
        credentials = f"{self.account_sid}:{self.auth_token}"
        encoded_credentials = b64encode(credentials.encode()).decode()
        return f"Basic {encoded_credentials}"
    
    async def test_connection(self) -> bool:
        """Test Twilio API connection"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": self._get_auth_header()
                }
                
                async with session.get(
                    f"{self.base_url}.json",
                    headers=headers
                ) as response:
                    return response.status == 200
        except Exception:
            return False
    
    async def get_status(self) -> Dict[str, Any]:
        """Get Twilio account status"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": self._get_auth_header()
                }
                
                async with session.get(
                    f"{self.base_url}.json",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "status": "connected",
                            "account_sid": data.get("sid"),
                            "account_status": data.get("status"),
                            "phone_number": self.phone_number
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
    
    async def send_sms(
        self,
        to_phone: str,
        message: str
    ) -> Dict[str, Any]:
        """Send SMS via Twilio"""
        if not self._validate_phone(to_phone):
            return {
                "success": False,
                "error": "Invalid phone number format"
            }
        
        normalized_to = self._normalize_phone(to_phone)
        normalized_from = self._normalize_phone(self.phone_number)
        
        # Ensure message is not too long (SMS limit is 1600 chars for concatenated)
        if len(message) > 1600:
            message = message[:1597] + "..."
        
        payload = {
            "From": normalized_from,
            "To": normalized_to,
            "Body": message
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": self._get_auth_header(),
                    "Content-Type": "application/x-www-form-urlencoded"
                }
                
                # Convert dict to form data
                form_data = aiohttp.FormData()
                for key, value in payload.items():
                    form_data.add_field(key, value)
                
                async with session.post(
                    f"{self.base_url}/Messages.json",
                    headers=headers,
                    data=form_data
                ) as response:
                    
                    if response.status in [200, 201]:
                        data = await response.json()
                        return {
                            "success": True,
                            "message_sid": data.get("sid"),
                            "status": data.get("status", "sent"),
                            "to": normalized_to,
                            "from": normalized_from
                        }
                    else:
                        error_text = await response.text()
                        try:
                            error_data = json.loads(error_text)
                            error_message = error_data.get("message", error_text)
                        except:
                            error_message = error_text
                        
                        return {
                            "success": False,
                            "error": f"Twilio API error: {response.status} - {error_message}"
                        }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to send SMS: {str(e)}"
            }
    
    async def get_message_status(self, message_sid: str) -> Dict[str, Any]:
        """Get status of a sent message"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": self._get_auth_header()
                }
                
                async with session.get(
                    f"{self.base_url}/Messages/{message_sid}.json",
                    headers=headers
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "success": True,
                            "status": data.get("status"),
                            "error_code": data.get("error_code"),
                            "error_message": data.get("error_message")
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"Failed to get message status: {response.status}"
                        }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get message status: {str(e)}"
            }