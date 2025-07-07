# Settings configuration for Financial Data Processor
# Based on config/settings_sample.py

import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Data directory for storing processed files
DATA_DIR = os.getenv("DATA_DIR", "data")

# API settings
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
API_DEBUG = os.getenv("API_DEBUG", "False").lower() == "true"

# Logging settings
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# File processing settings
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
ALLOWED_EXTENSIONS = [".csv", ".xlsx", ".xls", ".pdf"]

# Security settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

# Database settings (if using database)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

# External API settings
EXTERNAL_API_KEY = os.getenv("EXTERNAL_API_KEY", "")
EXTERNAL_API_URL = os.getenv("EXTERNAL_API_URL", "")

# Processing settings
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "1000"))
PROCESSING_TIMEOUT = int(os.getenv("PROCESSING_TIMEOUT", "300"))

# Source configuration directory
CONFIG_DIR = BASE_DIR / "config"

# Source metadata directory (under data directory)
SOURCE_METADATA_DIR = "source_metadata" 