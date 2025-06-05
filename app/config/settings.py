from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os

class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "IntelliSales Colombia"
    VERSION: str = "0.1.0"
    DEBUG: bool = False
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database
    DATABASE_URL: str
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # External APIs
    GOOGLE_ADS_DEVELOPER_TOKEN: Optional[str] = None
    GOOGLE_ADS_CLIENT_ID: Optional[str] = None
    GOOGLE_ADS_CLIENT_SECRET: Optional[str] = None
    
    PIPEDRIVE_API_TOKEN: Optional[str] = None
    ZOHO_CLIENT_ID: Optional[str] = None
    ZOHO_CLIENT_SECRET: Optional[str] = None
    
    # Email Settings (para notificaciones)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    
    # File Upload
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    UPLOAD_FOLDER: str = "uploads"
    
    # AI/ML Settings
    MODEL_STORAGE_PATH: str = "models"
    TRAINING_DATA_RETENTION_DAYS: int = 90
    
    # Configuración para Pydantic v2
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,  # Cambiado a False para mayor flexibilidad
        extra="ignore",
        validate_default=True
    )

# Crear la instancia de configuración
try:
    settings = Settings()
    print(f"✓ Settings loaded successfully for {settings.APP_NAME}")
except Exception as e:
    print(f"✗ Error loading settings: {e}")
    # Fallback settings for development
    print("Using fallback settings...")
    
    class FallbackSettings:
        APP_NAME = "IntelliSales Colombia"
        VERSION = "0.1.0"
        DEBUG = True
        SECRET_KEY = "fallback-secret-key-for-development-only"
        ALGORITHM = "HS256"
        ACCESS_TOKEN_EXPIRE_MINUTES = 30
        DATABASE_URL = "sqlite:///./intellisales.db"
        REDIS_URL = "redis://localhost:6379"
        GOOGLE_ADS_DEVELOPER_TOKEN = None
        GOOGLE_ADS_CLIENT_ID = None
        GOOGLE_ADS_CLIENT_SECRET = None
        PIPEDRIVE_API_TOKEN = None
        ZOHO_CLIENT_ID = None
        ZOHO_CLIENT_SECRET = None
        SMTP_HOST = None
        SMTP_PORT = 587
        SMTP_USER = None
        SMTP_PASSWORD = None
        MAX_FILE_SIZE = 50 * 1024 * 1024
        UPLOAD_FOLDER = "uploads"
        MODEL_STORAGE_PATH = "models"
        TRAINING_DATA_RETENTION_DAYS = 90
    
    settings = FallbackSettings()