"""
Configuration management for Financial Data Processor.
"""
from pydantic_settings import BaseSettings
from typing import Optional, List
import os
from pathlib import Path

# Import config settings
import sys
sys.path.append(str(Path(__file__).parent.parent.parent / "config"))
try:
    from settings import DATA_DIR, API_HOST, API_PORT, API_DEBUG, LOG_LEVEL, MAX_FILE_SIZE, ALLOWED_EXTENSIONS, SECRET_KEY, CORS_ORIGINS, CONFIG_DIR, SOURCE_METADATA_DIR
except ImportError:
    # Fallback defaults if config not available
    DATA_DIR = "data"
    API_HOST = "0.0.0.0"
    API_PORT = 8000
    API_DEBUG = False
    LOG_LEVEL = "INFO"
    MAX_FILE_SIZE = 10485760
    ALLOWED_EXTENSIONS = [".csv", ".xlsx", ".xls"]
    SECRET_KEY = "your-secret-key-here"
    CORS_ORIGINS = ["*"]
    CONFIG_DIR = Path(__file__).parent.parent.parent / "config"
    SOURCE_METADATA_DIR = "source_metadata"


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application settings
    app_name: str = "Financial Data Processor"
    debug: bool = API_DEBUG
    host: str = API_HOST
    port: int = API_PORT
    
    # Database settings
    database_url: str = "sqlite:///app.db"
    
    # File processing settings
    max_file_size_mb: int = MAX_FILE_SIZE // (1024 * 1024)  # Convert to MB
    allowed_file_types: List[str] = ALLOWED_EXTENSIONS
    processing_timeout_seconds: int = 300
    
    # Storage settings - using config directory settings
    data_directory: str = DATA_DIR
    backup_directory: str = "backups"
    source_metadata_directory: str = SOURCE_METADATA_DIR
    
    # Security settings
    secret_key: str = SECRET_KEY
    cors_origins: List[str] = CORS_ORIGINS
    
    # Logging settings
    log_level: str = LOG_LEVEL
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
    
    @property
    def source_metadata_path(self) -> Path:
        """Get the source metadata directory path."""
        return self.data_path / self.source_metadata_directory
    
    @property
    def config_path(self) -> Path:
        """Get the config directory path."""
        return CONFIG_DIR


# Global settings instance
settings = Settings() 