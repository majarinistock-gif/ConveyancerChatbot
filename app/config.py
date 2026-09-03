"""
Configuration management for WhatsApp Conveyancing Bot
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application Settings
    ENVIRONMENT: str = "sandbox"
    PORT: int = 8000
    DEBUG: bool = True
    
    # MongoDB Configuration
    MONGO_URI: str
    MONGO_DATABASE: str = "conveyancing_bot"
    
    # Meta WhatsApp Configuration (Sandbox Mode)
    META_ACCESS_TOKEN: str
    META_PHONE_NUMBER_ID: str
    WHATSAPP_VERIFY_TOKEN: str
    
    # Meta Configuration (Production Mode)
    META_WABA_ID: Optional[str] = None
    META_BUSINESS_ID: Optional[str] = None
    
    # OCR.space Configuration
    OCR_SPACE_API_KEY: str
    OCR_SPACE_ENGINE: int = 3
    
    # Paynow Payment Configuration
    PAYNOW_INTEGRATION_ID: str
    PAYNOW_INTEGRATION_KEY: str
    PAYNOW_RESULT_URL: str
    
    # Application Settings
    ADMIN_FEE_AMOUNT: float = 5.00
    ADMIN_FEE_CURRENCY: str = "USD"
    SESSION_EXPIRY_HOURS: int = 48
    
    # File Upload Settings
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_IMAGE_FORMATS: str = "jpg,jpeg,png"
    ALLOWED_DOCUMENT_FORMATS: str = "pdf"
    
    # Pagination Settings
    CONVEYANCERS_PER_PAGE: int = 5
    
    # Webhook Configuration
    WEBHOOK_URL: str
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    @property
    def allowed_image_formats_list(self) -> list:
        """Convert comma-separated image formats to list"""
        return [fmt.strip().lower() for fmt in self.ALLOWED_IMAGE_FORMATS.split(",")]
    
    @property
    def allowed_document_formats_list(self) -> list:
        """Convert comma-separated document formats to list"""
        return [fmt.strip().lower() for fmt in self.ALLOWED_DOCUMENT_FORMATS.split(",")]
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.ENVIRONMENT.lower() == "production"
    
    @property
    def is_sandbox(self) -> bool:
        """Check if running in sandbox mode"""
        return self.ENVIRONMENT.lower() == "sandbox"


# Global settings instance
settings = Settings()