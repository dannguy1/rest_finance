# Quick Reference: Error Handling & Best Practices

## For Route Handlers

### Using the Error Decorator

**Simple Route (Recommended):**
```python
from app.exceptions import handle_service_errors

@router.get("/data/{source}")
@handle_service_errors
async def get_data(source: str):
    # Your code here
    # Decorator automatically handles all exceptions
    # Converts custom exceptions to appropriate HTTP responses
    result = await some_service.get_data(source)
    return result
```

**What the Decorator Does:**
- Catches all exceptions
- Converts custom exceptions to HTTP responses with proper status codes
- Logs errors automatically
- Returns structured error responses with metadata

### Raising Errors

**Use Error Factories:**
```python
from app.exceptions import bad_request_error, not_found_error, internal_error

# Bad request (400)
raise bad_request_error(
    "Invalid source specified",
    {"source": source, "valid": ["a", "b", "c"]}
)

# Not found (404)
raise not_found_error(
    f"File '{filename}' not found",
    {"filename": filename, "source": source}
)

# Internal error (500)
raise internal_error(
    "Processing failed",
    {"error": str(e)}
)
```

**Or Raise Specific Exceptions:**
```python
from app.exceptions import InvalidSourceError, AppFileNotFoundError

# These are automatically converted by @handle_service_errors
raise InvalidSourceError(f"Invalid source: {source}")
raise AppFileNotFoundError(f"File not found: {filename}")
```

## For Service Methods

### File Operations

```python
from app.exceptions import (
    FileOperationError,
    FileAlreadyExistsError,
    InvalidFileTypeError,
    AppFileNotFoundError
)

async def save_file(source: str, file: UploadFile, filename: str):
    # Check for concurrent upload
    if lock_file.exists():
        raise FileAlreadyExistsError(f"Upload in progress: {filename}")
    
    # Validate MIME type
    is_valid, error = await validate_file_content(file_path)
    if not is_valid:
        raise InvalidFileTypeError(f"Invalid file type: {error}")
    
    # Save file
    try:
        # ... save operation
        pass
    except Exception as e:
        raise FileOperationError(f"Failed to save file: {str(e)}")
```

### Validation

```python
from app.exceptions import CSVParsingError, DataValidationError

def validate_csv(file_path: Path):
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        raise CSVParsingError(f"Failed to parse CSV: {str(e)}")
    
    if not validate_columns(df):
        raise DataValidationError("Missing required columns")
```

### Processing

```python
from app.exceptions import ProcessingError

async def process_data(source: str):
    try:
        # ... processing logic
        pass
    except Exception as e:
        raise ProcessingError(f"Processing failed: {str(e)}")
```

## Using Constants

### Instead of Magic Values

**Bad:**
```python
if file_size > 100 * 1024 * 1024:  # Magic number!
    raise HTTPException(status_code=400, detail="File too large")
```

**Good:**
```python
from app.constants import MAX_FILE_SIZE_MB, ERROR_FILE_TOO_LARGE

max_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
if file_size > max_bytes:
    raise bad_request_error(ERROR_FILE_TOO_LARGE)
```

### Available Constants

**File Operations:**
```python
from app.constants import (
    MAX_FILE_SIZE_MB,           # 100
    SUPPORTED_FILE_EXTENSIONS,  # ['.csv', '.txt']
    ALLOWED_MIME_TYPES,         # ['text/csv', 'text/plain', ...]
    LOCK_FILE_PREFIX,           # '.uploading_'
    LOCK_FILE_SUFFIX            # '.lock'
)
```

**Error Messages:**
```python
from app.constants import (
    ERROR_FILE_NOT_FOUND,      # "File not found: {filename}"
    ERROR_INVALID_FILE_TYPE,   # "Invalid file type: {extension}"
    ERROR_FILE_TOO_LARGE,      # "File exceeds maximum size..."
    ERROR_INVALID_SOURCE,      # "Invalid source: {source}..."
    SUCCESS_FILE_UPLOADED      # "File uploaded successfully"
)

# Use with .format()
message = ERROR_FILE_NOT_FOUND.format(filename="data.csv")
```

