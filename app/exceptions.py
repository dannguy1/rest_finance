"""
Custom exceptions and error handling for Financial Data Processor.
Provides specific exception types for better error handling and debugging.
"""
from typing import Optional, Dict, Any
from fastapi import HTTPException, status


class FinanceProcessorError(Exception):
    """Base exception for all application errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class FileOperationError(FinanceProcessorError):
    """Raised when file operations fail."""
    pass


class FileValidationError(FinanceProcessorError):
    """Raised when file validation fails."""
    pass


class FileTooLargeError(FileValidationError):
    """Raised when uploaded file exceeds size limit."""
    pass


class InvalidFileTypeError(FileValidationError):
    """Raised when file type is not supported."""
    pass


class FileNotFoundError(FileOperationError):
    """Raised when a file cannot be found."""
    pass


class FileAlreadyExistsError(FileOperationError):
    """Raised when attempting to upload a file that already exists."""
    pass


class ProcessingError(FinanceProcessorError):
    """Raised when data processing fails."""
    pass


class CSVParsingError(ProcessingError):
    """Raised when CSV parsing fails."""
    pass


class DataValidationError(ProcessingError):
    """Raised when data validation fails."""
    pass


class MappingError(FinanceProcessorError):
    """Raised when mapping configuration errors occur."""
    pass


class InvalidMappingError(MappingError):
    """Raised when mapping configuration is invalid."""
    pass


class MappingNotFoundError(MappingError):
    """Raised when requested mapping is not found."""
    pass


class SourceError(FinanceProcessorError):
    """Raised when source-related errors occur."""
    pass


class InvalidSourceError(SourceError):
    """Raised when source ID is invalid."""
    pass


class SourceNotFoundError(SourceError):
    """Raised when source is not found."""
    pass


class ConfigurationError(FinanceProcessorError):
    """Raised when configuration errors occur."""
    pass


class MetadataError(FinanceProcessorError):
    """Raised when metadata operations fail."""
    pass


# HTTP Exception Factories
def create_http_exception(
    status_code: int,
    message: str,
    error_code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> HTTPException:
    """
    Create a standardized HTTPException.
    
    Args:
        status_code: HTTP status code
        message: User-friendly error message
        error_code: Machine-readable error code
        details: Additional error details
        
    Returns:
        HTTPException with standardized format
    """
    headers = {}
    if error_code:
        headers["X-Error-Code"] = error_code
    
    detail = {"message": message}
    if details:
        detail["details"] = details
        
    return HTTPException(
        status_code=status_code,
        detail=detail if details else message,
        headers=headers if headers else None
    )


def bad_request_error(message: str, details: Optional[Dict[str, Any]] = None) -> HTTPException:
    """Create a 400 Bad Request error."""
    return create_http_exception(
        status.HTTP_400_BAD_REQUEST,
        message,
        "BAD_REQUEST",
        details
    )


def not_found_error(message: str, details: Optional[Dict[str, Any]] = None) -> HTTPException:
    """Create a 404 Not Found error."""
    return create_http_exception(
        status.HTTP_404_NOT_FOUND,
        message,
        "NOT_FOUND",
        details
    )


def conflict_error(message: str, details: Optional[Dict[str, Any]] = None) -> HTTPException:
    """Create a 409 Conflict error."""
    return create_http_exception(
        status.HTTP_409_CONFLICT,
        message,
        "CONFLICT",
        details
    )


def internal_error(message: str = "An internal error occurred", details: Optional[Dict[str, Any]] = None) -> HTTPException:
    """Create a 500 Internal Server Error."""
    return create_http_exception(
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        message,
        "INTERNAL_ERROR",
        details
    )


def unprocessable_entity_error(message: str, details: Optional[Dict[str, Any]] = None) -> HTTPException:
    """Create a 422 Unprocessable Entity error."""
    return create_http_exception(
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        message,
        "UNPROCESSABLE_ENTITY",
        details
    )


# Error Handler Decorators
from functools import wraps
from typing import Callable
import logging

logger = logging.getLogger(__name__)


def handle_service_errors(func: Callable) -> Callable:
    """
    Decorator to handle service-level errors and convert to HTTP exceptions.
    
    Usage:
        @handle_service_errors
        async def my_route_handler():
            # ... route logic
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except FileValidationError as e:
            logger.warning(f"File validation error: {e.message}", extra=e.details)
            raise bad_request_error(e.message, e.details)
        except FileNotFoundError as e:
            logger.warning(f"File not found: {e.message}", extra=e.details)
            raise not_found_error(e.message, e.details)
        except FileAlreadyExistsError as e:
            logger.warning(f"File conflict: {e.message}", extra=e.details)
            raise conflict_error(e.message, e.details)
        except (ProcessingError, CSVParsingError, DataValidationError) as e:
            logger.error(f"Processing error: {e.message}", extra=e.details)
            raise unprocessable_entity_error(e.message, e.details)
        except (InvalidMappingError, MappingNotFoundError) as e:
            logger.warning(f"Mapping error: {e.message}", extra=e.details)
            raise bad_request_error(e.message, e.details)
        except InvalidSourceError as e:
            logger.warning(f"Invalid source: {e.message}", extra=e.details)
            raise bad_request_error(e.message, e.details)
        except FinanceProcessorError as e:
            logger.error(f"Application error: {e.message}", extra=e.details)
            raise internal_error(e.message, e.details)
        except Exception as e:
            logger.critical(f"Unexpected error: {str(e)}", exc_info=True)
            raise internal_error("An unexpected error occurred. Please try again.")
    
    return wrapper


def handle_sync_service_errors(func: Callable) -> Callable:
    """
    Decorator to handle service-level errors in synchronous functions.
    
    Usage:
        @handle_sync_service_errors
        def my_sync_handler():
            # ... logic
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FileValidationError as e:
            logger.warning(f"File validation error: {e.message}", extra=e.details)
            raise bad_request_error(e.message, e.details)
        except FileNotFoundError as e:
            logger.warning(f"File not found: {e.message}", extra=e.details)
            raise not_found_error(e.message, e.details)
        except FileAlreadyExistsError as e:
            logger.warning(f"File conflict: {e.message}", extra=e.details)
            raise conflict_error(e.message, e.details)
        except (ProcessingError, CSVParsingError, DataValidationError) as e:
            logger.error(f"Processing error: {e.message}", extra=e.details)
            raise unprocessable_entity_error(e.message, e.details)
        except (InvalidMappingError, MappingNotFoundError) as e:
            logger.warning(f"Mapping error: {e.message}", extra=e.details)
            raise bad_request_error(e.message, e.details)
        except InvalidSourceError as e:
            logger.warning(f"Invalid source: {e.message}", extra=e.details)
            raise bad_request_error(e.message, e.details)
        except FinanceProcessorError as e:
            logger.error(f"Application error: {e.message}", extra=e.details)
            raise internal_error(e.message, e.details)
        except Exception as e:
            logger.critical(f"Unexpected error: {str(e)}", exc_info=True)
            raise internal_error("An unexpected error occurred. Please try again.")
    
    return wrapper
