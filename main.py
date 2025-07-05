"""
Main entry point for Garlic and Chives application.

This module provides the entry point for running the application.
"""
import uvicorn
from app.api.main import app
from app.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.api.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
        access_log=True
    ) 