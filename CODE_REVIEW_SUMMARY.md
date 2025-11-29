# Code Review Summary - Immediate Actions

**Date**: November 28, 2025  
**Priority**: HIGH - Implement Before Production

## Files Created

### 1. `/CODE_REVIEW.md`
Comprehensive code review document with:
- Critical, high, medium, and low priority issues
- Security vulnerabilities identified
- Performance concerns
- Code quality recommendations
- Action items with priority matrix

### 2. `/app/constants.py`
Centralized constants to replace magic numbers:
- File processing constants (sizes, extensions, formats)
- CSV processing parameters
- Date format patterns
- Rate limiting values
- Error and success message templates
- Source IDs and names
- HTTP status codes

### 3. `/app/exceptions.py`
Custom exception hierarchy for better error handling:
- Domain-specific exceptions (FileOperationError, ProcessingError, MappingError, etc.)
- HTTP exception factories
- Error handler decorators (@handle_service_errors)
- Standardized error response format

## Critical Issues Found

### 🔴 Security Issues (MUST FIX):
1. **Broad Exception Handling** - 20+ locations using `except Exception`
2. **Missing File Content Validation** - No MIME type checking
3. **Path Traversal Risk** - Need to verify sanitization is robust
4. **No Input Validation** - CSV content not validated before processing

### 🟡 Data Integrity Issues (HIGH PRIORITY):
1. **No Transaction Support** - Partial failures leave inconsistent state
2. **Race Conditions** - Multiple uploads can conflict
3. **Silent Failures** - Errors only printed, not logged properly

### 🟠 Performance Issues (MEDIUM PRIORITY):
1. **Blocking I/O** - Synchronous operations in async functions
2. **Memory Usage** - Large files loaded entirely into memory
3. **No Caching** - Mappings loaded from disk every time

## Implementation Recommendations

### Phase 1: Critical Fixes (This Week)

#### 1. Update File Service with Specific Exceptions
```python
# app/services/file_service.py
from app.exceptions import FileOperationError, FileNotFoundError, FileAlreadyExistsError
from app.constants import LOCK_FILE_PREFIX, LOCK_FILE_SUFFIX

async def save_uploaded_file(self, source: str, file, filename: str) -> bool:
    """Save uploaded file with proper error handling and locking."""
    lock_file = None
    try:
        source_dir = self.data_dir / source / "input"
        FileUtils.ensure_directory(source_dir)
        
        safe_filename = FileUtils.sanitize_filename(filename)
        file_path = source_dir / safe_filename
        
        # Check if file exists
        if file_path.exists():
            raise FileAlreadyExistsError(
                f"File already exists: {safe_filename}",
                {"filename": safe_filename, "source": source}
            )
        
        # Create lock file
        lock_file = file_path.parent / f"{LOCK_FILE_PREFIX}{safe_filename}{LOCK_FILE_SUFFIX}"
        
        # Save file with lock
        async with aiofiles.open(lock_file, 'w') as lock:
            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
        
        processing_logger.log_file_operation("upload", safe_filename, source, True)
        return True
        
    except FileAlreadyExistsError:
        raise  # Re-raise custom exceptions
    except (IOError, PermissionError) as e:
        processing_logger.log_file_operation("upload", filename, source, False, str(e))
        raise FileOperationError(
            f"Failed to save file: {filename}",
            {"error": str(e), "source": source}
        )
    except Exception as e:
        processing_logger.log_system_event(
            f"Unexpected error in file upload: {str(e)}",
            level="critical",
            details={"filename": filename, "source": source}
        )
        raise
    finally:
        # Clean up lock file
        if lock_file and lock_file.exists():
            lock_file.unlink(missing_ok=True)
```

#### 2. Add File Content Validation
```python
# app/utils/file_utils.py
import magic
from app.constants import ALLOWED_CSV_MIME_TYPES, ALLOWED_PDF_MIME_TYPES
from app.exceptions import InvalidFileTypeError

class FileUtils:
    @staticmethod
    async def validate_file_content(file_path: Path, expected_extension: str) -> bool:
        """
        Validate file content matches expected type.
        
        Args:
            file_path: Path to file
            expected_extension: Expected file extension (.csv or .pdf)
            
        Returns:
            True if valid
            
        Raises:
            InvalidFileTypeError: If content doesn't match extension
        """
        try:
            # Read file magic bytes
            async with aiofiles.open(file_path, 'rb') as f:
                header = await f.read(2048)
            
            mime_type = magic.from_buffer(header, mime=True)
            
            if expected_extension == '.csv':
                if mime_type not in ALLOWED_CSV_MIME_TYPES:
                    raise InvalidFileTypeError(
                        f"File content type '{mime_type}' does not match CSV extension",
                        {"mime_type": mime_type, "expected": "CSV"}
                    )
            elif expected_extension == '.pdf':
                if mime_type not in ALLOWED_PDF_MIME_TYPES:
                    raise InvalidFileTypeError(
                        f"File content type '{mime_type}' does not match PDF extension",
                        {"mime_type": mime_type, "expected": "PDF"}
                    )
            
            return True
            
        except InvalidFileTypeError:
            raise
        except Exception as e:
            processing_logger.log_system_event(
                f"File content validation failed: {str(e)}",
                level="error"
            )
            raise FileValidationError(
                "Failed to validate file content",
                {"error": str(e)}
            )
```

