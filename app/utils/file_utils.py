"""
File utility functions for Financial Data Processor.
"""
import os
import shutil
from pathlib import Path
from typing import List, Optional
from datetime import datetime
import aiofiles
from app.config import settings
from app.utils.logging import processing_logger


class FileUtils:
    """Utility class for file operations."""
    
    @staticmethod
    def ensure_directory(path: Path) -> None:
        """Ensure directory exists, create if it doesn't."""
        path.mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def get_file_size_mb(file_path: Path) -> float:
        """Get file size in megabytes."""
        return file_path.stat().st_size / (1024 * 1024)
    
    @staticmethod
    def is_valid_file_type(filename: str) -> bool:
        """Check if file type is allowed."""
        file_ext = Path(filename).suffix.lower()
        return file_ext in settings.allowed_file_types
    
    @staticmethod
    def is_valid_file_size(file_path: Path) -> bool:
        """Check if file size is within limits."""
        size_mb = FileUtils.get_file_size_mb(file_path)
        return size_mb <= settings.max_file_size_mb
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for safe storage."""
        import re
        # Remove or replace unsafe characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Limit length
        if len(sanitized) > 255:
            name, ext = sanitized.rsplit('.', 1)
            sanitized = name[:255-len(ext)-1] + '.' + ext
        return sanitized
    
    @staticmethod
    def create_backup(file_path: Path, backup_dir: Path) -> Optional[Path]:
        """Create a backup of a file."""
        try:
            FileUtils.ensure_directory(backup_dir)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
            backup_path = backup_dir / backup_name
            
            shutil.copy2(file_path, backup_path)
            processing_logger.log_file_operation(
                "backup", str(file_path), "system", True
            )
            return backup_path
        except Exception as e:
            processing_logger.log_file_operation(
                "backup", str(file_path), "system", False, str(e)
            )
            return None
    
    @staticmethod
    def cleanup_old_files(directory: Path, days_old: int = 30) -> int:
        """Clean up files older than specified days."""
        try:
            cutoff_time = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
            cleaned_count = 0
            
            for file_path in directory.rglob("*"):
                if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
                    cleaned_count += 1
                    processing_logger.log_file_operation(
                        "cleanup", str(file_path), "system", True
                    )
            
            return cleaned_count
        except Exception as e:
            processing_logger.log_system_event(
                f"Cleanup failed for {directory}: {str(e)}", level="error"
            )
            return 0
    
    @staticmethod
    async def read_file_content(file_path: Path) -> Optional[str]:
        """Read file content asynchronously."""
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
            return content
        except Exception as e:
            processing_logger.log_file_operation(
                "read", str(file_path), "system", False, str(e)
            )
            return None
    
    @staticmethod
    async def write_file_content(file_path: Path, content: str) -> bool:
        """Write content to file asynchronously."""
        try:
            FileUtils.ensure_directory(file_path.parent)
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(content)
            processing_logger.log_file_operation(
                "write", str(file_path), "system", True
            )
            return True
        except Exception as e:
            processing_logger.log_file_operation(
                "write", str(file_path), "system", False, str(e)
            )
            return False
    
    @staticmethod
    def get_source_directories() -> List[Path]:
        """Get list of source directories."""
        return [
            settings.data_path / "BankOfAmerica",
            settings.data_path / "Chase", 
            settings.data_path / "RestaurantDepot",
            settings.data_path / "Sysco"
        ]
    
    @staticmethod
    def get_input_directory(source: str) -> Path:
        """Get input directory for a source."""
        return settings.data_path / source / "input"
    
    @staticmethod
    def get_output_directory(source: str, year: Optional[int] = None) -> Path:
        """Get output directory for a source and optional year."""
        output_dir = settings.data_path / source / "output"
        if year:
            output_dir = output_dir / str(year)
        return output_dir 

def get_data_source_directory() -> Path:
    """Return the main data source directory as a Path object."""
    return settings.data_path 