**Date Formats:**
```python
from app.constants import DATE_FORMATS

# ['%m/%d/%Y', '%Y-%m-%d', '%d/%m/%Y', ...]
for fmt in DATE_FORMATS:
    try:
        date = datetime.strptime(date_str, fmt)
        break
    except ValueError:
        continue
```

## File Locking Pattern

### Preventing Race Conditions

```python
from app.constants import LOCK_FILE_PREFIX, LOCK_FILE_SUFFIX
from app.exceptions import FileAlreadyExistsError, FileOperationError

async def save_with_lock(file_path: Path, content: bytes):
    # Create lock file path
    lock_file = file_path.parent / f"{LOCK_FILE_PREFIX}{file_path.name}{LOCK_FILE_SUFFIX}"
    
    try:
        # Check for existing lock
        if lock_file.exists():
            raise FileAlreadyExistsError(f"Upload in progress: {file_path.name}")
        
        # Create lock
        lock_file.touch()
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
            
    except FileAlreadyExistsError:
        raise  # Re-raise specific exception
    except Exception as e:
        raise FileOperationError(f"Failed to save: {str(e)}")
    finally:
        # Always cleanup lock
        if lock_file.exists():
            lock_file.unlink()
```

## MIME Type Validation

### Using FileUtils

```python
from app.utils.file_utils import FileUtils
from app.exceptions import InvalidFileTypeError

async def validate_upload(file_path: Path):
    is_valid, error_msg = await FileUtils.validate_file_content(file_path)
    if not is_valid:
        raise InvalidFileTypeError(error_msg)
```

### Graceful Degradation

The MIME validation automatically falls back to extension checking if python-magic is not available:

```python
# This works even without python-magic installed
is_valid, msg = await FileUtils.validate_file_content(file_path)
# Returns: (True, "Validation successful") - even with fallback
```

## Caching Pattern

### Using LRU Cache

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_expensive_data(key: str) -> dict:
    # This result will be cached
    return expensive_operation(key)
```

### Cache Invalidation

```python
class ConfigManager:
    _cache_version = 0
    
    @lru_cache(maxsize=128)
    def _get_cached_data(self, key: str, version: int) -> dict:
        # version parameter ensures cache miss when version changes
        return load_data(key)
    
    def get_data(self, key: str) -> dict:
        return self._get_cached_data(key, self._cache_version)
    
    def update_data(self, key: str, value: dict):
        save_data(key, value)
        # Invalidate cache
        self._cache_version += 1
```

## Logging Best Practices

### Instead of print()

**Bad:**
```python
print(f"Processing file: {filename}")
print(f"Error: {str(e)}")
```

**Good:**
```python
from app.utils.logging import processing_logger

processing_logger.log_system_event(f"Processing file: {filename}", level="info")
processing_logger.log_system_event(f"Error: {str(e)}", level="error")
processing_logger.log_file_operation("upload", filename, source, success=True)
```

### Log Levels

```python
# Info - normal operations
processing_logger.log_system_event("File uploaded", level="info")

# Warning - recoverable issues
processing_logger.log_system_event("Cache miss", level="warning")

# Error - failures
processing_logger.log_system_event("Validation failed", level="error")
```

## Exception Hierarchy Reference

```
FinanceProcessorError (base)
│
├── FileOperationError
│   ├── FileAlreadyExistsError        # File/lock already exists
│   ├── InvalidFileTypeError          # MIME validation failed
│   └── AppFileNotFoundError          # File not found
│
├── ProcessingError
│   ├── CSVParsingError              # Failed to parse CSV
│   └── DataValidationError          # Validation failed
│
├── MappingError
│   ├── InvalidSourceError           # Unknown source
│   └── MappingNotFoundError         # Mapping not found
│
└── ConfigurationError
    ├── InvalidConfigError           # Config validation failed
    └── MissingConfigError           # Required config missing
