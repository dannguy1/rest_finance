"""
Health check and monitoring routes.
"""
import psutil
import os
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings
from app.utils.logging import processing_logger
from app.models.file_models import HealthCheck, DetailedHealthCheck

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.get("/", response_model=HealthCheck)
@limiter.limit(settings.rate_limit_api)
async def health_check(request: Request):
    """Basic health check endpoint."""
    return HealthCheck(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="1.0.0"
    )


@router.get("/detailed", response_model=DetailedHealthCheck)
@limiter.limit(settings.rate_limit_api)
async def detailed_health_check(request: Request):
    """Detailed health check with system metrics."""
    try:
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        system_metrics = {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available_gb": round(memory.available / (1024**3), 2),
            "disk_percent": disk.percent,
            "disk_free_gb": round(disk.free / (1024**3), 2)
        }
        
        # Database status (SQLite file check)
        db_status = "healthy"
        try:
            db_path = Path("app.db")
            if db_path.exists():
                db_size = db_path.stat().st_size
                db_status = f"healthy (size: {db_size} bytes)"
            else:
                db_status = "not_initialized"
        except Exception as e:
            db_status = f"error: {str(e)}"
        
        database_status = {
            "status": db_status,
            "type": "sqlite"
        }
        
        # Service status
        services_status = {
            "file_service": "healthy",
            "processing_service": "healthy",
            "validation_service": "healthy"
        }
        
        # Overall status
        overall_status = "healthy"
        if cpu_percent > 90 or memory.percent > 90 or disk.percent > 90:
            overall_status = "warning"
        
        return DetailedHealthCheck(
            status=overall_status,
            timestamp=datetime.now().isoformat(),
            system=system_metrics,
            database=database_status,
            services=services_status
        )
        
    except Exception as e:
        processing_logger.log_system_event(
            f"Health check error: {str(e)}", level="error"
        )
        return DetailedHealthCheck(
            status="error",
            timestamp=datetime.now().isoformat(),
            system={"error": str(e)},
            database={"status": "error"},
            services={"error": str(e)}
        )


@router.get("/ready")
@limiter.limit(settings.rate_limit_api)
async def readiness_check(request: Request):
    """Readiness check for Kubernetes/container orchestration."""
    try:
        # Check if data directories exist and are writable
        from app.utils.file_utils import FileUtils
        
        data_path = settings.data_path
        if not data_path.exists():
            return {"status": "not_ready", "message": "Data directory does not exist"}
        
        # Check if we can write to the data directory
        test_file = data_path / "health_check_test"
        try:
            test_file.write_text("test")
            test_file.unlink()
        except Exception as e:
            return {"status": "not_ready", "message": f"Cannot write to data directory: {str(e)}"}
        
        return {"status": "ready", "message": "Application is ready to serve requests"}
        
    except Exception as e:
        processing_logger.log_system_event(
            f"Readiness check error: {str(e)}", level="error"
        )
        return {"status": "not_ready", "message": f"Readiness check failed: {str(e)}"}


@router.get("/live")
@limiter.limit(settings.rate_limit_api)
async def liveness_check(request: Request):
    """Liveness check for Kubernetes/container orchestration."""
    return {"status": "alive", "timestamp": datetime.now().isoformat()}


@router.get("/metrics")
@limiter.limit(settings.rate_limit_api)
async def metrics(request: Request):
    """Application metrics endpoint."""
    try:
        # Process metrics
        process = psutil.Process()
        
        metrics_data = {
            "process": {
                "cpu_percent": process.cpu_percent(),
                "memory_percent": process.memory_percent(),
                "memory_rss_mb": round(process.memory_info().rss / (1024**2), 2),
                "num_threads": process.num_threads(),
                "open_files": len(process.open_files()),
                "connections": len(process.connections())
            },
            "system": {
                "cpu_count": psutil.cpu_count(),
                "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
                "disk_total_gb": round(psutil.disk_usage('/').total / (1024**3), 2)
            },
            "application": {
                "version": "1.0.0",
                "uptime_seconds": (datetime.now() - datetime.fromtimestamp(process.create_time())).total_seconds()
            }
        }
        
        return metrics_data
        
    except Exception as e:
        processing_logger.log_system_event(
            f"Metrics error: {str(e)}", level="error"
        )
        return {"error": str(e)} 