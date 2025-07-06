"""
File management routes for Financial Data Processor.
"""
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Request
from fastapi.responses import FileResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings
from app.utils.logging import processing_logger
from app.services.file_service import FileService
from app.services.validation_service import ValidationService
from app.models.file_models import SourceType, ProcessingOptions
from app.config.source_mapping import mapping_manager

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

# Initialize services
file_service = FileService()
validation_service = ValidationService()

def get_source_config(source_slug: str) -> dict:
    """Get source configuration by slug using mapping manager."""
    mapping = mapping_manager.get_mapping(source_slug)
    if not mapping:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid source '{source_slug}'. Supported sources: {', '.join(mapping_manager.get_all_mappings().keys())}"
        )
    
    # Convert mapping to legacy format for compatibility
    # Use source_id directly as directory name (no conversion needed)
    return {
        "name": mapping.source_id,  # Use source_id directly
        "display_name": mapping.display_name,
        "description": mapping.description,
        "required_columns": mapping.required_columns,
        "optional_columns": [opt.source_column for opt in mapping.optional_mappings],
        "date_column": mapping.date_mapping.source_column,
        "description_column": mapping.description_mapping.source_column,
        "amount_column": mapping.amount_mapping.source_column,
        "date_format": mapping.default_date_format
    }

def validate_source_format(source_config: dict, filename: str) -> None:
    """Validate that file format matches source requirements."""
    # This would be called during upload/validation
    pass

