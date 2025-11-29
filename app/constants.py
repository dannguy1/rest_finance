"""
Application-wide constants for Financial Data Processor.
Centralizes magic numbers, strings, and configuration values.
"""
from typing import List

# File Processing Constants
MAX_FILE_SIZE_MB: int = 10
MAX_FILE_SIZE_BYTES: int = MAX_FILE_SIZE_MB * 1024 * 1024
SUPPORTED_FILE_EXTENSIONS: List[str] = ['.csv', '.pdf']
ALLOWED_CSV_MIME_TYPES: List[str] = ['text/csv', 'text/plain', 'application/csv']
ALLOWED_PDF_MIME_TYPES: List[str] = ['application/pdf']

# CSV Processing Constants
DEFAULT_DATE_FORMAT: str = "MM/DD/YYYY"
DEFAULT_AMOUNT_FORMAT: str = "USD"
CSV_CHUNK_SIZE: int = 10000
MAX_CSV_PREVIEW_ROWS: int = 50
MIN_REQUIRED_FIELDS: int = 3

# Date Format Patterns
DATE_FORMATS: List[str] = [
    "%m/%d/%Y",   # MM/DD/YYYY
    "%Y-%m-%d",   # YYYY-MM-DD
    "%m-%d-%Y",   # MM-DD-YYYY
    "%d/%m/%Y",   # DD/MM/YYYY
    "%Y/%m/%d"    # YYYY/MM/DD
]

# Processing Constants
PROCESSING_TIMEOUT_SECONDS: int = 300
MAX_CONCURRENT_JOBS: int = 5
BATCH_SIZE: int = 1000

# File Organization
INPUT_DIR_NAME: str = "input"
OUTPUT_DIR_NAME: str = "output"
BACKUP_DIR_NAME: str = "backups"
METADATA_DIR_NAME: str = "source_metadata"
TEMP_DIR_NAME: str = ".temp"

# Logging Constants
LOG_LEVEL_INFO: str = "info"
LOG_LEVEL_WARNING: str = "warning"
LOG_LEVEL_ERROR: str = "error"
LOG_LEVEL_CRITICAL: str = "critical"
LOG_LEVEL_DEBUG: str = "debug"

# Rate Limiting
RATE_LIMIT_UPLOAD: str = "10/minute"
RATE_LIMIT_PROCESS: str = "5/minute"
RATE_LIMIT_DOWNLOAD: str = "30/minute"
RATE_LIMIT_API: str = "100/minute"

# Cache Settings
CACHE_TTL_SECONDS: int = 300
MAX_CACHE_SIZE: int = 128

# Validation Thresholds
MIN_CONVERSION_SUCCESS_RATE: float = 0.8
MAX_MALFORMED_ROW_PERCENTAGE: float = 0.3
MAX_EMPTY_VALUE_PERCENTAGE: float = 0.5

# Source IDs (normalized)
SOURCE_BANK_OF_AMERICA: str = "bankofamerica"
SOURCE_CHASE: str = "chase"
SOURCE_RESTAURANT_DEPOT: str = "restaurantdepot"
SOURCE_SYSCO: str = "sysco"
SOURCE_GG: str = "gg"
SOURCE_AR: str = "ar"

# Source Display Names
SOURCE_NAMES: dict = {
    SOURCE_BANK_OF_AMERICA: "Bank of America",
    SOURCE_CHASE: "Chase",
    SOURCE_RESTAURANT_DEPOT: "Restaurant Depot",
    SOURCE_SYSCO: "Sysco",
    SOURCE_GG: "GG",
    SOURCE_AR: "AR"
}

# HTTP Status Codes
HTTP_OK: int = 200
HTTP_CREATED: int = 201
HTTP_BAD_REQUEST: int = 400
HTTP_UNAUTHORIZED: int = 401
HTTP_FORBIDDEN: int = 403
HTTP_NOT_FOUND: int = 404
HTTP_CONFLICT: int = 409
HTTP_INTERNAL_ERROR: int = 500

# Error Messages
ERROR_FILE_TOO_LARGE: str = "File size exceeds maximum allowed size of {max_size}MB"
ERROR_INVALID_FILE_TYPE: str = "Invalid file type. Allowed types: {allowed_types}"
ERROR_FILE_NOT_FOUND: str = "File not found: {filename}"
ERROR_PROCESSING_FAILED: str = "Failed to process file. Please check file format and try again."
ERROR_INVALID_SOURCE: str = "Invalid source: {source}. Supported sources: {supported_sources}"
ERROR_MISSING_REQUIRED_COLUMN: str = "Missing required column: {column}"
ERROR_DUPLICATE_FILE: str = "File already exists or is being processed: {filename}"

# Success Messages
SUCCESS_FILE_UPLOADED: str = "File uploaded successfully: {filename}"
SUCCESS_FILE_PROCESSED: str = "File processed successfully: {filename}"
SUCCESS_FILE_DELETED: str = "File deleted successfully: {filename}"
SUCCESS_MAPPING_SAVED: str = "Mapping configuration saved successfully"

# Encoding
DEFAULT_ENCODING: str = "utf-8"
ENCODING_UTF8_BOM: str = "utf-8-sig"
SUPPORTED_ENCODINGS: List[str] = [DEFAULT_ENCODING, ENCODING_UTF8_BOM, "latin-1", "iso-8859-1"]

# File Naming
TEMP_FILE_PREFIX: str = "temp_"
BACKUP_FILE_SUFFIX: str = "_backup"
LOCK_FILE_PREFIX: str = "."
LOCK_FILE_SUFFIX: str = ".lock"