```

## HTTP Status Code Mapping

| Exception Type | HTTP Status | When to Use |
|---------------|-------------|-------------|
| `InvalidSourceError` | 400 Bad Request | Unknown source name |
| `InvalidFileTypeError` | 400 Bad Request | Wrong file type |
| `DataValidationError` | 400 Bad Request | Validation failed |
| `AppFileNotFoundError` | 404 Not Found | File doesn't exist |
| `MappingNotFoundError` | 404 Not Found | Mapping doesn't exist |
| `FileAlreadyExistsError` | 409 Conflict | Concurrent upload |
| `FileOperationError` | 500 Internal | I/O failure |
| `ProcessingError` | 500 Internal | Processing failed |
| `ConfigurationError` | 500 Internal | Config issue |

## Common Patterns

### Validate-Then-Process

```python
@router.post("/process/{source}")
@handle_service_errors
async def process(source: str, file: UploadFile):
    # 1. Validate source
    if source not in VALID_SOURCES:
        raise InvalidSourceError(f"Invalid source: {source}")
    
    # 2. Validate file type
    is_valid, error = await FileUtils.validate_file_content(temp_path)
    if not is_valid:
        raise InvalidFileTypeError(error)
    
    # 3. Validate data
    validation = validate_csv(temp_path)
    if not validation['valid']:
        raise DataValidationError("Validation failed", validation['errors'])
    
    # 4. Process
    result = await process_file(temp_path)
    return result
```

### Try-Finally for Cleanup

```python
lock_file = None
try:
    lock_file = create_lock(filename)
    result = await save_file(file)
    return result
finally:
    if lock_file and lock_file.exists():
        lock_file.unlink()  # Always cleanup
```

### Specific Then Generic Exception

```python
try:
    # Operation
    result = risky_operation()
except SpecificKnownError as e:
    raise DataValidationError(f"Known issue: {str(e)}")
except Exception as e:
    # Last resort - log and convert
    processing_logger.log_system_event(f"Unexpected error: {str(e)}", level="error")
    raise ProcessingError(f"Unexpected error: {str(e)}")
```

## Testing

### Testing Exception Handling

```python
import pytest
from app.exceptions import InvalidSourceError

def test_invalid_source():
    with pytest.raises(InvalidSourceError):
        get_source_config("invalid_source")

def test_file_not_found():
    with pytest.raises(AppFileNotFoundError):
        await file_service.delete_file("source", "nonexistent.csv")
```

### Testing Routes with Exceptions

```python
from fastapi.testclient import TestClient

def test_upload_invalid_type():
    response = client.post(
        "/api/files/upload/source",
        files={"file": ("test.exe", b"content", "application/x-executable")}
    )
    assert response.status_code == 400
    assert "Invalid file type" in response.json()["detail"]
```

## Migration Checklist

When updating existing code:

- [ ] Replace broad `except Exception` with specific types
- [ ] Add `@handle_service_errors` decorator to routes
- [ ] Remove manual try/except in routes (decorator handles it)
- [ ] Replace magic values with constants
- [ ] Replace `print()` with `processing_logger`
- [ ] Use error factories instead of `HTTPException`
- [ ] Add file locking for file operations
- [ ] Add MIME validation for file uploads
- [ ] Test error scenarios
- [ ] Update documentation

## Resources

- **Full Code Review**: [CODE_REVIEW.md](CODE_REVIEW.md)
- **Implementation Progress**: [IMPLEMENTATION_PROGRESS.md](IMPLEMENTATION_PROGRESS.md)
- **Changelog**: [CHANGELOG.md](CHANGELOG.md)
- **System Overview**: [docs/overview.md](docs/overview.md)

---

**Last Updated**: December 2024
