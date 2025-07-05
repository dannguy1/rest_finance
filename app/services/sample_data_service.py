"""
Sample Data Service for managing processed file metadata.
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from app.config import settings
from app.config.source_mapping import mapping_manager
from app.utils.logging import processing_logger


@dataclass
class ProcessedSampleData:
    """Metadata for processed sample data."""
    source_id: str
    filename: str
    original_filename: str
    processed_at: str
    file_size_bytes: int
    total_rows: int
    columns: List[str]
    sample_data: List[Dict[str, Any]]
    detected_mappings: Dict[str, str]
    file_format: str  # 'csv', 'xlsx', 'xls'
    encoding: Optional[str] = None  # For CSV files
    metadata: Optional[Dict[str, Any]] = None  # Additional metadata


class SampleDataService:
    """Service for managing processed sample data metadata."""
    
    def __init__(self):
        self.metadata_dir = Path(settings.data_dir) / "source_metadata"
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
    
    def save_processed_data(self, source_id: str, processed_data: Dict[str, Any], 
                          original_filename: str, file_size_bytes: int, 
                          file_format: str, encoding: Optional[str] = None) -> bool:
        """Save processed sample data metadata."""
        try:
            # Create source directory
            source_dir = self.metadata_dir / source_id
            source_dir.mkdir(parents=True, exist_ok=True)
            
            # Create metadata object
            metadata = ProcessedSampleData(
                source_id=source_id,
                filename=f"{source_id}_sample_data.json",
                original_filename=original_filename,
                processed_at=datetime.now().isoformat(),
                file_size_bytes=file_size_bytes,
                total_rows=processed_data.get('total_rows', 0),
                columns=processed_data.get('columns', []),
                sample_data=processed_data.get('sample_data', []),
                detected_mappings=processed_data.get('detected_mappings', {}),
                file_format=file_format,
                encoding=encoding,
                metadata={
                    'message': processed_data.get('message', ''),
                    'processing_version': '1.0'
                }
            )
            
            # Save to JSON file
            metadata_file = source_dir / metadata.filename
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(metadata), f, indent=2, ensure_ascii=False)
            
            processing_logger.log_system_event(
                f"Saved processed sample data for {source_id}: {original_filename}",
                level="info",
                metadata={
                    'source_id': source_id,
                    'filename': original_filename,
                    'columns_count': len(metadata.columns),
                    'sample_rows': len(metadata.sample_data)
                }
            )
            
            return True
            
        except Exception as e:
            processing_logger.log_system_event(
                f"Error saving processed sample data for {source_id}: {str(e)}",
                level="error"
            )
            return False
    
    def get_processed_data(self, source_id: str) -> Optional[ProcessedSampleData]:
        """Get processed sample data for a source."""
        try:
            metadata_file = self.metadata_dir / source_id / f"{source_id}_sample_data.json"
            
            if not metadata_file.exists():
                return None
            
            with open(metadata_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return ProcessedSampleData(**data)
            
        except Exception as e:
            processing_logger.log_system_event(
                f"Error loading processed sample data for {source_id}: {str(e)}",
                level="error"
            )
            return None
    
    def list_processed_sources(self) -> List[str]:
        """List all sources that have processed sample data."""
        try:
            sources = []
            for source_dir in self.metadata_dir.iterdir():
                if source_dir.is_dir():
                    metadata_file = source_dir / f"{source_dir.name}_sample_data.json"
                    if metadata_file.exists():
                        sources.append(source_dir.name)
            return sorted(sources)
            
        except Exception as e:
            processing_logger.log_system_event(
                f"Error listing processed sources: {str(e)}",
                level="error"
            )
            return []
    
    def delete_processed_data(self, source_id: str) -> bool:
        """Delete processed sample data for a source."""
        try:
            metadata_file = self.metadata_dir / source_id / f"{source_id}_sample_data.json"
            
            if metadata_file.exists():
                metadata_file.unlink()
                
                # Remove source directory if empty
                source_dir = self.metadata_dir / source_id
                if source_dir.exists() and not any(source_dir.iterdir()):
                    source_dir.rmdir()
                
                processing_logger.log_system_event(
                    f"Deleted processed sample data for {source_id}",
                    level="info"
                )
                return True
            
            return False
            
        except Exception as e:
            processing_logger.log_system_event(
                f"Error deleting processed sample data for {source_id}: {str(e)}",
                level="error"
            )
            return False
    
    def update_processed_data(self, source_id: str, processed_data: Dict[str, Any],
                            original_filename: str, file_size_bytes: int,
                            file_format: str, encoding: Optional[str] = None) -> bool:
        """Update processed sample data (replace existing)."""
        # Delete existing data first
        self.delete_processed_data(source_id)
        
        # Save new data
        return self.save_processed_data(
            source_id, processed_data, original_filename, 
            file_size_bytes, file_format, encoding
        )
    
    def get_sample_data_summary(self, source_id: str) -> Optional[Dict[str, Any]]:
        """Get a summary of processed sample data."""
        processed_data = self.get_processed_data(source_id)
        
        if not processed_data:
            return None
        
        return {
            "source_id": processed_data.source_id,
            "original_filename": processed_data.original_filename,
            "processed_at": processed_data.processed_at,
            "file_size_mb": round(processed_data.file_size_bytes / (1024 * 1024), 2),
            "total_rows": processed_data.total_rows,
            "columns_count": len(processed_data.columns),
            "sample_rows": len(processed_data.sample_data),
            "detected_mappings": processed_data.detected_mappings,
            "file_format": processed_data.file_format,
            "encoding": processed_data.encoding
        }
    
    def validate_against_saved_data(self, source_id: str, uploaded_file_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate uploaded file against saved sample data."""
        saved_data = self.get_processed_data(source_id)
        
        if not saved_data:
            return {
                "valid": False,
                "message": "No saved sample data found for this source",
                "suggestions": []
            }
        
        validation_result = {
            "valid": True,
            "message": "File structure matches saved sample data",
            "warnings": [],
            "suggestions": []
        }
        
        # Check column structure
        uploaded_columns = set(uploaded_file_data.get('columns', []))
        saved_columns = set(saved_data.columns)
        
        missing_columns = saved_columns - uploaded_columns
        new_columns = uploaded_columns - saved_columns
        
        if missing_columns:
            validation_result["valid"] = False
            validation_result["message"] = f"Missing expected columns: {', '.join(missing_columns)}"
            validation_result["suggestions"].append("Check if the file has the correct structure")
        
        if new_columns:
            validation_result["warnings"].append(f"New columns detected: {', '.join(new_columns)}")
            validation_result["suggestions"].append("Consider updating the mapping configuration")
        
        # Check file format
        if uploaded_file_data.get('file_format') != saved_data.file_format:
            validation_result["warnings"].append(
                f"File format changed from {saved_data.file_format} to {uploaded_file_data.get('file_format')}"
            )
        
        return validation_result
    
    def get_source_config_path(self, source_id: str) -> Optional[Path]:
        """Get the path to the source configuration file."""
        try:
            config_dir = Path("config")
            config_file = config_dir / f"{source_id}.json"
            
            if config_file.exists():
                return config_file
            return None
            
        except Exception as e:
            processing_logger.log_system_event(
                f"Error getting config path for {source_id}: {str(e)}",
                level="error"
            )
            return None
    
    def update_source_config_with_metadata(self, source_id: str) -> bool:
        """Update the source configuration file with processed metadata."""
        try:
            processed_data = self.get_processed_data(source_id)
            if not processed_data:
                return False
            
            config_path = self.get_source_config_path(source_id)
            if not config_path:
                return False
            
            # Read existing config
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Update with processed metadata
            config.update({
                "processed_metadata": {
                    "processed_at": processed_data.processed_at,
                    "original_filename": processed_data.original_filename,
                    "file_size_mb": round(processed_data.file_size_bytes / (1024 * 1024), 2),
                    "total_rows": processed_data.total_rows,
                    "columns": processed_data.columns,
                    "detected_mappings": processed_data.detected_mappings,
                    "file_format": processed_data.file_format,
                    "encoding": processed_data.encoding
                }
            })
            
            # Write updated config
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            processing_logger.log_system_event(
                f"Updated source config with metadata for {source_id}",
                level="info"
            )
            
            return True
            
        except Exception as e:
            processing_logger.log_system_event(
                f"Error updating source config for {source_id}: {str(e)}",
                level="error"
            )
            return False


# Global instance
sample_data_service = SampleDataService() 