@router.get("/list/{source}")
@limiter.limit(settings.rate_limit_api)
async def list_files(source: str, request: Request):
    """List uploaded files for a specific source."""
    try:
        source_config = get_source_config(source)
        source_enum = source_config["name"]
        
        files = await file_service.get_source_files(source_enum)
        
        return {
            "source": source_enum,
            "source_display": source_config["display_name"],
            "description": source_config["description"],
            "required_format": {
                "required_columns": source_config["required_columns"],
                "date_format": source_config["date_format"],
                "optional_columns": source_config.get("optional_columns", [])
            },
            "files": files,
            "count": len(files)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        processing_logger.log_system_event(
            f"Error listing files for {source}: {str(e)}", level="error"
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{source}/{filename}")
@limiter.limit(settings.rate_limit_api)
async def delete_file(source: str, filename: str, request: Request):
    """Delete a file from a source."""
    try:
        source_config = get_source_config(source)
        source_enum = source_config["name"]
        
        success = await file_service.delete_file(source_enum, filename)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"File '{filename}' not found for {source_config['display_name']}"
            )
        
        return {
            "message": "File deleted successfully",
            "filename": filename,
            "source": source_enum,
            "source_display": source_config["display_name"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        processing_logger.log_file_operation("delete", filename, source, False, str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/validate/{source}/{filename}")
@limiter.limit(settings.rate_limit_api)
async def validate_file(source: str, filename: str, request: Request):
    """Validate a file for processing with source-specific requirements."""
    try:
        source_config = get_source_config(source)
        source_enum = source_config["name"]
        
        from pathlib import Path
        file_path = settings.data_path / source_enum / "input" / filename
        
        if not file_path.exists():
            raise HTTPException(
                status_code=404, 
                detail=f"File '{filename}' not found for {source_config['display_name']}"
            )
        
        validation_result = validation_service.validate_csv_file(file_path, source_enum)
        
        return {
            "filename": filename,
            "source": source_enum,
            "source_display": source_config["display_name"],
            "expected_format": {
                "required_columns": source_config["required_columns"],
                "date_format": source_config["date_format"],
                "optional_columns": source_config.get("optional_columns", [])
            },
            **validation_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        processing_logger.log_system_event(
            f"Error validating file {filename} for {source}: {str(e)}", level="error"
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/backup/{source}/{filename}")
@limiter.limit(settings.rate_limit_api)
async def backup_file(source: str, filename: str, request: Request):
    """Create a backup of a file."""
    try:
        source_config = get_source_config(source)
        source_enum = source_config["name"]
        
        backup_path = await file_service.backup_file(source_enum, filename)
        
        if not backup_path:
            raise HTTPException(
                status_code=404,
                detail=f"File '{filename}' not found for {source_config['display_name']} or backup failed"
            )
        
        return {
            "message": "File backed up successfully",
            "filename": filename,
            "source": source_enum,
            "source_display": source_config["display_name"],
            "backup_path": str(backup_path)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        processing_logger.log_system_event(
            f"Error backing up file {filename} for {source}: {str(e)}", level="error"
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/output/{source}")
@limiter.limit(settings.rate_limit_download)
async def list_output_files(source: str, request: Request, year: Optional[int] = None):
    """List output files for a source."""
    try:
        source_config = get_source_config(source)
        source_enum = source_config["name"]
        
        files = await file_service.get_output_files(source_enum, year)
        
        return {
            "source": source_enum,
            "source_display": source_config["display_name"],
            "year": year,
            "files": files,
            "count": len(files)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        processing_logger.log_system_event(
            f"Error listing output files for {source}: {str(e)}", level="error"
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download/{source}/{year}/{month}")
@limiter.limit(settings.rate_limit_download)
async def download_output_file(source: str, year: int, month: int, request: Request):
    """Download an output file."""
    try:
        source_config = get_source_config(source)
        source_enum = source_config["name"]
        
        from pathlib import Path
        
        file_path = settings.data_path / source_enum / "output" / str(year) / f"{month:02d}_{year}.csv"
        
        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Processed file not found for {source_config['display_name']} {year}/{month:02d}"
            )
        
        return FileResponse(
            path=str(file_path),
            filename=f"{source_config['display_name']}_{year}_{month:02d}.csv",
            media_type="text/csv"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        processing_logger.log_system_event(
            f"Error downloading file for {source} {year}/{month}: {str(e)}", level="error"
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{source}")
@limiter.limit(settings.rate_limit_api)
async def get_source_files(source: str, request: Request, year: Optional[int] = None, month: Optional[int] = None):
    """Get processed files for a source with optional year/month filtering."""
    try:
        source_config = get_source_config(source)
        source_enum = source_config["name"]
        
        files = await file_service.get_processed_files(source_enum, year, month)
        years = await file_service.get_available_years(source_enum)
        
        return {
            "source": source_enum,
            "source_display": source_config["display_name"],
            "description": source_config["description"],
            "files": files,
            "years": years,
            "count": len(files)
        }
    except HTTPException:
        raise
    except Exception as e:
        processing_logger.log_system_event(
            f"Error getting files for {source}: {str(e)}", level="error"
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/preview/{source}")
@limiter.limit(settings.rate_limit_api)
async def preview_file(source: str, request: Request, file: str):
    """Preview a processed file."""
    try:
        source_config = get_source_config(source)
        source_enum = source_config["name"]
        
        preview_data = await file_service.preview_file(source_enum, file)
        if not preview_data:
            raise HTTPException(
                status_code=404, 
                detail=f"File '{file}' not found for {source_config['display_name']}"
            )
        return preview_data
    except HTTPException:
        raise
    except Exception as e:
        processing_logger.log_system_event(
            f"Error previewing file {file} for {source}: {str(e)}", level="error"
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/preview-uploaded/{source}")
@limiter.limit(settings.rate_limit_api)
async def preview_uploaded_file(source: str, request: Request, file: str):
    """Preview an uploaded CSV file."""
    try:
        source_config = get_source_config(source)
        source_enum = source_config["name"]
        
        preview_data = await file_service.preview_uploaded_file(source_enum, file)
        if not preview_data:
            raise HTTPException(
                status_code=404, 
                detail=f"File '{file}' not found for {source_config['display_name']}"
            )
        return preview_data
    except HTTPException:
        raise
    except Exception as e:
        processing_logger.log_system_event(
            f"Error previewing uploaded file {file} for {source}: {str(e)}", level="error"
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/preview-uploaded-full/{source}")
@limiter.limit(settings.rate_limit_api)
async def preview_uploaded_file_full(source: str, request: Request, file: str):
    """Preview an uploaded CSV file with all rows."""
    try:
        source_config = get_source_config(source)
        source_enum = source_config["name"]
        
        preview_data = await file_service.preview_uploaded_file_full(source_enum, file)
        if not preview_data:
            raise HTTPException(
                status_code=404, 
                detail=f"File '{file}' not found for {source_config['display_name']}"
            )
        return preview_data
    except HTTPException:
        raise
    except Exception as e:
        processing_logger.log_system_event(
            f"Error previewing uploaded file {file} for {source}: {str(e)}", level="error"
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/preview-full/{source}")
@limiter.limit(settings.rate_limit_api)
async def preview_file_full(source: str, request: Request, file: str):
    """Preview a processed file with all rows."""
    try:
        source_config = get_source_config(source)
        source_enum = source_config["name"]
        
        preview_data = await file_service.preview_file_full(source_enum, file)
        if not preview_data:
            raise HTTPException(
                status_code=404, 
                detail=f"File '{file}' not found for {source_config['display_name']}"
            )
        return preview_data
    except HTTPException:
        raise
    except Exception as e:
        processing_logger.log_system_event(
            f"Error previewing file {file} for {source}: {str(e)}", level="error"
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download/{source}")
@limiter.limit(settings.rate_limit_download)
async def download_file(source: str, request: Request, file: str):
    """Download a processed file."""
    try:
        source_config = get_source_config(source)
        source_enum = source_config["name"]
        
        file_path = await file_service.get_file_path(source_enum, file)
        if not file_path or not file_path.exists():
            raise HTTPException(
                status_code=404, 
                detail=f"File '{file}' not found for {source_config['display_name']}"
            )
        return FileResponse(
            path=str(file_path),
            filename=file_path.name,
            media_type='text/csv'
        )
    except HTTPException:
        raise
    except Exception as e:
        processing_logger.log_system_event(
            f"Error downloading file {file} for {source}: {str(e)}", level="error"
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload/{source}")
@limiter.limit(settings.rate_limit_upload)
async def upload_files(
    source: str,
    request: Request,
    files: List[UploadFile] = File(...)
):
    """Upload multiple files for a source with enhanced metadata-based validation."""
    try:
        source_config = get_source_config(source)
        source_enum = source_config["name"]
        
        # Check if we have saved metadata for this source
        from app.services.sample_data_service import sample_data_service
        saved_metadata = sample_data_service.get_processed_data(source)
        
        uploaded_files = []
        for file in files:
            # Validate file type
            if not validation_service.validate_file_extension(file.filename):
                uploaded_files.append({
                    "name": file.filename,
                    "size": file.size,
                    "status": "failed",
                    "error": "Invalid file type. Only CSV files are supported."
                })
                continue
            
            # Save file first
            success = await file_service.save_uploaded_file(source_enum, file, file.filename)
            if not success:
                uploaded_files.append({
                    "name": file.filename,
                    "size": file.size,
                    "status": "failed",
                    "error": "Failed to save file"
                })
                processing_logger.log_file_operation("upload", file.filename, source_enum, False)
                continue
            
            # Perform validation based on available metadata
            validation_result = None
            if saved_metadata:
                # Use metadata-based validation
                from pathlib import Path
                file_path = settings.data_path / source_enum / "input" / file.filename
                validation_result = validation_service.validate_file_against_metadata(file_path, source)
            else:
                # Fall back to basic validation
                from pathlib import Path
                file_path = settings.data_path / source_enum / "input" / file.filename
                validation_result = validation_service.validate_csv_file(file_path, source_enum)
            
            # Determine upload status based on validation
            if validation_result['valid']:
                uploaded_files.append({
                    "name": file.filename,
                    "size": file.size,
                    "status": "uploaded",
                    "validation": {
                        "valid": True,
                        "warnings": validation_result.get('warnings', []),
                        "metadata_validation": validation_result.get('metadata_validation', {}),
                        "record_count": validation_result.get('record_count', 0)
                    },
                    "expected_format": {
                        "required_columns": source_config["required_columns"],
                        "date_format": source_config["date_format"]
                    }
                })
                processing_logger.log_file_operation("upload", file.filename, source_enum, True)
            else:
                # File is invalid, but we still saved it - user can review and fix
                uploaded_files.append({
                    "name": file.filename,
                    "size": file.size,
                    "status": "uploaded_with_errors",
                    "validation": {
                        "valid": False,
                        "errors": validation_result.get('errors', []),
                        "warnings": validation_result.get('warnings', []),
                        "metadata_validation": validation_result.get('metadata_validation', {}),
                        "record_count": validation_result.get('record_count', 0)
                    },
                    "expected_format": {
                        "required_columns": source_config["required_columns"],
                        "date_format": source_config["date_format"]
                    }
                })
                processing_logger.log_file_operation("upload", file.filename, source_enum, True)
        
        successful_count = len([f for f in uploaded_files if f['status'] in ['uploaded', 'uploaded_with_errors']])
        valid_count = len([f for f in uploaded_files if f['status'] == 'uploaded'])
        
        return {
            "message": f"Uploaded {successful_count} files for {source_config['display_name']} ({valid_count} valid)",
            "source": source_enum,
            "source_display": source_config["display_name"],
            "files": uploaded_files,
            "total": len(files),
            "successful": successful_count,
            "valid": valid_count,
            "has_metadata": saved_metadata is not None,
            "expected_format": {
                "required_columns": source_config["required_columns"],
                "date_format": source_config["date_format"],
                "optional_columns": source_config.get("optional_columns", [])
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        processing_logger.log_system_event(
            f"Error uploading files for {source}: {str(e)}", level="error"
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/process/{source}/{filename}")
@limiter.limit(settings.rate_limit_process)
async def process_file(
    source: str,
    filename: str,
    request: Request,
    options: Optional[ProcessingOptions] = None
):
    """Process a single uploaded file."""
    try:
        source_config = get_source_config(source)
        source_enum = source_config["name"]
        
        from app.services.processing_service import DataProcessor
        processor = DataProcessor()
        
        # Process the specific file
        result = await processor.process_single_file(source_enum, filename, options)
        
        if result.success:
            processing_logger.log_file_operation("process", filename, source_enum, True)
            return {
                "message": f"File processed successfully for {source_config['display_name']}",
                "filename": filename,
                "source": source_enum,
                "source_display": source_config["display_name"],
                "files_processed": result.files_processed,
                "output_files": result.output_files,
                "processing_time": result.processing_time
            }
        else:
            processing_logger.log_file_operation("process", filename, source_enum, False, result.error_message)
            raise HTTPException(
                status_code=500,
                detail=result.error_message or f"Processing failed for {source_config['display_name']}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        processing_logger.log_file_operation("process", filename, source, False, str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/processed/{source}/{year}/{month}")
@limiter.limit(settings.rate_limit_api)
async def delete_processed_file(source: str, year: int, month: int, request: Request):
    """Delete a processed file for a specific source, year, and month."""
    try:
        source_config = get_source_config(source)
        source_enum = source_config["name"]
        
        from pathlib import Path
        
        # Construct the file path
        file_path = settings.data_path / source_enum / "output" / str(year) / f"{month:02d}_{year}.csv"
        
        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Processed file not found for {source_config['display_name']} {year}/{month:02d}"
            )
        
        # Delete the file
        file_path.unlink()
        
        processing_logger.log_file_operation("delete", f"{month:02d}_{year}.csv", source_enum, True)
        
        return {
            "message": "Processed file deleted successfully",
            "source": source_enum,
            "source_display": source_config["display_name"],
            "year": year,
            "month": month,
            "filename": f"{month:02d}_{year}.csv"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        processing_logger.log_file_operation("delete", f"{month:02d}_{year}.csv", source, False, str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/validate/{source}")
@limiter.limit(settings.rate_limit_api)
async def validate_uploaded_files(source: str, request: Request):
    """Validate uploaded files for a specific source with enhanced metadata-based validation."""
    try:
        source_config = get_source_config(source)
        source_enum = source_config["name"]
        
        # Check if we have saved metadata for this source
        from app.services.sample_data_service import sample_data_service
        saved_metadata = sample_data_service.get_processed_data(source)
        
        # Get all uploaded files for this source
        files = await file_service.get_source_files(source_enum)
        
        validation_results = []
        for file_info in files:
            filename = file_info.get('filename')
            if not filename:
                continue
            
            # Perform validation based on available metadata
            validation_result = None
            if saved_metadata:
                # Use metadata-based validation
                from pathlib import Path
                file_path = settings.data_path / source_enum / "input" / filename
                validation_result = validation_service.validate_file_against_metadata(file_path, source)
            else:
                # Fall back to basic validation
                validation_result = await file_service.validate_file(source_enum, filename)
            
            validation_results.append({
                "filename": filename,
                "size_mb": file_info.get('size_mb', 0),
                "upload_date": file_info.get('created'),
                "validation": validation_result,
                "has_metadata_validation": saved_metadata is not None
            })
        
        return {
            "source": source_enum,
            "source_display": source_config["display_name"],
            "expected_format": {
                "required_columns": source_config["required_columns"],
                "date_format": source_config["date_format"],
                "optional_columns": source_config.get("optional_columns", [])
            },
            "files_validated": len(validation_results),
            "has_metadata": saved_metadata is not None,
            "results": validation_results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        processing_logger.log_system_event(
            f"Error validating files for {source}: {str(e)}", level="error"
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analyze/{source}/{filename}")
@limiter.limit(settings.rate_limit_api)
async def analyze_file(source: str, filename: str, request: Request):
    """Analyze a specific file with enhanced validation and issue detection."""
    try:
        source_config = get_source_config(source)
        source_enum = source_config["name"]
        
        from pathlib import Path
        file_path = settings.data_path / source_enum / "input" / filename
        
        if not file_path.exists():
            raise HTTPException(
                status_code=404, 
                detail=f"File '{filename}' not found for {source_config['display_name']}"
            )
        
        # Use enhanced validation service
        validation_result = validation_service.validate_csv_file(file_path, source_enum)
        
        # Debug: Log the validation result
        processing_logger.log_system_event(
            f"Validation result for {filename}: {validation_result}", level="info"
        )
        processing_logger.log_system_event(
            f"Issues detected: {validation_result.get('issues_detected', [])}", level="info"
        )
        
        # Get sample data for display
        import pandas as pd
        import numpy as np
        df = pd.read_csv(file_path)
        file_columns = list(df.columns)
        
        # Get sample data (first 5 rows) with proper JSON serialization
        sample_df = df.head(5)
        sample_records = []
        for _, row in sample_df.iterrows():
            record = {}
            for col in df.columns:
                value = row[col]
                # Handle infinite and NaN values
                if pd.isna(value):
                    record[col] = None
                elif isinstance(value, (int, float)) and (pd.isna(value) or np.isinf(value)):
                    record[col] = None
                else:
                    record[col] = str(value) if not isinstance(value, (int, float, str, bool)) else value
            sample_records.append(record)
        
        analysis = {
            "source": source_enum,
            "filename": filename,
            "file_size_bytes": file_path.stat().st_size,
            "columns": file_columns,
            "sample_data": sample_records,
            "validation": validation_result
        }
        
        return {
            "filename": filename,
            "source": source_enum,
            "source_display": source_config["display_name"],
            "expected_format": {
                "required_columns": source_config["required_columns"],
                "date_format": source_config["date_format"],
                "optional_columns": source_config.get("optional_columns", [])
            },
            "analysis": analysis
        }
        
    except HTTPException:
        raise
    except Exception as e:
        processing_logger.log_system_event(
            f"Error analyzing file {filename} for {source}: {str(e)}", level="error"
        )
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.post("/fix/{source}/{filename}")
@limiter.limit(settings.rate_limit_api)
async def apply_automatic_fixes(source: str, filename: str, request: Request):
    """Apply automatic fixes to a file."""
    try:
        source_config = get_source_config(source)
        source_enum = source_config["name"]
        
        from pathlib import Path
        file_path = settings.data_path / source_enum / "input" / filename
        
        if not file_path.exists():
            raise HTTPException(
                status_code=404, 
                detail=f"File '{filename}' not found for {source_config['display_name']}"
            )
        
        # Get the validation result to see what issues need fixing
        validation_result = validation_service.validate_csv_file(file_path, source_enum)
        
        # Apply fixes for each detected issue
        fixes_applied = []
        issues_detected = validation_result.get('issues_detected', [])
        
        for issue in issues_detected:
            if issue.get('fixable', False):
                fix_result = validation_service._apply_source_specific_fix(file_path, source_enum, issue)
                if fix_result['success']:
                    fixes_applied.append(fix_result['message'])
                    processing_logger.log_system_event(
                        f"Applied fix for {issue['type']}: {fix_result['message']}", level="info"
                    )
        
        if fixes_applied:
            return {
                "message": "Automatic fixes applied successfully",
                "filename": filename,
                "source": source_enum,
                "source_display": source_config["display_name"],
                "fixes_applied": fixes_applied
            }
        else:
            return {
                "message": "No automatic fixes were needed",
                "filename": filename,
                "source": source_enum,
                "source_display": source_config["display_name"],
                "fixes_applied": []
            }
        
    except HTTPException:
        raise
    except Exception as e:
        processing_logger.log_system_event(
            f"Error applying fixes to file {filename} for {source}: {str(e)}", level="error"
        )
        raise HTTPException(status_code=500, detail=f"Failed to apply fixes: {str(e)}")

@router.get("/formats/{source}")
@limiter.limit(settings.rate_limit_api)
async def get_source_format(source: str, request: Request):
    """Get the expected file format for a specific source."""
    try:
        source_config = get_source_config(source)
        
        return {
            "source": source_config["name"],
            "source_display": source_config["display_name"],
            "description": source_config["description"],
            "format": {
                "required_columns": source_config["required_columns"],
                "date_format": source_config["date_format"],
                "optional_columns": source_config.get("optional_columns", []),
                "example": {
                    "BankOfAmerica": [
                        {"Status": "Posted", "Date": "12/31/2024", "Original Description": "DEBIT CARD PURCHASE", "Amount": "25.50"},
                        {"Status": "Posted", "Date": "12/30/2024", "Original Description": "ACH CREDIT", "Amount": "1000.00"}
                    ],
                    "Chase": [
                        {"Details": "CREDIT", "Posting Date": "12/31/2024", "Description": "ACH CREDIT", "Amount": "471.34", "Type": "ACH_CREDIT", "Balance": "42652.73"},
                        {"Details": "DEBIT", "Posting Date": "12/30/2024", "Description": "DEBIT CARD PURCHASE", "Amount": "-25.50", "Type": "ACH_DEBIT", "Balance": "42181.39"}
                    ],
                    "RestaurantDepot": [
                        {"Date": "12/31/2024", "Description": "Invoice #12345", "Total": "1500.00"},
                        {"Date": "12/30/2024", "Description": "Invoice #12344", "Total": "750.25"}
                    ],
                    "Sysco": [
                        {"Date": "12/31/2024", "Description": "Invoice #67890", "Total": "2200.00"},
                        {"Date": "12/30/2024", "Description": "Invoice #67889", "Total": "1800.75"}
                    ]
                }.get(source_config["name"], [])
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        processing_logger.log_system_event(
            f"Error getting format for {source}: {str(e)}", level="error"
        )
        raise HTTPException(status_code=500, detail=str(e))

# Analytics endpoints
@router.get("/analytics/{source}/group-by-description")
@limiter.limit(settings.rate_limit_api)
async def analytics_group_by_description(source: str, request: Request, fileType: str, filePath: str):
    """Group data by description and provide summary statistics."""
    try:
        source_config = get_source_config(source)
        source_enum = source_config["name"]
        
        # Load the file data
        df = await load_file_data(source_enum, fileType, filePath)
        
        # Group by description
        description_groups = df.groupby('Description').agg({
            'Amount': ['count', 'sum', 'mean', 'min', 'max']
        }).round(2)
        
        # Flatten column names
        description_groups.columns = ['count', 'total_amount', 'average_amount', 'min_amount', 'max_amount']
        description_groups = description_groups.reset_index()
        
        # Convert to list of dictionaries
        groups = []
        for _, row in description_groups.iterrows():
            groups.append({
                'description': row['Description'],
                'count': int(row['count']),
                'total_amount': float(row['total_amount']),
                'average_amount': float(row['average_amount']),
                'min_amount': float(row['min_amount']),
                'max_amount': float(row['max_amount'])
            })
        
        # Sort by total amount descending
        groups.sort(key=lambda x: x['total_amount'], reverse=True)
        
        return {
            "source": source_enum,
            "file_type": fileType,
            "file_path": filePath,
            "groups": groups,
            "total_groups": len(groups)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        processing_logger.log_system_event(
            f"Error in group by description analytics for {source}: {str(e)}", level="error"
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/{source}/monthly-summary")
@limiter.limit(settings.rate_limit_api)
async def analytics_monthly_summary(source: str, request: Request, fileType: str, filePath: str):
    """Provide monthly summary statistics."""
    try:
        source_config = get_source_config(source)
        source_enum = source_config["name"]
        
        # Load the file data
        df = await load_file_data(source_enum, fileType, filePath)
        
        # Convert date column to datetime
        date_column = get_date_column(source_enum)
        df[date_column] = pd.to_datetime(df[date_column])
        
        # Group by month
        df['month'] = df[date_column].dt.to_period('M')
        monthly_data = df.groupby('month').agg({
            'Amount': ['sum', 'count']
        }).round(2)
        
        monthly_data.columns = ['amount', 'count']
        monthly_data = monthly_data.reset_index()
        
        # Convert to list of dictionaries
        monthly_summary = []
        for _, row in monthly_data.iterrows():
            monthly_summary.append({
                'month': str(row['month']),
                'amount': float(row['amount']),
                'count': int(row['count'])
            })
        
        # Calculate summary statistics
        total_transactions = df['Amount'].count()
        total_amount = df['Amount'].sum()
        average_per_month = total_amount / len(monthly_summary) if monthly_summary else 0
        
        # Find highest and lowest months
        if monthly_summary:
            highest_month = max(monthly_summary, key=lambda x: x['amount'])
            lowest_month = min(monthly_summary, key=lambda x: x['amount'])
        else:
            highest_month = lowest_month = None
        
        return {
            "source": source_enum,
            "file_type": fileType,
            "file_path": filePath,
            "monthly_data": monthly_summary,
            "total_transactions": total_transactions,
            "total_amount": float(total_amount),
            "average_per_month": float(average_per_month),
            "highest_month": highest_month['month'] if highest_month else None,
            "lowest_month": lowest_month['month'] if lowest_month else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        processing_logger.log_system_event(
            f"Error in monthly summary analytics for {source}: {str(e)}", level="error"
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/{source}/amount-analysis")
@limiter.limit(settings.rate_limit_api)
async def analytics_amount_analysis(source: str, request: Request, fileType: str, filePath: str):
    """Provide amount analysis including distribution and statistics."""
    try:
        source_config = get_source_config(source)
        source_enum = source_config["name"]
        
        # Load the file data
        df = await load_file_data(source_enum, fileType, filePath)
        
        # Calculate basic statistics
        amounts = df['Amount']
        mean = amounts.mean()
        median = amounts.median()
        std_dev = amounts.std()
        min_amount = amounts.min()
        max_amount = amounts.max()
        count = len(amounts)
        
        # Create amount distribution (bins)
        bins = pd.cut(amounts, bins=10)
        distribution = bins.value_counts().sort_index()
        
        distribution_data = []
        for bin_name, count in distribution.items():
            distribution_data.append({
                'range': str(bin_name),
                'count': int(count)
            })
        
        # Create amount ranges for pie chart
        ranges = [
            {'range': 'Very Low (< $10)', 'count': int(len(amounts[amounts < 10]))},
            {'range': 'Low ($10 - $50)', 'count': int(len(amounts[(amounts >= 10) & (amounts < 50)]))},
            {'range': 'Medium ($50 - $200)', 'count': int(len(amounts[(amounts >= 50) & (amounts < 200)]))},
            {'range': 'High ($200 - $1000)', 'count': int(len(amounts[(amounts >= 200) & (amounts < 1000)]))},
            {'range': 'Very High (> $1000)', 'count': int(len(amounts[amounts >= 1000]))}
        ]
        
        return {
            "source": source_enum,
            "file_type": fileType,
            "file_path": filePath,
            "mean": float(mean),
            "median": float(median),
            "std_dev": float(std_dev),
            "min": float(min_amount),
            "max": float(max_amount),
            "count": count,
            "distribution": distribution_data,
            "ranges": ranges
        }
        
    except HTTPException:
        raise
    except Exception as e:
        processing_logger.log_system_event(
            f"Error in amount analysis for {source}: {str(e)}", level="error"
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/{source}/trends")
@limiter.limit(settings.rate_limit_api)
async def analytics_trends(source: str, request: Request, fileType: str, filePath: str):
    """Provide trend analysis over time."""
    try:
        source_config = get_source_config(source)
        source_enum = source_config["name"]
        
        # Load the file data
        df = await load_file_data(source_enum, fileType, filePath)
        
        # Convert date column to datetime
        date_column = get_date_column(source_enum)
        df[date_column] = pd.to_datetime(df[date_column])
        
        # Group by month and calculate trends
        df['month'] = df[date_column].dt.to_period('M')
        monthly_trends = df.groupby('month')['Amount'].sum().reset_index()
        
        # Convert to list of dictionaries
        trend_data = []
        for _, row in monthly_trends.iterrows():
            trend_data.append({
                'month': str(row['month']),
                'amount': float(row['Amount'])
            })
        
        # Calculate trend direction and growth rate
        if len(trend_data) >= 2:
            first_amount = trend_data[0]['amount']
            last_amount = trend_data[-1]['amount']
            
            if first_amount != 0:
                growth_rate = ((last_amount - first_amount) / abs(first_amount)) * 100
            else:
                growth_rate = 0
                
            trend_direction = "Increasing" if growth_rate > 0 else "Decreasing" if growth_rate < 0 else "Stable"
        else:
            growth_rate = 0
            trend_direction = "Insufficient Data"
        
        # Find peak and lowest months
        if trend_data:
            peak_month = max(trend_data, key=lambda x: x['amount'])
            lowest_month = min(trend_data, key=lambda x: x['amount'])
        else:
            peak_month = lowest_month = None
        
        return {
            "source": source_enum,
            "file_type": fileType,
            "file_path": filePath,
            "trend_data": trend_data,
            "trend_direction": trend_direction,
            "growth_rate": round(growth_rate, 2),
            "peak_month": peak_month['month'] if peak_month else None,
            "lowest_month": lowest_month['month'] if lowest_month else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        processing_logger.log_system_event(
            f"Error in trends analysis for {source}: {str(e)}", level="error"
        )
        raise HTTPException(status_code=500, detail=str(e))

async def load_file_data(source_enum: str, file_type: str, file_path: str):
    """Load file data for analytics."""
    from pathlib import Path
    import pandas as pd
    
    if file_type == "uploaded":
        file_path_obj = settings.data_path / source_enum / "input" / file_path
    else:  # processed
        file_path_obj = settings.data_path / source_enum / "output" / file_path
    
    if not file_path_obj.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Load CSV data
    df = pd.read_csv(file_path_obj)
    
    # Normalize column names for analytics
    df.columns = df.columns.str.strip()
    
    # Ensure Amount column exists and is numeric
    amount_column = get_amount_column(source_enum)
    if amount_column not in df.columns:
        raise HTTPException(status_code=400, detail=f"Amount column '{amount_column}' not found")
    
    # Convert amount to numeric, handling currency symbols and commas
    df[amount_column] = pd.to_numeric(df[amount_column].astype(str).str.replace('$', '').str.replace(',', ''), errors='coerce')
    
    # Remove rows with NaN amounts
    df = df.dropna(subset=[amount_column])
    
    # Rename columns for consistency
    df = df.rename(columns={
        amount_column: 'Amount',
        get_description_column(source_enum): 'Description'
    })
    
    return df

def get_date_column(source_enum: str) -> str:
    """Get the date column name for a source."""
    date_columns = {
        "BankOfAmerica": "Date",
        "Chase": "Posting Date",
        "RestaurantDepot": "Date",
        "Sysco": "Date"
    }
    return date_columns.get(source_enum, "Date")

def get_amount_column(source_enum: str) -> str:
    """Get the amount column name for a source."""
    amount_columns = {
        "BankOfAmerica": "Amount",
        "Chase": "Amount",
        "RestaurantDepot": "Total",
        "Sysco": "Total"
    }
    return amount_columns.get(source_enum, "Amount")

def get_description_column(source_enum: str) -> str:
    """Get the description column name for a source."""
    description_columns = {
        "BankOfAmerica": "Original Description",
        "Chase": "Description",
        "RestaurantDepot": "Description",
        "Sysco": "Description"
    }
    return description_columns.get(source_enum, "Description") 