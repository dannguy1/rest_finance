"""
Sample Data API endpoints for managing processed file metadata.
"""
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pathlib import Path
import tempfile
import os

from app.services.sample_data_service import sample_data_service
from app.services.validation_service import ValidationService
from app.utils.logging import processing_logger

router = APIRouter(tags=["sample-data"])


@router.get("/sources")
async def list_processed_sources() -> Dict[str, List[str]]:
    """List all sources that have processed sample data."""
    try:
        sources = sample_data_service.list_processed_sources()
        return {"sources": sources}
    except Exception as e:
        processing_logger.log_system_event(
            f"Error listing processed sources: {str(e)}",
            level="error"
        )
        raise HTTPException(status_code=500, detail="Failed to list processed sources")


@router.get("/sources/{source_id}")
async def get_source_summary(source_id: str) -> Dict[str, Any]:
    """Get summary of processed sample data for a source."""
    try:
        summary = sample_data_service.get_sample_data_summary(source_id)
        if not summary:
            raise HTTPException(status_code=404, detail="No processed data found for this source")
        
        return summary
    except HTTPException:
        raise
    except Exception as e:
        processing_logger.log_system_event(
            f"Error getting source summary for {source_id}: {str(e)}",
            level="error"
        )
        raise HTTPException(status_code=500, detail="Failed to get source summary")


@router.get("/sources/{source_id}/full")
async def get_source_full_data(source_id: str) -> Dict[str, Any]:
    """Get full processed sample data for a source."""
    try:
        processed_data = sample_data_service.get_processed_data(source_id)
        if not processed_data:
            raise HTTPException(status_code=404, detail="No processed data found for this source")
        
        return {
            "source_id": processed_data.source_id,
            "filename": processed_data.filename,
            "original_filename": processed_data.original_filename,
            "processed_at": processed_data.processed_at,
            "file_size_bytes": processed_data.file_size_bytes,
            "total_rows": processed_data.total_rows,
            "columns": processed_data.columns,
            "sample_data": processed_data.sample_data,
            "detected_mappings": processed_data.detected_mappings,
            "file_format": processed_data.file_format,
            "encoding": processed_data.encoding,
            "metadata": processed_data.metadata
        }
    except HTTPException:
        raise
    except Exception as e:
        processing_logger.log_system_event(
            f"Error getting full source data for {source_id}: {str(e)}",
            level="error"
        )
        raise HTTPException(status_code=500, detail="Failed to get source data")


@router.delete("/sources/{source_id}")
async def delete_source_data(source_id: str) -> Dict[str, str]:
    """Delete processed sample data for a source."""
    try:
        success = sample_data_service.delete_processed_data(source_id)
        if not success:
            raise HTTPException(status_code=404, detail="No processed data found for this source")
        
        return {"message": f"Processed data for {source_id} has been deleted"}
    except HTTPException:
        raise
    except Exception as e:
        processing_logger.log_system_event(
            f"Error deleting source data for {source_id}: {str(e)}",
            level="error"
        )
        raise HTTPException(status_code=500, detail="Failed to delete source data")


@router.post("/sources/{source_id}/validate")
async def validate_uploaded_file(
    source_id: str,
    uploaded_file_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Validate uploaded file against saved sample data."""
    try:
        validation_result = sample_data_service.validate_against_saved_data(
            source_id, uploaded_file_data
        )
        return validation_result
    except Exception as e:
        processing_logger.log_system_event(
            f"Error validating file for {source_id}: {str(e)}",
            level="error"
        )
        raise HTTPException(status_code=500, detail="Failed to validate file")


@router.post("/sources/{source_id}/validate-file")
async def validate_file_against_metadata(
    source_id: str,
    file: UploadFile = File(...)
) -> Dict[str, Any]:
    """Validate uploaded file against saved metadata using enhanced validation service."""
    try:
        # Validate file type
        if not file.filename.lower().endswith('.csv'):
            raise HTTPException(status_code=400, detail="Only CSV files are supported")
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as temp_file:
            # Write uploaded file content to temporary file
            content = await file.read()
            temp_file.write(content)
            temp_file_path = Path(temp_file.name)
        
        try:
            # Use enhanced validation service
            validation_service = ValidationService()
            validation_result = validation_service.validate_file_against_metadata(
                temp_file_path, source_id
            )
            
            # Add file information to result
            validation_result['file_info'] = {
                'filename': file.filename,
                'size_bytes': len(content),
                'content_type': file.content_type
            }
            
            return validation_result
            
        finally:
            # Clean up temporary file
            if temp_file_path.exists():
                os.unlink(temp_file_path)
                
    except HTTPException:
        raise
    except Exception as e:
        processing_logger.log_system_event(
            f"Error validating file against metadata for {source_id}: {str(e)}",
            level="error"
        )
        raise HTTPException(status_code=500, detail="Failed to validate file against metadata")


@router.post("/sources/{source_id}/update-config")
async def update_source_config(source_id: str) -> Dict[str, str]:
    """Update the source configuration file with processed metadata."""
    try:
        success = sample_data_service.update_source_config_with_metadata(source_id)
        if not success:
            raise HTTPException(
                status_code=404, 
                detail="No processed data or configuration file found for this source"
            )
        
        return {"message": f"Configuration updated for {source_id}"}
    except HTTPException:
        raise
    except Exception as e:
        processing_logger.log_system_event(
            f"Error updating source config for {source_id}: {str(e)}",
            level="error"
        )
        raise HTTPException(status_code=500, detail="Failed to update configuration")


@router.get("/config/{source_id}")
async def get_source_config_info(source_id: str) -> Dict[str, Any]:
    """Get information about source configuration and processed metadata."""
    try:
        config_path = sample_data_service.get_source_config_path(source_id)
        processed_data = sample_data_service.get_processed_data(source_id)
        
        result = {
            "source_id": source_id,
            "config_exists": config_path is not None,
            "config_path": str(config_path) if config_path else None,
            "processed_data_exists": processed_data is not None
        }
        
        if processed_data:
            result.update({
                "processed_at": processed_data.processed_at,
                "original_filename": processed_data.original_filename,
                "columns_count": len(processed_data.columns),
                "sample_rows": len(processed_data.sample_data)
            })
        
        return result
    except Exception as e:
        processing_logger.log_system_event(
            f"Error getting config info for {source_id}: {str(e)}",
            level="error"
        )
        raise HTTPException(status_code=500, detail="Failed to get configuration info")


@router.get("/sources/{source_id}/metadata")
async def get_source_metadata(source_id: str) -> Dict[str, Any]:
    """Get metadata for a source (columns and basic info for frontend dropdowns)."""
    try:
        processed_data = sample_data_service.get_processed_data(source_id)
        if not processed_data:
            raise HTTPException(status_code=404, detail="No processed data found for this source")
        
        return {
            "source_id": processed_data.source_id,
            "columns": processed_data.columns,
            "detected_mappings": processed_data.detected_mappings,
            "processed_at": processed_data.processed_at,
            "original_filename": processed_data.original_filename
        }
    except HTTPException:
        raise
    except Exception as e:
        processing_logger.log_system_event(
            f"Error getting source metadata for {source_id}: {str(e)}",
            level="error"
        )
        raise HTTPException(status_code=500, detail="Failed to get source metadata") 