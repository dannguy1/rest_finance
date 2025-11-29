"""
Middleware for adding correlation IDs to requests.
"""
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.utils.logging_enhanced import set_correlation_id, clear_correlation_id, api_logger
import time


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Middleware to add correlation ID to each request."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with correlation ID."""
        # Get or create correlation ID
        corr_id = request.headers.get("X-Correlation-ID")
        if not corr_id:
            corr_id = set_correlation_id()
        else:
            set_correlation_id(corr_id)
        
        # Start timing
        start_time = time.time()
        
        try:
            # Process request
            response = await call_next(request)
            
            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = corr_id
            
            # Log request
            duration_ms = (time.time() - start_time) * 1000
            api_logger.log_http_request(
                method=request.method,
                path=str(request.url.path),
                status_code=response.status_code,
                duration_ms=round(duration_ms, 2),
                user_agent=request.headers.get("User-Agent")
            )
            
            return response
            
        except Exception as e:
            # Log error
            duration_ms = (time.time() - start_time) * 1000
            api_logger.log_error(e, {
                "method": request.method,
                "path": str(request.url.path),
                "duration_ms": round(duration_ms, 2)
            })
            raise
        finally:
            # Clear correlation ID from context
            clear_correlation_id()
