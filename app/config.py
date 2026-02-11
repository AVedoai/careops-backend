from pydantic_settings import BaseSettings
from typing import List
from functools import lru_cache

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    
    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    # Redis
    REDIS_URL: str
    
    # SendGrid
    SENDGRID_API_KEY: str
    SENDGRID_FROM_EMAIL: str
    SENDGRID_FROM_NAME: str = "CareOps"
    
    # Twilio
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_PHONE_NUMBER: str
    
    # Google Calendar
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    
    # Supabase
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_KEY: str = ""
    FILE_STORAGE_BUCKET: str = "forms"
    
    # CORS
    CORS_ORIGINS: str
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # URLs
    FRONTEND_URL: str
    BACKEND_URL: str
    
    # File Storage
    FILE_STORAGE_URL: str = ""
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    @property
    def cors_origins_list(self) -> List[str]:
        if self.ENVIRONMENT == "production":
            # In production, parse JSON string properly
            import json
            try:
                return json.loads(self.CORS_ORIGINS.replace("'", '"'))
            except:
                # Fallback to comma-separated parsing
                return [origin.strip() for origin in self.CORS_ORIGINS.split(',')]
        else:
            # Development: comma-separated or JSON
            if self.CORS_ORIGINS.startswith('['):
                import json
                return json.loads(self.CORS_ORIGINS.replace("'", '"'))
            return [origin.strip() for origin in self.CORS_ORIGINS.split(',')]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()