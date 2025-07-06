"""
Error handling middleware for consistent error responses.
"""
import traceback
from typing import Callable
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from app.utils.logging import processing_logger


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for handling errors and providing consistent error responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and handle errors."""
        try:
            return await call_next(request)
            
        except HTTPException as e:
            # Handle HTTP exceptions
            processing_logger.log_system_event(
                "HTTP Exception",
                {
                    "method": request.method,
                    "url": str(request.url),
                    "status_code": e.status_code,
                    "detail": e.detail
                },
                level="warning"
            )
            
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "error": "HTTP Error",
                    "message": e.detail,
                    "status_code": e.status_code
                }
            )
            
        except Exception as e:
            # Handle unexpected exceptions
            processing_logger.log_system_event(
                "Unexpected Error",
                {
                    "method": request.method,
                    "url": str(request.url),
                    "error": str(e),
                    "traceback": traceback.format_exc()
                },
                level="error"
            )
            
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal Server Error",
                    "message": "An unexpected error occurred",
                    "status_code": 500
                }
            ) 