#### 3. Add Caching for Mappings
```python
# app/config/source_mapping.py
from functools import lru_cache
from app.constants import MAX_CACHE_SIZE

class SourceMappingManager:
    @lru_cache(maxsize=MAX_CACHE_SIZE)
    def get_mapping(self, source_id: str) -> Optional[SourceMappingConfig]:
        """Get mapping configuration for a source (cached)."""
        return self.mappings.get(source_id.lower())
    
    def add_mapping(self, mapping: SourceMappingConfig) -> None:
        """Add or update a mapping configuration."""
        self.mappings[mapping.source_id.lower()] = mapping
        self._save_mapping(mapping)
        # Clear cache when mapping is updated
        self.get_mapping.cache_clear()
```

#### 4. Use Error Handling Decorators in Routes
```python
# app/api/routes/file_routes.py
from app.exceptions import handle_service_errors
from app.constants import SUCCESS_FILE_UPLOADED, ERROR_FILE_TOO_LARGE

@router.post("/upload/{source}")
@handle_service_errors
@limiter.limit(settings.rate_limit_upload)
async def upload_files(request: Request, source: str, files: List[UploadFile] = File(...)):
    """Upload files for a specific source with enhanced error handling."""
    if not FileService.validate_source(source):
        raise InvalidSourceError(
            f"Invalid source: {source}",
            {"source": source, "supported": list(SOURCE_NAMES.keys())}
        )
    
    uploaded_files = []
    
    for file in files:
        # Validate file size
        content = await file.read()
        if len(content) > MAX_FILE_SIZE_BYTES:
            raise FileTooLargeError(
                ERROR_FILE_TOO_LARGE.format(max_size=MAX_FILE_SIZE_MB),
                {"file": file.filename, "size": len(content)}
            )
        
        # Reset file pointer
        await file.seek(0)
        
        # Save file (will raise specific exceptions on error)
        success = await file_service.save_uploaded_file(source, file, file.filename)
        if success:
            uploaded_files.append(file.filename)
    
    return {
        "message": SUCCESS_FILE_UPLOADED.format(filename=", ".join(uploaded_files)),
        "files": uploaded_files,
        "count": len(uploaded_files)
    }
```

### Phase 2: Testing (Next Week)

#### Add Integration Tests
```python
# tests/test_concurrent_operations.py
import pytest
import asyncio
from app.services.file_service import FileService

@pytest.mark.asyncio
async def test_concurrent_file_uploads():
    """Test concurrent uploads don't create race conditions."""
    file_service = FileService()
    
    # Simulate concurrent uploads of same file
    async def upload_file(file_num):
        # Mock file upload
        return await file_service.save_uploaded_file(
            "chase",
            mock_file,
            "test.csv"
        )
    
    tasks = [upload_file(i) for i in range(5)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Only one should succeed, others should raise FileAlreadyExistsError
    successes = [r for r in results if r is True]
    errors = [r for r in results if isinstance(r, Exception)]
    
    assert len(successes) == 1
    assert len(errors) == 4
    assert all(isinstance(e, FileAlreadyExistsError) for e in errors)
```

### Phase 3: Monitoring (This Month)

#### Add Prometheus Metrics
```python
# app/metrics.py
from prometheus_client import Counter, Histogram, Gauge

# File upload metrics
file_uploads_total = Counter(
    'file_uploads_total',
    'Total number of file uploads',
    ['source', 'status']
)

file_upload_size_bytes = Histogram(
    'file_upload_size_bytes',
    'Size of uploaded files in bytes',
    ['source']
)

# Processing metrics
processing_duration_seconds = Histogram(
    'processing_duration_seconds',
    'Time spent processing files',
    ['source']
)

processing_jobs_active = Gauge(
    'processing_jobs_active',
    'Number of active processing jobs'
)

# Error metrics
errors_total = Counter(
    'errors_total',
    'Total number of errors',
    ['error_type', 'endpoint']
)
```

## Next Steps

1. **Review CODE_REVIEW.md** - Understand all issues
2. **Install Dependencies** - Add `python-magic` to requirements.txt
3. **Implement Phase 1 Fixes** - Security and error handling
4. **Add Tests** - Concurrent operations and error cases
5. **Update Documentation** - Document new error codes
6. **Security Audit** - External review after fixes

## Dependencies to Add

```bash
# Add to requirements.txt
python-magic==0.4.27
prometheus-client==0.19.0
```

## Configuration Updates

```python
# config/settings.py
# Add file validation settings
FILE_CONTENT_VALIDATION_ENABLED = os.getenv("FILE_CONTENT_VALIDATION", "True").lower() == "true"
ENABLE_FILE_LOCKING = os.getenv("ENABLE_FILE_LOCKING", "True").lower() == "true"
ENABLE_METRICS = os.getenv("ENABLE_METRICS", "False").lower() == "true"
```

## Estimated Effort

- **Phase 1 (Critical)**: 2-3 days
- **Phase 2 (Testing)**: 2 days
- **Phase 3 (Monitoring)**: 1-2 days

**Total**: ~1 week for essential improvements

---

**Status**: Ready for implementation
**Reviewed by**: AI Code Review
**Next Review**: After Phase 1 completion
