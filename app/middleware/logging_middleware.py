"""
Logging middleware for request/response tracking.
"""
import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.utils.logging import processing_logger


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log details."""
        start_time = time.time()
        
        # Log request
        processing_logger.log_system_event(
            "HTTP Request",
            {
                "method": request.method,
                "url": str(request.url),
                "client_ip": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", "unknown")
            },
            level="info"
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log response
            processing_logger.log_system_event(
                "HTTP Response",
                {
                    "method": request.method,
                    "url": str(request.url),
                    "status_code": response.status_code,
                    "process_time": process_time
                },
                level="info"
            )
            
            # Add processing time header
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            # Log error
            process_time = time.time() - start_time
            processing_logger.log_system_event(
                "HTTP Error",
                {
                    "method": request.method,
                    "url": str(request.url),
                    "error": str(e),
                    "process_time": process_time
                },
                level="error"
            )
            raise 