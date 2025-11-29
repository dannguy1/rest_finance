"""
Prometheus metrics for Financial Data Processor.
Tracks application performance and usage metrics.
"""
import time
from typing import Callable
from prometheus_client import Counter, Histogram, Gauge, Summary, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.utils.logging import processing_logger

# File upload metrics
file_upload_counter = Counter(
    'file_uploads_total',
    'Total number of file uploads',
    ['source', 'file_type', 'status']
)

file_upload_size_bytes = Summary(
    'file_upload_size_bytes',
    'Size of uploaded files in bytes',
    ['source', 'file_type']
)

# Processing metrics
processing_duration_seconds = Histogram(
    'processing_duration_seconds',
    'Time spent processing files',
    ['source', 'operation'],
    buckets=[1, 5, 10, 30, 60, 120, 300, 600]  # 1s to 10min
)

processing_errors_total = Counter(
    'processing_errors_total',
    'Total number of processing errors',
    ['source', 'error_type']
)

processing_records_total = Counter(
    'processing_records_total',
    'Total number of records processed',
    ['source']
)

processing_files_total = Counter(
    'processing_files_total',
    'Total number of files processed',
    ['source', 'status']
)

# Cache metrics
cache_hits_total = Counter(
    'cache_hits_total',
    'Total number of cache hits',
    ['cache_type']
)

cache_misses_total = Counter(
    'cache_misses_total',
    'Total number of cache misses',
    ['cache_type']
)

# Active jobs gauge
active_processing_jobs = Gauge(
    'active_processing_jobs',
    'Number of currently active processing jobs',
    ['source']
)

# HTTP request metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# Validation metrics
validation_errors_total = Counter(
    'validation_errors_total',
    'Total number of validation errors',
    ['source', 'error_type']
)

validation_duration_seconds = Histogram(
    'validation_duration_seconds',
    'Time spent validating files',
    ['source'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

# Database metrics (file-based tracking)
db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration',
    ['operation'],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0]
)

db_connections_total = Gauge(
    'db_connections_total',
    'Number of active database connections'
)

# System metrics
system_cpu_usage = Gauge(
    'system_cpu_usage_percent',
    'System CPU usage percentage'
)

system_memory_usage = Gauge(
    'system_memory_usage_percent',
    'System memory usage percentage'
)

system_disk_usage = Gauge(
    'system_disk_usage_percent',
    'System disk usage percentage'
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Middleware to collect HTTP request metrics."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and collect metrics."""
        start_time = time.time()
        
        # Get endpoint path
        endpoint = request.url.path
        method = request.method
        
        try:
            response = await call_next(request)
            status_code = response.status_code
            
            # Record metrics
            duration = time.time() - start_time
            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code
            ).inc()
            
            http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
            
            return response
            
        except Exception as e:
            # Record error
            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status_code=500
            ).inc()
            
            processing_logger.log_system_event(
                f"Request error: {str(e)}",
                level="error",
                details={"endpoint": endpoint, "method": method}
            )
            raise


# Helper functions for recording metrics
def record_file_upload(source: str, file_type: str, file_size: int, status: str = "success"):
    """Record file upload metrics."""
    file_upload_counter.labels(
        source=source,
        file_type=file_type,
        status=status
    ).inc()
    
    file_upload_size_bytes.labels(
        source=source,
        file_type=file_type
    ).observe(file_size)


def record_processing_start(source: str):
    """Record start of processing job."""
    active_processing_jobs.labels(source=source).inc()


def record_processing_complete(source: str, duration: float, records_count: int, files_count: int = 1):
    """Record successful processing completion."""
    active_processing_jobs.labels(source=source).dec()
    
    processing_duration_seconds.labels(
        source=source,
        operation="process"
    ).observe(duration)
    
    processing_records_total.labels(source=source).inc(records_count)
    
    processing_files_total.labels(
        source=source,
        status="success"
    ).inc(files_count)


def record_processing_error(source: str, error_type: str):
    """Record processing error."""
    active_processing_jobs.labels(source=source).dec()
    
    processing_errors_total.labels(
        source=source,
        error_type=error_type
    ).inc()
    
    processing_files_total.labels(
        source=source,
        status="error"
    ).inc()


def record_validation_error(source: str, error_type: str):
    """Record validation error."""
    validation_errors_total.labels(
        source=source,
        error_type=error_type
    ).inc()


def record_validation_duration(source: str, duration: float):
    """Record validation duration."""
    validation_duration_seconds.labels(source=source).observe(duration)


def record_cache_hit(cache_type: str = "default"):
    """Record cache hit."""
    cache_hits_total.labels(cache_type=cache_type).inc()


def record_cache_miss(cache_type: str = "default"):
    """Record cache miss."""
    cache_misses_total.labels(cache_type=cache_type).inc()


def record_db_query(operation: str, duration: float):
    """Record database query metrics."""
    db_query_duration_seconds.labels(operation=operation).observe(duration)


def update_system_metrics():
    """Update system resource metrics."""
    try:
        import psutil
        
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        system_cpu_usage.set(cpu_percent)
        
        # Memory usage
        memory = psutil.virtual_memory()
        system_memory_usage.set(memory.percent)
        
        # Disk usage
        disk = psutil.disk_usage('/')
        system_disk_usage.set(disk.percent)
        
    except Exception as e:
        processing_logger.log_system_event(
            f"Error updating system metrics: {str(e)}",
            level="error"
        )


# Middleware instance
metrics_middleware = PrometheusMiddleware
