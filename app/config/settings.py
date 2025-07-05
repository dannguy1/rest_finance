"""
Configuration management for Garlic and Chives.
"""
from pydantic_settings import BaseSettings
from typing import Optional, List
import os
from pathlib import Path


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application settings
    app_name: str = "Garlic and Chives"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Database settings
    database_url: str = "sqlite:///app.db"
    
    # File processing settings
    max_file_size_mb: int = 50
    allowed_file_types: List[str] = [".csv"]
    processing_timeout_seconds: int = 300
    
    # Storage settings
    data_directory: str = "data"
    backup_directory: str = "backups"
    
    # Security settings
    secret_key: str = "your-secret-key-here-change-in-production"
    cors_origins: List[str] = ["*"]
    
    # Logging settings
    log_level: str = "INFO"
    log_file: Optional[str] = "logs/processing.log"
    
    # Rate limiting settings
    rate_limit_upload: str = "10/minute"
    rate_limit_process: str = "5/minute"
    rate_limit_download: str = "30/minute"
    rate_limit_api: str = "100/minute"
    
    # Cache settings
    cache_ttl_seconds: int = 300
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    @property
    def data_path(self) -> Path:
        """Get the data directory path."""
        return Path(self.data_directory)
    
    @property
    def backup_path(self) -> Path:
        """Get the backup directory path."""
        return Path(self.backup_directory)
    
    @property
    def log_path(self) -> Optional[Path]:
        """Get the log file path."""
        if self.log_file:
            return Path(self.log_file)
        return None
    
    @property
    def data_dir(self) -> str:
        return self.data_directory


# Global settings instance
settings = Settings() 