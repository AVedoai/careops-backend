import re
from typing import Optional

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return bool(re.match(pattern, email))

def validate_phone(phone: str) -> bool:
    """Validate phone format (basic)"""
    pattern = r'^\+?1?\d{9,15}$'
    return bool(re.match(pattern, phone.replace(' ', '').replace('-', '')))

def create_slug(name: str) -> str:
    """Create URL-friendly slug"""
    slug = name.lower()
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    slug = slug.strip('-')
    return slug