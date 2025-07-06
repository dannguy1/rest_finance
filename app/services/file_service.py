"""
File service for handling file system operations.
"""
import shutil
from pathlib import Path
from typing import List, Optional
import aiofiles
from app.config import settings
from app.utils.logging import processing_logger
from app.utils.file_utils import FileUtils
import asyncio
import pandas as pd
import numpy as np
from datetime import datetime


class FileService:
    """Service for file system operations."""
    
    def __init__(self, data_dir: Optional[str] = None):
        """Initialize file service."""
        self.data_dir = Path(data_dir) if data_dir else settings.data_path
        processing_logger.log_system_event("FileService initialized", {"data_dir": str(self.data_dir)})
    
    async def save_uploaded_file(self, source: str, file, filename: str) -> bool:
        """Save uploaded file to appropriate directory."""
        try:
            # Create source directory if it doesn't exist
            source_dir = self.data_dir / source / "input"
            FileUtils.ensure_directory(source_dir)
            
            # Sanitize filename
            safe_filename = FileUtils.sanitize_filename(filename)
            file_path = source_dir / safe_filename
            
            # Save file
            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
            
            processing_logger.log_file_operation("upload", safe_filename, source, True)
            return True
            
        except Exception as e:
            processing_logger.log_file_operation("upload", filename, source, False, str(e))
            return False
    
    async def get_source_files(self, source: str) -> List[dict]:
        """Get list of files for a source with file information."""
        source_dir = self.data_dir / source / "input"
        if not source_dir.exists():
            return []
        
        files = []
        for file_path in source_dir.glob("*.csv"):
            stat = file_path.stat()
            files.append({
                "name": file_path.name,
                "size": stat.st_size,
                "modified": stat.st_mtime
            })
        
        return files
    
    async def delete_file(self, source: str, filename: str) -> bool:
        """Delete a file from source directory."""
        try:
            file_path = self.data_dir / source / "input" / filename
            if file_path.exists():
                file_path.unlink()
                processing_logger.log_file_operation("delete", filename, source, True)
                return True
            return False
            
        except Exception as e:
            processing_logger.log_file_operation("delete", filename, source, False, str(e))
            return False
    
    async def get_output_files(self, source: str, year: Optional[int] = None) -> List[str]:
        """Get list of output files for a source."""
        output_dir = self.data_dir / source / "output"
        if not output_dir.exists():
            return []
        
        if year:
            year_dir = output_dir / str(year)
            if not year_dir.exists():
                return []
            return [f.name for f in year_dir.glob("*.csv")]
        else:
            files = []
            for year_dir in output_dir.iterdir():
                if year_dir.is_dir():
                    files.extend([f"{year_dir.name}/{f.name}" for f in year_dir.glob("*.csv")])
            return files
    
    async def read_output_file(self, source: str, year: int, month: int) -> Optional[str]:
        """Read content of an output file."""
        try:
            file_path = self.data_dir / source / "output" / str(year) / f"{month:02d}_{year}.csv"
            if not file_path.exists():
                return None
            
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
            return content
            
        except Exception as e:
            processing_logger.log_file_operation("read", f"{month:02d}_{year}.csv", source, False, str(e))
            return None
    
    async def backup_file(self, source: str, filename: str) -> Optional[Path]:
        """Create backup of a file."""
        try:
            file_path = self.data_dir / source / "input" / filename
            if not file_path.exists():
                return None
            
            backup_dir = settings.backup_path / source
            backup_path = FileUtils.create_backup(file_path, backup_dir)
            
            if backup_path:
                processing_logger.log_file_operation("backup", filename, source, True)
            else:
                processing_logger.log_file_operation("backup", filename, source, False)
            
            return backup_path
            
        except Exception as e:
            processing_logger.log_file_operation("backup", filename, source, False, str(e))
            return None
    
    async def validate_file(self, source: str, filename: str) -> tuple[bool, List[str]]:
        """Validate a file for processing."""
        try:
            file_path = self.data_dir / source / "input" / filename
            
            if not file_path.exists():
                return False, ["File does not exist"]
            
            errors = []
            
            # Check file type
            if not FileUtils.is_valid_file_type(filename):
                errors.append("Invalid file type")
            
            # Check file size
            if not FileUtils.is_valid_file_size(file_path):
                errors.append(f"File too large (max {settings.max_file_size_mb}MB)")
            
            # Check CSV structure
            from app.utils.csv_utils import CSVUtils
            is_valid, structure_errors = CSVUtils.validate_csv_structure(file_path, source)
            if not is_valid:
                errors.extend(structure_errors)
            
            return len(errors) == 0, errors
            
        except Exception as e:
            return False, [f"Validation error: {str(e)}"]
    
    async def get_file_info(self, source: str, filename: str) -> Optional[dict]:
        """Get information about a file."""
        try:
            file_path = self.data_dir / source / "input" / filename
            
            if not file_path.exists():
                return None
            
            stat = file_path.stat()
            
            return {
                "filename": filename,
                "size_bytes": stat.st_size,
                "size_mb": FileUtils.get_file_size_mb(file_path),
                "created": stat.st_ctime,
                "modified": stat.st_mtime,
                "source": source
            }
            
        except Exception as e:
            processing_logger.log_system_event(f"Error getting file info: {str(e)}", level="error")
            return None
    
    async def cleanup_old_files(self, days_old: int = 30) -> int:
        """Clean up old files from all sources."""
        total_cleaned = 0
        
        for source in ["BankOfAmerica", "Chase", "RestaurantDepot", "Sysco"]:
            source_dir = self.data_dir / source / "input"
            if source_dir.exists():
                cleaned = FileUtils.cleanup_old_files(source_dir, days_old)
                total_cleaned += cleaned
                processing_logger.log_system_event(
                    f"Cleaned {cleaned} old files from {source}"
                )
        
        return total_cleaned

    async def get_processed_files(self, source: str, year: Optional[int] = None, month: Optional[int] = None) -> List[dict]:
        """Get processed files for a source with optional filtering."""
        try:
            output_dir = self.data_dir / source / "output"
            if not output_dir.exists():
                return []
            
            files = []
            
            if year:
                year_dir = output_dir / str(year)
                if not year_dir.exists():
                    return []
                
                if month:
                    # Specific month
                    file_path = year_dir / f"{month:02d}_{year}.csv"
                    if file_path.exists():
                        stat = file_path.stat()
                        files.append({
                            "name": file_path.name,
                            "path": str(file_path.relative_to(self.data_dir)),
                            "year": year,
                            "month": month,
                            "size": stat.st_size,
                            "modified": stat.st_mtime
                        })
                else:
                    # All months in year
                    for file_path in year_dir.glob("*.csv"):
                        stat = file_path.stat()
                        # Extract month from filename (MM_YYYY.csv)
                        month_str = file_path.stem.split('_')[0]
                        month_num = int(month_str)
                        files.append({
                            "name": file_path.name,
                            "path": str(file_path.relative_to(self.data_dir)),
                            "year": year,
                            "month": month_num,
                            "size": stat.st_size,
                            "modified": stat.st_mtime
                        })
            else:
                # All years
                for year_dir in output_dir.iterdir():
                    if year_dir.is_dir() and year_dir.name.isdigit():
                        year_num = int(year_dir.name)
                        for file_path in year_dir.glob("*.csv"):
                            stat = file_path.stat()
                            # Extract month from filename (MM_YYYY.csv)
                            month_str = file_path.stem.split('_')[0]
                            month_num = int(month_str)
                            files.append({
                                "name": file_path.name,
                                "path": str(file_path.relative_to(self.data_dir)),
                                "year": year_num,
                                "month": month_num,
                                "size": stat.st_size,
                                "modified": stat.st_mtime
                            })
            
            # Sort by year, then month
            files.sort(key=lambda x: (x["year"], x["month"]))
            return files
            
        except Exception as e:
            processing_logger.log_system_event(f"Error getting processed files for {source}: {str(e)}", level="error")
            return []

    async def get_available_years(self, source: str) -> List[int]:
        """Get available years for a source."""
        try:
            output_dir = self.data_dir / source / "output"
            if not output_dir.exists():
                return []
            
            years = []
            for year_dir in output_dir.iterdir():
                if year_dir.is_dir() and year_dir.name.isdigit():
                    years.append(int(year_dir.name))
            
            return sorted(years)
            
        except Exception as e:
            processing_logger.log_system_event(f"Error getting available years for {source}: {str(e)}", level="error")
            return []

    async def preview_file(self, source: str, file_path: str) -> Optional[dict]:
        """Preview a processed file (first few rows)."""
        try:
            full_path = self.data_dir / file_path
            if not full_path.exists():
                return None
            
            import csv
            import io
            
            # Read first 10 rows
            rows = []
            headers = []
            
            async with aiofiles.open(full_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                csv_reader = csv.reader(io.StringIO(content))
                
                for i, row in enumerate(csv_reader):
                    if i == 0:
                        headers = row
                    elif i <= 10:  # First 10 data rows
                        rows.append(row)
                    else:
                        break
            
            return {
                "fileName": full_path.name,
                "filePath": file_path,
                "headers": headers,
                "rows": rows,
                "totalRows": len(rows)
            }
            
        except Exception as e:
            processing_logger.log_system_event(f"Error previewing file {file_path}: {str(e)}", level="error")
            return None

    async def get_file_path(self, source: str, file_path: str) -> Optional[Path]:
        """Get the full path to a file."""
        try:
            full_path = self.data_dir / file_path
            if full_path.exists():
                return full_path
            return None
            
        except Exception as e:
            processing_logger.log_system_event(f"Error getting file path for {file_path}: {str(e)}", level="error")
            return None

    async def preview_uploaded_file(self, source: str, filename: str) -> Optional[dict]:
        """Preview an uploaded CSV file."""
        try:
            file_path = self.data_dir / source / "input" / filename
            
            if not file_path.exists():
                return None
            
            # Read the CSV file
            import pandas as pd
            df = pd.read_csv(file_path)
            
            # Get first 50 rows for preview
            preview_df = df.head(50)
            
            # Convert DataFrame to JSON-safe format
            rows = []
            for _, row in preview_df.iterrows():
                row_data = []
                for value in row:
                    # Handle infinite and NaN values
                    if pd.isna(value):
                        row_data.append(None)
                    elif isinstance(value, (int, float)) and (pd.isna(value) or np.isinf(value)):
                        row_data.append(None)
                    else:
                        row_data.append(str(value) if not isinstance(value, (int, float, str, bool)) else value)
                rows.append(row_data)
            
            return {
                "fileName": filename,
                "filePath": str(file_path),
                "totalRows": len(df),
                "previewRows": len(preview_df),
                "headers": df.columns.tolist(),
                "rows": rows,
                "fileSize": file_path.stat().st_size,
                "source": source
            }
            
        except Exception as e:
            processing_logger.log_system_event(
                f"Error previewing uploaded file {filename}: {str(e)}", level="error"
            )
            return None

    async def preview_uploaded_file_full(self, source: str, filename: str) -> Optional[dict]:
        """Preview an uploaded CSV file with all rows."""
        try:
            file_path = self.data_dir / source / "input" / filename
            
            if not file_path.exists():
                return None
            
            # Read the CSV file
            import pandas as pd
            df = pd.read_csv(file_path)
            
            # Convert DataFrame to JSON-safe format
            rows = []
            for _, row in df.iterrows():
                row_data = []
                for value in row:
                    # Handle infinite and NaN values
                    if pd.isna(value):
                        row_data.append(None)
                    elif isinstance(value, (int, float)) and (pd.isna(value) or np.isinf(value)):
                        row_data.append(None)
                    else:
                        row_data.append(str(value) if not isinstance(value, (int, float, str, bool)) else value)
                rows.append(row_data)
            
            return {
                "fileName": filename,
                "filePath": str(file_path),
                "totalRows": len(df),
                "headers": df.columns.tolist(),
                "rows": rows,
                "fileSize": file_path.stat().st_size,
                "source": source
            }
            
        except Exception as e:
            processing_logger.log_system_event(
                f"Error previewing uploaded file {filename}: {str(e)}", level="error"
            )
            return None

    async def preview_file_full(self, source: str, file_path: str) -> Optional[dict]:
        """Preview a processed file with all rows."""
        try:
            full_path = self.data_dir / file_path
            if not full_path.exists():
                return None
            
            # Read the CSV file
            import pandas as pd
            df = pd.read_csv(full_path)
            
            # Convert DataFrame to JSON-safe format
            rows = []
            for _, row in df.iterrows():
                row_data = []
                for value in row:
                    # Handle infinite and NaN values
                    if pd.isna(value):
                        row_data.append(None)
                    elif isinstance(value, (int, float)) and (pd.isna(value) or np.isinf(value)):
                        row_data.append(None)
                    else:
                        row_data.append(str(value) if not isinstance(value, (int, float, str, bool)) else value)
                rows.append(row_data)
            
            return {
                "fileName": full_path.name,
                "filePath": file_path,
                "totalRows": len(df),
                "headers": df.columns.tolist(),
                "rows": rows,
                "fileSize": full_path.stat().st_size,
                "source": source
            }
            
        except Exception as e:
            processing_logger.log_system_event(f"Error previewing file {file_path}: {str(e)}", level="error")
            return None 