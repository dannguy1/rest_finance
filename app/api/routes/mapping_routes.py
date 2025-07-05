"""
Source mapping configuration routes for Financial Data Processor.
Allows users to configure how source-specific columns map to normalized processed data.
"""
from typing import List, Dict, Any, Optional
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
import os
import json
import pandas as pd
import numpy as np
from werkzeug.utils import secure_filename

from app.config import settings
from app.utils.logging import processing_logger
from app.config.source_mapping import (
    SourceMappingConfig, 
    ColumnMapping, 
    MappingType, 
    mapping_manager
)
from app.services.mapping_validation_service import mapping_validation_service, MappingValidationService
from app.services.sample_data_service import sample_data_service
from app.models.file_models import SourceType
from app.utils.file_utils import get_data_source_directory

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.get("")
@limiter.limit(settings.rate_limit_api)
async def list_source_mappings(request: Request):
    """List all available source mapping configurations."""
    try:
        mappings = mapping_manager.get_all_mappings()
        return {
            "mappings": {
                source_id: mapping_manager.get_mapping_summary(source_id)
                for source_id in mappings.keys()
            },
            "count": len(mappings)
        }
    except Exception as e:
        processing_logger.log_system_event(
            f"Error listing source mappings: {str(e)}", level="error"
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{source_id}")
@limiter.limit(settings.rate_limit_api)
async def get_source_mapping(source_id: str, request: Request):
    """Get detailed mapping configuration for a specific source."""
    try:
        mapping = mapping_manager.get_mapping(source_id)
        if not mapping:
            raise HTTPException(
                status_code=404,
                detail=f"Source mapping not found for '{source_id}'"
            )
        
        return {
            "mapping": mapping.dict(),
            "summary": mapping_manager.get_mapping_summary(source_id)
        }
    except HTTPException:
        raise
    except Exception as e:
        processing_logger.log_system_event(
            f"Error getting source mapping for {source_id}: {str(e)}", level="error"
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("")
@limiter.limit(settings.rate_limit_api)
async def create_source_mapping(mapping: SourceMappingConfig, request: Request):
    """Create a new source mapping configuration."""
    try:
        # Require sample data for validation
        if not mapping.example_data:
            raise HTTPException(
                status_code=400,
                detail="Sample data is required. Please provide example_data in the mapping configuration."
            )
        
        # Validate the mapping with sample data
        validation_result = mapping_validation_service.validate_mapping_comprehensive(
            mapping, 
            sample_data=mapping.example_data
        )
        
        if not validation_result["valid"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid mapping configuration: {'; '.join(validation_result['errors'])}"
            )
        
        # Check if mapping already exists
        existing = mapping_manager.get_mapping(mapping.source_id)
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"Source mapping already exists for '{mapping.source_id}'"
            )
        
        # Add the mapping
        mapping_manager.add_mapping(mapping)
        
        processing_logger.log_system_event(
            f"Created source mapping for {mapping.source_id}", level="info"
        )
        
        return {
            "message": "Source mapping created successfully",
            "mapping": mapping.dict(),
            "summary": mapping_manager.get_mapping_summary(mapping.source_id)
        }
    except HTTPException:
        raise
    except Exception as e:
        processing_logger.log_system_event(
            f"Error creating source mapping: {str(e)}", level="error"
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{source_id}")
@limiter.limit(settings.rate_limit_api)
async def update_source_mapping(source_id: str, mapping: SourceMappingConfig, request: Request):
    """Update an existing source mapping configuration."""
    try:
        # Require sample data for validation
        if not mapping.example_data:
            raise HTTPException(
                status_code=400,
                detail="Sample data is required. Please provide example_data in the mapping configuration."
            )
        
        # Validate the mapping with sample data
        validation_result = mapping_validation_service.validate_mapping_comprehensive(
            mapping, 
            sample_data=mapping.example_data
        )
        
        if not validation_result["valid"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid mapping configuration: {'; '.join(validation_result['errors'])}"
            )
        
        # Check if mapping exists
        existing = mapping_manager.get_mapping(source_id)
        if not existing:
            raise HTTPException(
                status_code=404,
                detail=f"Source mapping not found for '{source_id}'"
            )
        
        # Ensure source_id matches
        if mapping.source_id.lower() != source_id.lower():
            raise HTTPException(
                status_code=400,
                detail="Source ID in URL must match source_id in mapping configuration"
            )
        
        # Update the mapping
        mapping_manager.add_mapping(mapping)
        
        processing_logger.log_system_event(
            f"Updated source mapping for {source_id}", level="info"
        )
        
        return {
            "message": "Source mapping updated successfully",
            "mapping": mapping.dict(),
            "summary": mapping_manager.get_mapping_summary(source_id)
        }
    except HTTPException:
        raise
    except Exception as e:
        processing_logger.log_system_event(
            f"Error updating source mapping for {source_id}: {str(e)}", level="error"
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{source_id}")
@limiter.limit(settings.rate_limit_api)
async def delete_source_mapping(source_id: str, request: Request):
    """Delete a source mapping configuration."""
    try:
        # Check if mapping exists
        existing = mapping_manager.get_mapping(source_id)
        if not existing:
            raise HTTPException(
                status_code=404,
                detail=f"Source mapping not found for '{source_id}'"
            )
        
        # Remove the mapping
        success = mapping_manager.remove_mapping(source_id)
        if not success:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete source mapping for '{source_id}'"
            )
        
        processing_logger.log_system_event(
            f"Deleted source mapping for {source_id}", level="info"
        )
        
        return {
            "message": "Source mapping deleted successfully",
            "source_id": source_id
        }
    except HTTPException:
        raise
    except Exception as e:
        processing_logger.log_system_event(
            f"Error deleting source mapping for {source_id}: {str(e)}", level="error"
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{source_id}/validate")
@limiter.limit(settings.rate_limit_api)
async def validate_source_mapping(source_id: str, mapping: SourceMappingConfig, request: Request):
    """Validate a source mapping configuration without saving it."""
    try:
        # Require sample data for validation
        if not mapping.example_data:
            raise HTTPException(
                status_code=400,
                detail="Sample data is required for validation. Please provide example_data in the mapping configuration."
            )
        
        # Use enhanced validation service
        validation_result = mapping_validation_service.validate_mapping_comprehensive(
            mapping, 
            sample_data=mapping.example_data
        )
        
        return {
            "valid": validation_result["valid"],
            "errors": validation_result["errors"],
            "warnings": validation_result["warnings"],
            "test_results": validation_result["test_results"],
            "summary": validation_result["summary"],
            "mapping_summary": mapping_manager.get_mapping_summary(mapping.source_id) if validation_result["valid"] else None
        }
    except HTTPException:
        raise
    except Exception as e:
        processing_logger.log_system_event(
            f"Error validating source mapping for {source_id}: {str(e)}", level="error"
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{source_id}/template")
@limiter.limit(settings.rate_limit_api)
async def get_mapping_template(source_id: str, request: Request):
    """Get a template mapping configuration for a new source."""
    try:
        # Check if mapping already exists
        existing = mapping_manager.get_mapping(source_id)
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"Source mapping already exists for '{source_id}'. Use PUT to update."
            )
        
        # Create a template mapping
        template = SourceMappingConfig(
            source_id=source_id,
            display_name=source_id.title().replace("_", " "),
            description=f"Configure mapping for {source_id} data source",
            icon="file",
            date_mapping=ColumnMapping(
                source_column="Date",
                target_field="date",
                mapping_type=MappingType.DATE,
                required=True,
                date_format="MM/DD/YYYY",
                description="Transaction date"
            ),
            description_mapping=ColumnMapping(
                source_column="Description",
                target_field="description",
                mapping_type=MappingType.DESCRIPTION,
                required=True,
                description="Transaction description"
            ),
            amount_mapping=ColumnMapping(
                source_column="Amount",
                target_field="amount",
                mapping_type=MappingType.AMOUNT,
                required=True,
                amount_format="USD",
                description="Transaction amount"
            ),
            optional_mappings=[],
            expected_columns=["Date", "Description", "Amount"],
            required_columns=["Date", "Description", "Amount"],
            example_data=[
                {"Date": "01/15/2024", "Description": "SAMPLE TRANSACTION", "Amount": "100.00"}
            ]
        )
        
        return {
            "template": template.dict(),
            "instructions": [
                "1. Update the display_name and description to match your source",
                "2. Configure the date_mapping to point to your date column",
                "3. Configure the description_mapping to point to your description column", 
                "4. Configure the amount_mapping to point to your amount column",
                "5. Add any optional_mappings for additional columns",
                "6. Update expected_columns and required_columns lists",
                "7. Provide example_data to help users understand the format"
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        processing_logger.log_system_event(
            f"Error creating mapping template for {source_id}: {str(e)}", level="error"
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{source_id}/format")
@limiter.limit(settings.rate_limit_api)
async def get_source_format(source_id: str, request: Request):
    """Get format information for a source (compatibility with existing API)."""
    try:
        mapping = mapping_manager.get_mapping(source_id)
        if not mapping:
            raise HTTPException(
                status_code=404,
                detail=f"Source mapping not found for '{source_id}'"
            )
        
        return {
            "source_id": mapping.source_id,
            "display_name": mapping.display_name,
            "description": mapping.description,
            "required_columns": mapping.required_columns,
            "optional_columns": [opt.source_column for opt in mapping.optional_mappings],
            "date_format": mapping.default_date_format,
            "amount_format": mapping.default_amount_format,
            "example_data": mapping.example_data,
            "mapping_details": {
                "date_column": mapping.date_mapping.source_column,
                "description_column": mapping.description_mapping.source_column,
                "amount_column": mapping.amount_mapping.source_column,
                "optional_columns": [
                    {
                        "source_column": opt.source_column,
                        "target_field": opt.target_field,
                        "description": opt.description
                    }
                    for opt in mapping.optional_mappings
                ]
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        processing_logger.log_system_event(
            f"Error getting source format for {source_id}: {str(e)}", level="error"
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{source_id}/test-file")
@limiter.limit(settings.rate_limit_api)
async def test_mapping_against_file(source_id: str, file_path: str, request: Request):
    """Test a mapping configuration against an actual file."""
    try:
        mapping = mapping_manager.get_mapping(source_id)
        if not mapping:
            raise HTTPException(
                status_code=404,
                detail=f"Source mapping not found for '{source_id}'"
            )
        
        # Validate the file path
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            raise HTTPException(
                status_code=404,
                detail=f"File not found: {file_path}"
            )
        
        # Test the mapping against the file
        validation_result = mapping_validation_service.validate_file_against_mapping(
            file_path_obj, mapping
        )
        
        return {
            "valid": validation_result["valid"],
            "errors": validation_result["errors"],
            "warnings": validation_result["warnings"],
            "test_results": validation_result["test_results"],
            "file_path": str(file_path_obj),
            "file_size": file_path_obj.stat().st_size if file_path_obj.exists() else 0
        }
    except HTTPException:
        raise
    except Exception as e:
        processing_logger.log_system_event(
            f"Error testing mapping against file for {source_id}: {str(e)}", level="error"
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{source_id}/sample-template")
@limiter.limit(settings.rate_limit_api)
async def get_sample_data_template(source_id: str, request: Request):
    """Get a sample data template for testing a mapping configuration."""
    try:
        mapping = mapping_manager.get_mapping(source_id)
        if not mapping:
            raise HTTPException(
                status_code=404,
                detail=f"Source mapping not found for '{source_id}'"
            )
        
        # Generate sample data template
        sample_template = mapping_validation_service.generate_sample_data_template(mapping)
        
        return {
            "source_id": source_id,
            "sample_template": sample_template,
            "instructions": [
                "Use this template to create sample data for testing your mapping",
                "Replace the sample values with realistic data from your source",
                "Include multiple rows to test different scenarios",
                "Upload the sample data to test your mapping configuration"
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        processing_logger.log_system_event(
            f"Error getting sample template for {source_id}: {str(e)}", level="error"
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process-sample-file")
@limiter.limit(settings.rate_limit_api)
async def process_sample_file(request: Request):
    """Process a sample data file to extract columns and generate sample data."""
    try:
        # Get the uploaded file and source_id
        form = await request.form()
        file = form.get("file")
        source_id = form.get("source_id", "temp_upload")
        
        if not file:
            raise HTTPException(
                status_code=400,
                detail="No file uploaded"
            )
        
        # Check file type
        filename = file.filename
        if not filename or not any(filename.lower().endswith(ext) for ext in ['.csv', '.xlsx', '.xls']):
            raise HTTPException(
                status_code=400,
                detail="Unsupported file format. Please upload CSV or Excel files only."
            )
        
        # Read the file content
        content = await file.read()
        
        # Process the file based on its type
        if filename.lower().endswith('.csv'):
            # Process CSV file
            import io
            import pandas as pd
            
            # Try different encodings
            encodings = ['utf-8', 'latin-1', 'cp1252']
            df = None
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(io.BytesIO(content), encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            if df is None:
                raise HTTPException(
                    status_code=400,
                    detail="Could not read CSV file. Please check the file encoding."
                )
        else:
            # Process Excel file
            import io
            import pandas as pd
            
            try:
                df = pd.read_excel(io.BytesIO(content))
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Could not read Excel file: {str(e)}"
                )
        
        # Extract columns
        columns = df.columns.tolist()
        
        # Generate sample data (first few rows) with JSON-safe values
        sample_data = []
        for _, row in df.head(5).iterrows():
            clean_row = {}
            for col, value in row.items():
                # Handle infinite and NaN values
                if pd.isna(value):
                    clean_row[col] = None
                elif isinstance(value, (float, int)) and (np.isinf(value) or pd.isna(value)):
                    clean_row[col] = None
                else:
                    clean_row[col] = value
            sample_data.append(clean_row)
        
        # Detect potential mappings
        detected_mappings = {}
        
        # Look for date columns
        date_keywords = ['date', 'time', 'posted', 'transaction']
        for col in columns:
            if any(keyword in col.lower() for keyword in date_keywords):
                detected_mappings['date_column'] = col
                break
        
        # Look for description columns
        desc_keywords = ['description', 'desc', 'memo', 'note', 'details', 'transaction']
        for col in columns:
            if any(keyword in col.lower() for keyword in desc_keywords):
                detected_mappings['description_column'] = col
                break
        
        # Look for amount columns
        amount_keywords = ['amount', 'sum', 'total', 'debit', 'credit', 'balance']
        for col in columns:
            if any(keyword in col.lower() for keyword in amount_keywords):
                detected_mappings['amount_column'] = col
                break
        
        # Prepare processed data
        processed_data = {
            "columns": columns,
            "sample_data": sample_data,
            "detected_mappings": detected_mappings,
            "total_rows": len(df),
            "message": f"Successfully processed {filename} with {len(columns)} columns and {len(df)} rows"
        }
        
        # Determine file format and encoding
        file_format = 'csv' if filename.lower().endswith('.csv') else 'excel'
        encoding = None
        if file_format == 'csv':
            # Try to detect encoding
            for enc in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    pd.read_csv(io.BytesIO(content), encoding=enc)
                    encoding = enc
                    break
                except UnicodeDecodeError:
                    continue
        
        # Save processed data metadata
        file_size_bytes = len(content)
        
        # Save the processed data
        success = sample_data_service.save_processed_data(
            source_id=source_id,
            processed_data=processed_data,
            original_filename=filename,
            file_size_bytes=file_size_bytes,
            file_format=file_format,
            encoding=encoding
        )
        
        if success:
            # Try to update the source configuration file with metadata
            sample_data_service.update_source_config_with_metadata(source_id)
        
        return processed_data
        
    except HTTPException:
        raise
    except Exception as e:
        processing_logger.log_system_event(
            f"Error processing sample file: {str(e)}", level="error"
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list-sample-files")
@limiter.limit(settings.rate_limit_api)
async def list_sample_files(request: Request):
    """List available sample files in the data source directory."""
    try:
        data_source_dir = get_data_source_directory()
        if not data_source_dir.exists():
            return {
                "files": []
            }
        
        # Find CSV and Excel files
        sample_files = []
        for file_path in data_source_dir.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in ['.csv', '.xlsx', '.xls']:
                # Get relative path from data source directory
                relative_path = file_path.relative_to(data_source_dir)
                sample_files.append({
                    'name': file_path.name,
                    'path': str(relative_path),
                    'size': f"{file_path.stat().st_size / 1024:.1f} KB",
                    'full_path': str(file_path)
                })
        
        # Sort by name
        sample_files.sort(key=lambda x: x['name'])
        
        return {
            "files": sample_files
        }
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Error listing sample files: {str(e)}"
        processing_logger.log_system_event(error_msg, level="error")
        raise HTTPException(status_code=500, detail=error_msg)


@router.post("/process-existing-file")
@limiter.limit(settings.rate_limit_api)
async def process_existing_file(request: Request):
    """Process an existing sample file from the data source directory."""
    try:
        data = await request.json()
        file_path = data.get('file_path')
        
        if not file_path:
            raise HTTPException(
                status_code=400,
                detail="File path is required"
            )
        
        data_source_dir = get_data_source_directory()
        full_file_path = data_source_dir / file_path
        
        if not full_file_path.exists():
            raise HTTPException(
                status_code=404,
                detail="File not found"
            )
        
        if not full_file_path.is_file():
            raise HTTPException(
                status_code=400,
                detail="Path is not a file"
            )
        
        # Validate file extension
        if full_file_path.suffix.lower() not in ['.csv', '.xlsx', '.xls']:
            raise HTTPException(
                status_code=400,
                detail="Unsupported file format"
            )
        
        # Read the file
        try:
            if full_file_path.suffix.lower() == '.csv':
                df = pd.read_csv(full_file_path)
            else:
                df = pd.read_excel(full_file_path)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to read file: {str(e)}"
            )
        
        # Get columns
        columns = df.columns.tolist()
        
        # Generate sample data (first 3 rows) with JSON-safe values
        sample_data = []
        for _, row in df.head(3).iterrows():
            clean_row = {}
            for col, value in row.items():
                # Handle infinite and NaN values
                if pd.isna(value):
                    clean_row[col] = None
                elif isinstance(value, (float, int)) and (np.isinf(value) or pd.isna(value)):
                    clean_row[col] = None
                else:
                    clean_row[col] = value
            sample_data.append(clean_row)
        
        # Detect mappings
        detected_mappings = {}
        
        # Look for date column
        date_columns = [col for col in columns if any(keyword in col.lower() for keyword in ['date', 'time', 'created', 'posted'])]
        if date_columns:
            detected_mappings['date_column'] = date_columns[0]
        
        # Look for description column
        desc_columns = [col for col in columns if any(keyword in col.lower() for keyword in ['description', 'desc', 'memo', 'note', 'details', 'narration'])]
        if desc_columns:
            detected_mappings['description_column'] = desc_columns[0]
        
        # Look for amount column
        amount_columns = [col for col in columns if any(keyword in col.lower() for keyword in ['amount', 'sum', 'total', 'value', 'debit', 'credit', 'balance'])]
        if amount_columns:
            detected_mappings['amount_column'] = amount_columns[0]
        
        # Prepare processed data
        processed_data = {
            "columns": columns,
            "sample_data": sample_data,
            "detected_mappings": detected_mappings,
            "total_rows": len(df),
            "message": f"Successfully processed {file_path} with {len(columns)} columns and {len(df)} rows"
        }
        
        # Determine file format and encoding
        file_format = 'csv' if full_file_path.suffix.lower() == '.csv' else 'excel'
        encoding = None
        if file_format == 'csv':
            # Try to detect encoding
            for enc in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    pd.read_csv(full_file_path, encoding=enc)
                    encoding = enc
                    break
                except UnicodeDecodeError:
                    continue
        
        # Save processed data metadata
        file_size_bytes = full_file_path.stat().st_size
        
        # Save the processed data
        success = sample_data_service.save_processed_data(
            source_id=source_id,
            processed_data=processed_data,
            original_filename=full_file_path.name,
            file_size_bytes=file_size_bytes,
            file_format=file_format,
            encoding=encoding
        )
        
        if success:
            # Try to update the source configuration file with metadata
            sample_data_service.update_source_config_with_metadata(source_id)
        
        return processed_data
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Error processing existing file: {str(e)}"
        processing_logger.log_system_event(error_msg, level="error")
        raise HTTPException(status_code=500, detail=error_msg)


@router.get("/sample-data/{source_id}")
@limiter.limit(settings.rate_limit_api)
async def get_saved_sample_data(source_id: str, request: Request):
    """Get saved sample data for a source."""
    try:
        processed_data = sample_data_service.get_processed_data(source_id)
        
        if not processed_data:
            raise HTTPException(
                status_code=404,
                detail=f"No saved sample data found for source '{source_id}'"
            )
        
        return {
            "source_id": processed_data.source_id,
            "original_filename": processed_data.original_filename,
            "processed_at": processed_data.processed_at,
            "file_size_mb": round(processed_data.file_size_bytes / (1024 * 1024), 2),
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
            f"Error getting saved sample data for {source_id}: {str(e)}", level="error"
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sample-data")
@limiter.limit(settings.rate_limit_api)
async def list_saved_sample_data(request: Request):
    """List all sources with saved sample data."""
    try:
        sources = sample_data_service.list_processed_sources()
        
        summaries = []
        for source_id in sources:
            summary = sample_data_service.get_sample_data_summary(source_id)
            if summary:
                summaries.append(summary)
        
        return {
            "sources": summaries,
            "count": len(summaries)
        }
        
    except Exception as e:
        processing_logger.log_system_event(
            f"Error listing saved sample data: {str(e)}", level="error"
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sample-data/{source_id}")
@limiter.limit(settings.rate_limit_api)
async def delete_saved_sample_data(source_id: str, request: Request):
    """Delete saved sample data for a source."""
    try:
        success = sample_data_service.delete_processed_data(source_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"No saved sample data found for source '{source_id}'"
            )
        
        return {
            "message": f"Saved sample data deleted for source '{source_id}'"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        processing_logger.log_system_event(
            f"Error deleting saved sample data for {source_id}: {str(e)}", level="error"
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sample-data/{source_id}/validate")
@limiter.limit(settings.rate_limit_api)
async def validate_file_against_saved_data(source_id: str, uploaded_file_data: Dict[str, Any], request: Request):
    """Validate uploaded file against saved sample data."""
    try:
        validation_result = sample_data_service.validate_against_saved_data(source_id, uploaded_file_data)
        
        return {
            "source_id": source_id,
            "validation": validation_result
        }
        
    except Exception as e:
        processing_logger.log_system_event(
            f"Error validating file against saved data for {source_id}: {str(e)}", level="error"
        )
        raise HTTPException(status_code=500, detail=str(e))