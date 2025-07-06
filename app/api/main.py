"""
Main FastAPI application for Garlic and Chives.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import time
from pathlib import Path
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.utils.logging import processing_logger
from app.api.routes import file_routes, processing_routes, health_routes, web_routes, mapping_routes, analytics_routes
from app.api import sample_data
from app.middleware.logging_middleware import LoggingMiddleware
from app.middleware.error_middleware import ErrorHandlingMiddleware


# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    processing_logger.log_system_event("Application starting up", level="info")
    yield
    # Shutdown
    processing_logger.log_system_event("Application shutting down", level="info")


# Create FastAPI app
app = FastAPI(
    title="Garlic and Chives",
    description="Full-Stack Garlic and Chives for multi-source data processing",
    version="1.0.0",
    docs_url="/api/docs" if settings.debug else None,
    redoc_url="/api/redoc" if settings.debug else None,
    lifespan=lifespan
)

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
app.add_middleware(LoggingMiddleware)
app.add_middleware(ErrorHandlingMiddleware)

# Mount static files
static_path = Path(__file__).parent.parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Setup templates
from app.api.templates_config import templates

# Include routers
app.include_router(health_routes.router, prefix="/api/health", tags=["Health"])
app.include_router(analytics_routes.router, prefix="/api/files/analytics", tags=["Analytics"])
app.include_router(file_routes.router, prefix="/api/files", tags=["Files"])
app.include_router(processing_routes.router, prefix="/api/processing", tags=["Processing"])
app.include_router(mapping_routes.router, prefix="/api/mappings", tags=["Mapping"])
app.include_router(sample_data.router, prefix="/api/sample-data", tags=["Sample Data"])
app.include_router(web_routes.router, tags=["Web"])


@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    processing_logger.log_system_event("Application starting up")
    
    # Ensure data directories exist
    from app.utils.file_utils import FileUtils
    for source_dir in FileUtils.get_source_directories():
        FileUtils.ensure_directory(source_dir / "input")
        FileUtils.ensure_directory(source_dir / "output")
    
    # Ensure backup directory exists
    FileUtils.ensure_directory(settings.backup_path)
    
    processing_logger.log_system_event("Application startup completed")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    processing_logger.log_system_event("Application shutting down")


# Root endpoint is now handled by web_routes


@app.get("/api")
async def api_info():
    """API information endpoint."""
    return {
        "name": settings.app_name,
        "version": "1.0.0",
        "description": "Garlic and Chives API",
        "endpoints": {
            "health": "/api/health",
            "files": "/api/files",
            "processing": "/api/processing",
            "docs": "/api/docs" if settings.debug else None
        }
    }


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    processing_logger.log_system_event(
        f"Unhandled exception: {str(exc)}", 
        {"path": request.url.path, "method": request.method},
        level="error"
    )
    
    return {
        "error": "Internal server error",
        "message": str(exc) if settings.debug else "An unexpected error occurred",
        "status_code": 500
    } 