from datetime import datetime, date, time
from typing import Optional

def format_datetime(dt: Optional[datetime]) -> Optional[str]:
    """Format datetime to ISO string"""
    return dt.isoformat() if dt else None

def format_date(d: Optional[date]) -> Optional[str]:
    """Format date to ISO string"""
    return d.isoformat() if d else None

def format_time(t: Optional[time]) -> Optional[str]:
    """Format time to string"""
    return t.strftime("%H:%M") if t else None