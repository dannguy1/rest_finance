"""
Enhanced logging utilities for Financial Data Processor.
"""
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
from app.config import settings


class StructuredLogger:
    """Structured logger with JSON formatting and file/console handlers."""
    
    def __init__(self, name: str, log_file: Optional[str] = None):
        """Initialize logger with name and optional log file."""
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Prevent duplicate handlers
        if self.logger.handlers:
            return
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler (if specified)
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
    
    def log_processing_event(self, event_type: str, source: str, message: str, 
                           metadata: Optional[Dict[str, Any]] = None, level: str = "info"):
        """Log structured processing events."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "source": source,
            "message": message,
            "metadata": metadata or {},
            "level": level
        }
        
        log_message = json.dumps(log_entry)
        
        if level == "debug":
            self.logger.debug(log_message)
        elif level == "info":
            self.logger.info(log_message)
        elif level == "warning":
            self.logger.warning(log_message)
        elif level == "error":
            self.logger.error(log_message)
        elif level == "critical":
            self.logger.critical(log_message)
    
    def log_file_operation(self, operation: str, filename: str, source: str, 
                          success: bool, error: Optional[str] = None):
        """Log file operations."""
        metadata = {
            "operation": operation,
            "filename": filename,
            "source": source,
            "success": success
        }
        
        if error:
            metadata["error"] = error
            level = "error"
        else:
            level = "info"
        
        self.log_processing_event(
            "file_operation",
            source,
            f"File {operation}: {filename}",
            metadata,
            level
        )
    
    def log_processing_job(self, job_id: str, source: str, status: str, 
                          progress: float, message: str):
        """Log processing job updates."""
        metadata = {
            "job_id": job_id,
            "status": status,
            "progress": progress
        }
        
        level = "error" if status == "error" else "info"
        
        self.log_processing_event(
            "processing_job",
            source,
            message,
            metadata,
            level
        )
    
    def log_system_event(self, event: str, details: Optional[Dict[str, Any]] = None, 
                        level: str = "info"):
        """Log system-level events."""
        self.log_processing_event(
            "system_event",
            "system",
            event,
            details,
            level
        )


# Initialize global logger
processing_logger = StructuredLogger("financial_processor", settings.log_file) 