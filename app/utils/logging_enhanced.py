"""
Enhanced logging utilities with JSON formatting and correlation IDs.
"""
import logging
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
from contextvars import ContextVar
from app.config import settings

# Context variable for correlation ID
correlation_id: ContextVar[str] = ContextVar('correlation_id', default='')


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": correlation_id.get() or "N/A",
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)
        
        # Add standard fields
        log_data["module"] = record.module
        log_data["function"] = record.funcName
        log_data["line"] = record.lineno
        
        return json.dumps(log_data)


class CorrelationIdFilter(logging.Filter):
    """Filter to add correlation ID to log records."""
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add correlation ID to record."""
        record.correlation_id = correlation_id.get() or "N/A"
        return True


def set_correlation_id(corr_id: Optional[str] = None) -> str:
    """Set correlation ID for current context."""
    if corr_id is None:
        corr_id = str(uuid.uuid4())
    correlation_id.set(corr_id)
    return corr_id


def get_correlation_id() -> str:
    """Get current correlation ID."""
    return correlation_id.get() or "N/A"


def clear_correlation_id():
    """Clear correlation ID from context."""
    correlation_id.set('')


class StructuredLogger:
    """Enhanced structured logger with JSON formatting and correlation IDs."""
    
    def __init__(self, name: str, log_file: Optional[str] = None, use_json: bool = True):
        """Initialize logger with name and optional log file."""
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        self.use_json = use_json
        
        # Prevent duplicate handlers
        if self.logger.handlers:
            return
        
        # Add correlation ID filter
        corr_filter = CorrelationIdFilter()
        self.logger.addFilter(corr_filter)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        if use_json:
            console_handler.setFormatter(JSONFormatter())
        else:
            console_formatter = logging.Formatter(
                '%(asctime)s - [%(correlation_id)s] - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
        
        self.logger.addHandler(console_handler)
        
        # File handler (if specified)
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            
            if use_json:
                file_handler.setFormatter(JSONFormatter())
            else:
                file_formatter = logging.Formatter(
                    '%(asctime)s - [%(correlation_id)s] - %(name)s - %(levelname)s - %(message)s'
                )
                file_handler.setFormatter(file_formatter)
            
            self.logger.addHandler(file_handler)
    
    def _log(self, level: str, message: str, extra_fields: Optional[Dict[str, Any]] = None):
        """Internal log method with extra fields support."""
        extra = {"extra_fields": extra_fields or {}}
        
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        log_method(message, extra=extra)
    
    def log_processing_event(self, event_type: str, source: str, message: str, 
                           metadata: Optional[Dict[str, Any]] = None, level: str = "info"):
        """Log structured processing events."""
        extra_fields = {
            "event_type": event_type,
            "source": source,
            "metadata": metadata or {}
        }
        
        self._log(level, message, extra_fields)
    
    def log_file_operation(self, operation: str, filename: str, source: str, 
                          success: bool, error: Optional[str] = None):
        """Log file operations."""
        extra_fields = {
            "event_type": "file_operation",
            "operation": operation,
            "filename": filename,
            "source": source,
            "success": success
        }
        
        if error:
            extra_fields["error"] = error
            level = "error"
            message = f"File {operation} failed: {filename} - {error}"
        else:
            level = "info"
            message = f"File {operation} successful: {filename}"
        
        self._log(level, message, extra_fields)
    
    def log_processing_job(self, job_id: str, source: str, status: str, 
                          progress: float, message: str):
        """Log processing job updates."""
        extra_fields = {
            "event_type": "processing_job",
            "job_id": job_id,
            "source": source,
            "status": status,
            "progress": progress
        }
        
        self._log("info", message, extra_fields)
    
    def log_validation_event(self, source: str, filename: str, valid: bool, 
                           errors: Optional[list] = None, warnings: Optional[list] = None):
        """Log validation events."""
        extra_fields = {
            "event_type": "validation",
            "source": source,
            "filename": filename,
            "valid": valid,
            "errors": errors or [],
            "warnings": warnings or []
        }
        
        level = "error" if not valid else "warning" if warnings else "info"
        message = f"Validation {'passed' if valid else 'failed'} for {filename}"
        
        self._log(level, message, extra_fields)
    
    def log_system_event(self, message: str, level: str = "info", 
                        details: Optional[Dict[str, Any]] = None):
        """Log system-level events."""
        extra_fields = {
            "event_type": "system",
            "details": details or {}
        }
        
        self._log(level, message, extra_fields)
    
    def log_error(self, error: Exception, context: Optional[Dict[str, Any]] = None):
        """Log error with exception details."""
        extra_fields = {
            "event_type": "error",
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {}
        }
        
        self._log("error", f"Error occurred: {str(error)}", extra_fields)
    
    def log_http_request(self, method: str, path: str, status_code: int, 
                        duration_ms: float, user_agent: Optional[str] = None):
        """Log HTTP request details."""
        extra_fields = {
            "event_type": "http_request",
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": duration_ms,
            "user_agent": user_agent
        }
        
        level = "warning" if status_code >= 400 else "info"
        message = f"{method} {path} - {status_code} ({duration_ms}ms)"
        
        self._log(level, message, extra_fields)


# Initialize loggers
processing_logger = StructuredLogger(
    "processing",
    log_file=str(settings.log_path / "processing.log"),
    use_json=True
)

system_logger = StructuredLogger(
    "system",
    log_file=str(settings.log_path / "system.log"),
    use_json=True
)

api_logger = StructuredLogger(
    "api",
    log_file=str(settings.log_path / "api.log"),
    use_json=True
)
