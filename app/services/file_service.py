"""
File service for handling file system operations.
"""
import shutil
from pathlib import Path
from typing import List, Optional
import aiofiles
import asyncio
import pandas as pd
import numpy as np
from datetime import datetime

from app.config import settings
from app.utils.logging import processing_logger
from app.utils.file_utils import FileUtils
from app.constants import LOCK_FILE_PREFIX, LOCK_FILE_SUFFIX
from app.exceptions import (
    FileOperationError,
    FileNotFoundError as AppFileNotFoundError,
    FileAlreadyExistsError,
    InvalidFileTypeError
)


class FileService:
    """Service for file system operations."""
    
    def __init__(self, data_dir: Optional[str] = None):
        """Initialize file service."""
        self.data_dir = Path(data_dir) if data_dir else settings.data_path
        processing_logger.log_system_event("FileService initialized", {"data_dir": str(self.data_dir)})
    
    async def save_uploaded_file(self, source: str, file, filename: str) -> bool:
        """
        Save uploaded file to appropriate directory with file locking and validation.
        
        Args:
            source: Source identifier
            file: Uploaded file object
            filename: Original filename
            
        Returns:
            True if successful
            
        Raises:
            FileAlreadyExistsError: If file is being processed or exists
            InvalidFileTypeError: If file content doesn't match extension
            FileOperationError: If save operation fails
        """
        lock_file = None
        file_path = None
        
        try:
            # Create source directory if it doesn't exist
            source_dir = self.data_dir / source / "input"
            FileUtils.ensure_directory(source_dir)
            
            # Sanitize filename (prevents path traversal)
            safe_filename = FileUtils.sanitize_filename(filename)
            file_path = source_dir / safe_filename
            
            # Check if file already exists
            if file_path.exists():
                raise FileAlreadyExistsError(
                    f"File already exists: {safe_filename}",
                    {"filename": safe_filename, "source": source}
                )
            
            # Create lock file to prevent concurrent access
            lock_file = file_path.parent / f"{LOCK_FILE_PREFIX}{safe_filename}{LOCK_FILE_SUFFIX}"
            
            # Check if file is being processed
            if lock_file.exists():
                raise FileAlreadyExistsError(
                    f"File is currently being processed: {safe_filename}",
                    {"filename": safe_filename, "source": source, "locked": True}
                )
            
            # Create lock
            async with aiofiles.open(lock_file, 'w') as lock:
                await lock.write(f"Locked by upload at {datetime.now().isoformat()}")
            
            # Save file
            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
            
            # Validate file content matches extension
            file_extension = file_path.suffix
            try:
                await FileUtils.validate_file_content(file_path, file_extension)
            except ValueError as e:
                # Remove invalid file
                file_path.unlink(missing_ok=True)
                raise InvalidFileTypeError(str(e), {"filename": safe_filename, "source": source})
            
            # NOTE: PDF files are NOT automatically processed
            # User must explicitly click "Process" button to extract data
            # This ensures user has control over when extraction happens
            
            processing_logger.log_file_operation("upload", safe_filename, source, True)
            return True
            
        except (FileAlreadyExistsError, InvalidFileTypeError):
            # Re-raise custom exceptions
            raise
        except (IOError, PermissionError) as e:
            # Handle specific I/O errors
            if file_path and file_path.exists():
                file_path.unlink(missing_ok=True)
            processing_logger.log_file_operation("upload", filename, source, False, str(e))
            raise FileOperationError(
                f"Failed to save file: {filename}",
                {"error": str(e), "source": source, "type": type(e).__name__}
            )
        except Exception as e:
            # Unexpected errors - log and re-raise
            if file_path and file_path.exists():
                file_path.unlink(missing_ok=True)
            processing_logger.log_system_event(
                f"Unexpected error in file upload: {str(e)}",
                level="critical",
                details={"filename": filename, "source": source, "error": str(e)}
            )
            raise
        finally:
            # Always clean up lock file
            if lock_file and lock_file.exists():
                try:
                    lock_file.unlink()
                except Exception as e:
                    processing_logger.log_system_event(
                        f"Failed to remove lock file: {str(e)}",
                        level="warning"
                    )
    
    async def get_source_files(self, source: str) -> List[dict]:
        """
        Get list of files for a source with enhanced metadata.
        Detects parent-child relationships for extracted files.
        """
        source_dir = self.data_dir / source / "input"
        if not source_dir.exists():
            return []
        
        files = []
        extracted_files = set()  # Track extracted files
        
        # First pass: collect all files
        all_files = {}
        for file_path in source_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in ['.csv', '.pdf']:
                stat = file_path.stat()
                all_files[file_path.name] = {
                    "name": file_path.name,
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                    "type": file_path.suffix.lower(),
                    "path": str(file_path.relative_to(self.data_dir))
                }
        
        # Second pass: detect extracted files (CSV files with parent PDF)
        for filename, file_info in all_files.items():
            if filename.endswith('.csv'):
                # Check if there's a corresponding PDF
                # Pattern: Jan2025.pdf -> Jan2025_batches.csv
                base_name = filename.rsplit('_', 1)[0] if '_' in filename else filename.replace('.csv', '')
                possible_pdf = f"{base_name}.pdf"
                
                if possible_pdf in all_files:
                    # This CSV was likely extracted from the PDF
                    file_info['is_extracted'] = True
                    file_info['parent_file'] = possible_pdf
                    file_info['status'] = 'extracted'
                    extracted_files.add(filename)
                else:
                    file_info['is_extracted'] = False
                    file_info['status'] = 'pending'
            else:
                # PDF files
                file_info['is_extracted'] = False
                file_info['status'] = 'pending'
        
        # Sort: PDF files first, then their extracted CSVs, then other CSVs
        sorted_files = []
        for filename, file_info in sorted(all_files.items(), key=lambda x: (x[1]['modified'], x[0])):
            if file_info['type'] == '.pdf':
                sorted_files.append(file_info)
                # Add extracted CSV right after its parent PDF
                for csv_name, csv_info in all_files.items():
                    if csv_info.get('parent_file') == filename:
                        sorted_files.append(csv_info)
            elif filename not in extracted_files:
                # Add non-extracted CSV files
                sorted_files.append(file_info)
        
        return sorted_files
    
    async def delete_file(self, source: str, filename: str) -> dict:
        """
        Delete a source input file and remove its entries from all processed output files.

        Args:
            source: Source identifier
            filename: Filename to delete

        Returns:
            Dict with deletion result and cleanup summary:
                {
                    "success": True,
                    "output_files_modified": int,
                    "output_files_deleted": int,
                    "rows_removed": int,
                }

        Raises:
            AppFileNotFoundError: If file doesn't exist
            FileOperationError: If deletion fails
        """
        try:
            file_path = self.data_dir / source / "input" / filename

            if not file_path.exists():
                raise AppFileNotFoundError(
                    f"File not found: {filename}",
                    {"filename": filename, "source": source}
                )

            file_path.unlink()
            processing_logger.log_file_operation("delete", filename, source, True)

            cleanup = await self._remove_entries_from_outputs(source, filename)
            return {"success": True, **cleanup}

        except AppFileNotFoundError:
            raise
        except (IOError, PermissionError) as e:
            processing_logger.log_file_operation("delete", filename, source, False, str(e))
            raise FileOperationError(
                f"Failed to delete file: {filename}",
                {"error": str(e), "source": source, "type": type(e).__name__}
            )
        except Exception as e:
            processing_logger.log_system_event(
                f"Unexpected error deleting file: {str(e)}",
                level="critical",
                details={"filename": filename, "source": source}
            )
            raise

    async def _remove_entries_from_outputs(self, source: str, filename: str) -> dict:
        """
        Remove all rows attributed to `filename` from processed output CSVs.

        Scans every CSV under data/{source}/output/, strips rows where the
        'Source File' column matches `filename`, then either rewrites the file
        (rows remaining) or deletes it (no rows remaining).  Empty year
        directories are also removed.

        Args:
            source: Source identifier (e.g. "BankOfAmerica")
            filename: The deleted input filename to scrub from outputs

        Returns:
            {
                "output_files_modified": int,
                "output_files_deleted": int,
                "rows_removed": int,
            }
        """
        output_dir = self.data_dir / source / "output"
        files_modified = 0
        files_deleted = 0
        rows_removed = 0

        if not output_dir.exists():
            return {
                "output_files_modified": 0,
                "output_files_deleted": 0,
                "rows_removed": 0,
            }

        for csv_path in sorted(output_dir.rglob("*.csv")):
            try:
                df = pd.read_csv(csv_path)
            except Exception as e:
                processing_logger.log_system_event(
                    f"Could not read output file during cleanup: {csv_path}",
                    level="warning",
                    details={"error": str(e)}
                )
                continue

            if "Source File" not in df.columns:
                continue

            before = len(df)
            df = df[df["Source File"] != filename]
            removed = before - len(df)

            if removed == 0:
                continue

            rows_removed += removed

            if df.empty:
                csv_path.unlink()
                files_deleted += 1
                processing_logger.log_file_operation(
                    "delete", csv_path.name, source, True
                )
                # Remove empty year directory
                try:
                    csv_path.parent.rmdir()
                except OSError:
                    pass  # Directory not empty — leave it
            else:
                df.to_csv(csv_path, index=False)
                files_modified += 1
                processing_logger.log_file_operation(
                    "update", csv_path.name, source, True
                )

        if rows_removed:
            processing_logger.log_system_event(
                f"Cleaned up processed outputs after deleting '{filename}'",
                level="info",
                details={
                    "source": source,
                    "rows_removed": rows_removed,
                    "files_modified": files_modified,
                    "files_deleted": files_deleted,
                },
            )

        return {
            "output_files_modified": files_modified,
            "output_files_deleted": files_deleted,
            "rows_removed": rows_removed,
        }
    
    async def get_output_files(self, source: str, year: Optional[int] = None) -> List[str]:
        """Get list of output files for a source."""
        output_dir = self.data_dir / source / "output"
        if not output_dir.exists():
            return []
        
        if year:
            year_dir = output_dir / str(year)
            if not year_dir.exists():
                return []
            # Use case-insensitive file detection for CSV files
            return [f.name for f in year_dir.iterdir() if f.is_file() and f.suffix.lower() == '.csv']
        else:
            files = []
            for year_dir in output_dir.iterdir():
                if year_dir.is_dir():
                    files.extend([f"{year_dir.name}/{f.name}" for f in year_dir.iterdir() 
                                if f.is_file() and f.suffix.lower() == '.csv'])
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
            
            # Handle PDF files differently
            if filename.lower().endswith('.pdf'):
                from app.services.pdf_service import pdf_service
                validation = pdf_service.validate_pdf_content(file_path)
                if not validation["is_valid"]:
                    errors.append(f"Invalid PDF content: {validation.get('error', 'Unknown error')}")
            else:
                # Check CSV structure for CSV files
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
                    for file_path in year_dir.iterdir():
                        if file_path.is_file() and file_path.suffix.lower() == '.csv':
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
                        for file_path in year_dir.iterdir():
                            if file_path.is_file() and file_path.suffix.lower() == '.csv':
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