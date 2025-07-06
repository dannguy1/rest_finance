"""
API route modules for Financial Data Processor.
"""

from . import file_routes, processing_routes, health_routes, analytics_routes

__all__ = [
    "file_routes",
    "processing_routes",
    "health_routes",
    "analytics_routes",
] 