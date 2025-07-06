import csv
import pandas as pd
import chardet
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class RobustCSVLoader:
    """
    Robust CSV loader that handles common CSV parsing issues:
    - Inconsistent quoting and embedded commas
    - Trailing/leading empty columns
    - Variable header row location
    - Mixed line endings
    - Non-UTF-8 encodings
    - Malformed rows
    """
    
    def __init__(self, logger_instance=None):
        self.logger = logger_instance or logger
    
    def detect_encoding(self, file_path: Path) -> str:
        """Detect file encoding using chardet."""
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read()
                result = chardet.detect(raw_data)
                encoding = result['encoding'] or 'utf-8'
                confidence = result['confidence'] or 0
                
                self.logger.log_system_event(f"Detected encoding: {encoding} (confidence: {confidence:.2f})", level="info")
                return encoding
        except Exception as e:
            self.logger.log_system_event(f"Failed to detect encoding, using utf-8: {e}", level="warning")
            return 'utf-8'
    
    def find_header_row(self, file_path: Path, encoding: str, 
                       expected_headers: Optional[List[str]] = None) -> Tuple[int, List[str]]:
        """
        Find the header row by scanning for expected column names.
        
        Args:
            file_path: Path to CSV file
            encoding: File encoding
            expected_headers: List of expected header names (case-insensitive)
        
        Returns:
            Tuple of (header_row_index, header_columns)
        """
        with open(file_path, 'r', encoding=encoding, errors='replace') as f:
            reader = csv.reader(f, skipinitialspace=True)
            
            for row_idx, row in enumerate(reader):
                if not row or all(not cell.strip() for cell in row):
                    continue
                
                # Convert to lowercase for comparison
                row_lower = [cell.lower().strip() for cell in row]
                
                # If expected headers provided, check if this row contains them
                if expected_headers:
                    expected_lower = [h.lower() for h in expected_headers]
                    matches = sum(1 for expected in expected_lower 
                               for cell in row_lower if expected in cell)
                    
                    if matches >= len(expected_headers) * 0.7:  # 70% match threshold
                        self.logger.log_system_event(f"Found header row at line {row_idx + 1}", level="info")
                        return row_idx, row
                
                # Fallback: look for common header patterns
                common_headers = ['date', 'amount', 'description', 'type', 'balance', 'posting']
                matches = sum(1 for header in common_headers 
                           for cell in row_lower if header in cell)
                
                if matches >= 2:  # At least 2 common headers
                    self.logger.log_system_event(f"Found header row at line {row_idx + 1} (common pattern match)", level="info")
                    return row_idx, row
        
        raise ValueError("Could not find header row in CSV file")
    
    def normalize_row(self, row: List[str], header_length: int) -> List[str]:
        """
        Normalize a row to match header length by padding or truncating.
        
        Args:
            row: Raw CSV row
            header_length: Expected number of columns
        
        Returns:
            Normalized row with correct number of columns
        """
        # Pad with empty strings if row is too short
        if len(row) < header_length:
            row.extend([''] * (header_length - len(row)))
        # Truncate if row is too long
        elif len(row) > header_length:
            row = row[:header_length]
        
        return row
    
    def load_csv_robust(self, file_path: Path, expected_headers: Optional[List[str]] = None, skip_empty_rows: bool = True, metadata: Optional[dict] = None) -> pd.DataFrame:
        """
        Load a CSV file robustly, using metadata for validation and header detection.
        """
        # Use encoding from metadata if provided
        encoding = metadata.get('encoding') if metadata and 'encoding' in metadata else self.detect_encoding(file_path)
        header_match = metadata.get('header_match') if metadata else None
        min_row_fields = metadata.get('min_row_fields') if metadata else None
        required_columns = metadata.get('required_columns') if metadata else expected_headers
        
        # Read all lines
        with open(file_path, 'r', encoding=encoding) as f:
            lines = f.readlines()
        
        # Find header row using header_match patterns
        header_row_index = -1
        header = None
        if header_match:
            for i, line in enumerate(lines):
                row = [cell.strip().strip('"') for cell in next(csv.reader([line]))]
                for pattern in header_match:
                    if all(col in row for col in pattern):
                        header_row_index = i
                        header = row
                        break
                if header_row_index != -1:
                    break
        if header_row_index == -1:
            # Fallback: use first row as header
            header_row_index = 0
            header = [cell.strip().strip('"') for cell in next(csv.reader([lines[0]]))]
        
        # Validate required columns
        if required_columns and not all(col in header for col in required_columns):
            raise ValueError(f"Could not find header row with required columns in {file_path.name}")
        self.logger.log_system_event(f"Found header row at line {header_row_index+1}: {header}", level="info")
        
        # Parse data rows
        data_rows = []
        malformed_rows = []
        for row_idx, line in enumerate(lines[header_row_index+1:], start=header_row_index+2):
            row = [cell.strip().strip('"') for cell in next(csv.reader([line]))]
            if not row or all(cell == '' for cell in row):
                continue  # skip empty rows
            # Only accept rows with length within [len(header)-1, len(header)+1]
            if not (len(header)-1 <= len(row) <= len(header)+1):
                malformed_rows.append((row_idx, row))
                continue
            # Normalize row
            normalized_row = row[:len(header)] + [''] * (len(header) - len(row))
            # Validate required fields
            if required_columns:
                non_empty_required = sum(1 for i, col in enumerate(header) if col in required_columns and normalized_row[i])
                if min_row_fields:
                    if non_empty_required < min_row_fields:
                        malformed_rows.append((row_idx, normalized_row))
                        continue
                else:
                    if non_empty_required < len(required_columns):
                        malformed_rows.append((row_idx, normalized_row))
                        continue
            data_rows.append(normalized_row)
        # Log malformed rows
        if malformed_rows:
            self.logger.log_system_event(f"Found {len(malformed_rows)} malformed rows", level="warning")
            for row_idx, row in malformed_rows[:5]:
                self.logger.log_system_event(f"  Row {row_idx}: {row}", level="warning")
            if len(malformed_rows) > 5:
                self.logger.log_system_event(f"  ... and {len(malformed_rows) - 5} more", level="warning")
        # Build DataFrame
        if not data_rows:
            raise ValueError("No valid data rows found in file.")
        df = pd.DataFrame(data_rows, columns=header)
        return df

def load_csv_robust(file_path: Path, 
                   expected_headers: Optional[List[str]] = None,
                   skip_empty_rows: bool = True,
                   logger_instance: Optional[logging.Logger] = None,
                   metadata: Optional[dict] = None) -> pd.DataFrame:
    """
    Convenience function to load CSV file with robust parsing.
    
    Args:
        file_path: Path to CSV file
        expected_headers: List of expected header names for validation
        skip_empty_rows: Whether to skip completely empty rows
        logger_instance: Optional logger instance
    
    Returns:
        pandas DataFrame with normalized data
    """
    # Create a default logger if none provided
    if logger_instance is None:
        logger_instance = logging.getLogger(__name__)
    
    loader = RobustCSVLoader(logger_instance)
    return loader.load_csv_robust(file_path, expected_headers, skip_empty_rows, metadata) 