from app.integrations.base import BaseEmailIntegration
from typing import Dict, Any, Optional


class EmailIntegration(BaseEmailIntegration):
    """Base email integration with common functionality"""
    
    def __init__(self, credentials: Dict[str, Any]):
        super().__init__(credentials)
        self.from_email = credentials.get("from_email")
        
        if not self.from_email:
            raise ValueError("from_email is required in credentials")
    
    def _validate_email(self, email: str) -> bool:
        """Simple email validation"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _prepare_content(self, html_content: str, text_content: Optional[str] = None):
        """Prepare email content"""
        if text_content is None:
            # Simple HTML to text conversion
            import re
            text_content = re.sub('<[^<]+?>', '', html_content)
            text_content = re.sub(r'\s+', ' ', text_content).strip()
        
        return html_content, text_content