"""
Validation service for data validation operations.
"""
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import pandas as pd
from app.config import settings
from app.utils.logging import processing_logger
from app.utils.file_utils import FileUtils
from app.utils.csv_utils import CSVUtils
from datetime import datetime


class ValidationService:
    """Service for data validation operations."""
    
    def __init__(self):
        """Initialize validation service."""
        processing_logger.log_system_event("ValidationService initialized")
    
    def validate_csv_file(self, file_path: Path, source: str) -> Dict[str, Any]:
        """Validate CSV file for a specific source."""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'record_count': 0
        }
        
        try:
            # Basic file validation
            if not file_path.exists():
                validation_result['errors'].append("File does not exist")
                validation_result['valid'] = False
                return validation_result
            
            if not FileUtils.is_valid_file_type(file_path.name):
                validation_result['errors'].append("Invalid file type")
                validation_result['valid'] = False
                return validation_result
            
            if not FileUtils.is_valid_file_size(file_path):
                validation_result['errors'].append(f"File too large (max {settings.max_file_size_mb}MB)")
                validation_result['valid'] = False
                return validation_result
            
            # CSV structure validation
            is_valid, structure_errors = CSVUtils.validate_csv_structure(file_path, source)
            if not is_valid:
                validation_result['errors'].extend(structure_errors)
                validation_result['valid'] = False
            
            # Read CSV for further validation
            df = pd.read_csv(file_path)
            validation_result['record_count'] = len(df)
            
            # Source-specific validation
            if source == "BankOfAmerica":
                self._validate_boa_file(df, validation_result)
            elif source == "Chase":
                self._validate_chase_file(df, validation_result, source)
            elif source == "RestaurantDepot":
                self._validate_restaurant_depot_file(df, validation_result)
            elif source == "Sysco":
                self._validate_sysco_file(df, validation_result)
            else:
                validation_result['errors'].append(f"Unknown source type: {source}")
                validation_result['valid'] = False
            
            # General validation
            self._validate_general_csv(df, validation_result)
            
        except Exception as e:
            validation_result['errors'].append(f"File reading error: {str(e)}")
            validation_result['valid'] = False
        
        return validation_result
    
    def _validate_boa_file(self, df: pd.DataFrame, result: Dict[str, Any]):
        """Validate Bank of America file."""
        required_columns = ['Status', 'Date', 'Original Description', 'Amount']
        
        for col in required_columns:
            if col not in df.columns:
                result['errors'].append(f"Missing required column: {col}")
                result['valid'] = False
        
        # Validate date format
        if 'Date' in df.columns:
            invalid_dates = []
            for date_str in df['Date'].dropna():
                if CSVUtils.parse_date(str(date_str)) is None:
                    invalid_dates.append(str(date_str))
            
            if invalid_dates:
                result['warnings'].append(f"Invalid date formats found: {invalid_dates[:5]}")
        
        # Validate amounts
        if 'Amount' in df.columns:
            invalid_amounts = []
            for amount in df['Amount'].dropna():
                if not CSVUtils.is_valid_amount(amount):
                    invalid_amounts.append(str(amount))
            
            if invalid_amounts:
                result['warnings'].append(f"Invalid amounts found: {invalid_amounts[:5]}")
        
        # Check for empty descriptions
        if 'Original Description' in df.columns:
            empty_descriptions = df['Original Description'].isna().sum()
            if empty_descriptions > 0:
                result['warnings'].append(f"Found {empty_descriptions} empty descriptions")
        
        # Check for duplicate transactions
        if len(df) > 0:
            duplicates = df.duplicated().sum()
            if duplicates > 0:
                result['warnings'].append(f"Found {duplicates} duplicate transactions")
        
        # Check data quality
        if len(df) > 0:
            # Check for reasonable date range
            if 'Date' in df.columns:
                try:
                    dates = pd.to_datetime(df['Date'], errors='coerce')
                    valid_dates = dates.dropna()
                    if len(valid_dates) > 0:
                        min_date = valid_dates.min()
                        max_date = valid_dates.max()
                        current_year = datetime.now().year
                        
                        if min_date.year < 2020:
                            result['warnings'].append(f"File contains very old dates (earliest: {min_date.strftime('%Y-%m-%d')})")
                        
                        if max_date.year > current_year:
                            result['warnings'].append(f"File contains future dates (latest: {max_date.strftime('%Y-%m-%d')})")
                except Exception as e:
                    result['warnings'].append(f"Date parsing error: {str(e)}")
            
            # Check for reasonable amount ranges
            if 'Amount' in df.columns:
                try:
                    amounts = df['Amount'].apply(CSVUtils.clean_amount)
                    valid_amounts = amounts[amounts != 0]
                    if len(valid_amounts) > 0:
                        min_amount = valid_amounts.min()
                        max_amount = valid_amounts.max()
                        
                        if abs(min_amount) > 1000000:  # $1M
                            result['warnings'].append(f"File contains very large amounts (min: ${min_amount:,.2f})")
                        
                        if abs(max_amount) > 1000000:  # $1M
                            result['warnings'].append(f"File contains very large amounts (max: ${max_amount:,.2f})")
                except Exception as e:
                    result['warnings'].append(f"Amount parsing error: {str(e)}")
            
            # Check status values
            if 'Status' in df.columns:
                unique_statuses = df['Status'].dropna().unique()
                if len(unique_statuses) > 0:
                    result['info'] = f"Status values found: {', '.join(unique_statuses)}"
    
    def _validate_chase_file(self, df: pd.DataFrame, result: Dict[str, Any], source: str):
        """Validate Chase file."""
        # Chase files have specific column structure:
        # Details (CREDIT/DEBIT), Posting Date, Description, Amount, Type (ACH_CREDIT, ACCT_XFER), Balance, Check or Slip
        # We focus on: Posting Date, Description, Amount
        
        # Required columns for processing
        required_columns = ['Posting Date', 'Description', 'Amount']
        
        # Optional columns that may be present
        optional_columns = ['Details', 'Type', 'Balance', 'Check or Slip']
        
        # Check for required columns
        missing_required = []
        for col in required_columns:
            if col not in df.columns:
                missing_required.append(col)
        
        if missing_required:
            result['errors'].append(f"Missing required columns: {', '.join(missing_required)}")
            result['valid'] = False
        else:
            result['info'] = f"Found all required columns: {', '.join(required_columns)}"
        
        # Check for optional columns
        found_optional = []
        for col in optional_columns:
            if col in df.columns:
                found_optional.append(col)
        
        if found_optional:
            result['info'] = f"Additional columns found: {', '.join(found_optional)}"
        
        # Set the found columns for validation
        found_date_col = 'Posting Date' if 'Posting Date' in df.columns else None
        found_description_col = 'Description' if 'Description' in df.columns else None
        found_amount_col = 'Amount' if 'Amount' in df.columns else None
        
        # Add source information to result for general validation
        result['source'] = source
        
        # Validate date format
        if found_date_col:
            invalid_dates = []
            for date_str in df[found_date_col].dropna():
                if CSVUtils.parse_date(str(date_str)) is None:
                    invalid_dates.append(str(date_str))
            
            if invalid_dates:
                result['warnings'].append(f"Invalid date formats found: {invalid_dates[:5]}")
            
            # For Chase files, also check that we have valid dates
            if source == "Chase" and found_date_col == "Posting Date":
                try:
                    # Try to parse dates to ensure they're valid
                    pd.to_datetime(df[found_date_col], errors='coerce')
                    valid_dates = pd.to_datetime(df[found_date_col], errors='coerce').dropna()
                    if len(valid_dates) > 0:
                        result['info'] = f"Found {len(valid_dates)} valid dates in Posting Date column"
                except Exception as e:
                    result['warnings'].append(f"Date parsing error in Posting Date column: {str(e)}")
        
        # Validate amounts
        if found_amount_col:
            invalid_amounts = []
            for amount in df[found_amount_col].dropna():
                if not CSVUtils.is_valid_amount(amount):
                    invalid_amounts.append(str(amount))
            
            if invalid_amounts:
                result['warnings'].append(f"Invalid amounts found: {invalid_amounts[:5]}")
        
        # Check for empty descriptions
        if found_description_col:
            empty_descriptions = df[found_description_col].isna().sum()
            if empty_descriptions > 0:
                result['warnings'].append(f"Found {empty_descriptions} empty descriptions")
        
        # Check for duplicate transactions
        if len(df) > 0:
            duplicates = df.duplicated().sum()
            if duplicates > 0:
                result['warnings'].append(f"Found {duplicates} duplicate transactions")
        
        # Check data quality
        if len(df) > 0:
            # Check for reasonable date range
            if found_date_col:
                try:
                    dates = pd.to_datetime(df[found_date_col], errors='coerce')
                    valid_dates = dates.dropna()
                    if len(valid_dates) > 0:
                        min_date = valid_dates.min()
                        max_date = valid_dates.max()
                        current_year = datetime.now().year
                        
                        if min_date.year < 2020:
                            result['warnings'].append(f"File contains very old dates (earliest: {min_date.strftime('%Y-%m-%d')})")
                        
                        if max_date.year > current_year:
                            result['warnings'].append(f"File contains future dates (latest: {max_date.strftime('%Y-%m-%d')})")
                except Exception as e:
                    result['warnings'].append(f"Date parsing error: {str(e)}")
            
            # Check for reasonable amount ranges
            if found_amount_col:
                try:
                    amounts = df[found_amount_col].apply(CSVUtils.clean_amount)
                    valid_amounts = amounts[amounts != 0]
                    if len(valid_amounts) > 0:
                        min_amount = valid_amounts.min()
                        max_amount = valid_amounts.max()
                        
                        if abs(min_amount) > 1000000:  # $1M
                            result['warnings'].append(f"File contains very large amounts (min: ${min_amount:,.2f})")
                        
                        if abs(max_amount) > 1000000:  # $1M
                            result['warnings'].append(f"File contains very large amounts (max: ${max_amount:,.2f})")
                except Exception as e:
                    result['warnings'].append(f"Amount parsing error: {str(e)}")
            
            # Check optional columns for Chase files
            optional_columns = ['Balance', 'Check or Slip #', 'Type', 'Details']
            for col in optional_columns:
                if col in df.columns:
                    missing_count = df[col].isna().sum()
                    total_count = len(df)
                    if missing_count > 0:
                        # For optional columns, only warn if ALL values are missing
                        if missing_count == total_count:
                            result['warnings'].append(f"Optional column '{col}' has no data")
                        else:
                            # Log info about optional column usage
                            result['info'] = f"Optional column '{col}' has {total_count - missing_count} populated values out of {total_count} total"
    
    def _validate_restaurant_depot_file(self, df: pd.DataFrame, result: Dict[str, Any]):
        """Validate Restaurant Depot file."""
        # Restaurant Depot files may have varying structures
        # Check for common invoice-related columns
        invoice_indicators = ['Invoice', 'Date', 'Total', 'Amount', 'Item']
        found_indicators = [col for col in df.columns if any(indicator in col for indicator in invoice_indicators)]
        
        if len(found_indicators) < 2:
            result['warnings'].append("File may not be in expected Restaurant Depot format")
    
    def _validate_sysco_file(self, df: pd.DataFrame, result: Dict[str, Any]):
        """Validate Sysco file."""
        # Sysco files may have varying structures
        # Check for common invoice-related columns
        invoice_indicators = ['Invoice', 'Date', 'Total', 'Amount', 'Item']
        found_indicators = [col for col in df.columns if any(indicator in col for indicator in invoice_indicators)]
        
        if len(found_indicators) < 2:
            result['warnings'].append("File may not be in expected Sysco format")
    
    def _validate_general_csv(self, df: pd.DataFrame, result: Dict[str, Any]):
        """General CSV validation."""
        # Check for empty file
        if len(df) == 0:
            result['warnings'].append("File is empty")
        
        # Check for duplicate rows
        if len(df) != len(df.drop_duplicates()):
            result['warnings'].append("File contains duplicate rows")
        
        # Check for missing values in critical columns (but not optional columns)
        # Define optional columns for different sources
        optional_columns = {
            'Chase': ['Balance', 'Check or Slip #', 'Type', 'Details'],
            'BankOfAmerica': ['Status'],
            'RestaurantDepot': [],
            'Sysco': []
        }
        
        # Get the source from the result if available, otherwise assume general validation
        source = result.get('source', 'general')
        source_optional_cols = optional_columns.get(source, [])
        
        for col in df.columns:
            # Skip optional columns for their respective sources
            if col in source_optional_cols:
                continue
                
            missing_count = df[col].isna().sum()
            if missing_count > len(df) * 0.5:  # More than 50% missing
                result['warnings'].append(f"Column '{col}' has many missing values ({missing_count})")
    
    def validate_file_size(self, file_size: int, max_size_mb: Optional[int] = None) -> bool:
        """Validate file size."""
        if max_size_mb is None:
            max_size_mb = settings.max_file_size_mb
        
        max_size_bytes = max_size_mb * 1024 * 1024
        return file_size <= max_size_bytes
    
    def validate_file_extension(self, filename: str) -> bool:
        """Validate file extension."""
        return FileUtils.is_valid_file_type(filename)
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe storage."""
        return FileUtils.sanitize_filename(filename)
    
    def validate_processing_options(self, options: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate processing options."""
        errors = []
        
        if 'date_format' in options:
            date_format = options['date_format']
            if not isinstance(date_format, str):
                errors.append("date_format must be a string")
        
        if 'currency_format' in options:
            currency_format = options['currency_format']
            if not isinstance(currency_format, str):
                errors.append("currency_format must be a string")
        
        if 'group_by_description' in options:
            group_by = options['group_by_description']
            if not isinstance(group_by, bool):
                errors.append("group_by_description must be a boolean")
        
        if 'include_source_file' in options:
            include_source = options['include_source_file']
            if not isinstance(include_source, bool):
                errors.append("include_source_file must be a boolean")
        
        return len(errors) == 0, errors
    
    def analyze_file_structure(self, file_path: Path, source: str) -> Dict[str, Any]:
        """Analyze file structure and provide detailed information."""
        analysis = {
            'file_path': str(file_path),
            'source': source,
            'exists': file_path.exists(),
            'file_size_mb': 0,
            'columns': [],
            'sample_data': [],
            'issues': [],
            'recommendations': []
        }
        
        if not file_path.exists():
            analysis['issues'].append("File does not exist")
            return analysis
        
        try:
            # Get file size
            analysis['file_size_mb'] = FileUtils.get_file_size_mb(file_path)
            
            # Read CSV with different parsing options
            df = None
            parsing_errors = []
            
            # Try different CSV parsing approaches
            try:
                # First try standard parsing
                df = pd.read_csv(file_path)
            except Exception as e1:
                parsing_errors.append(f"Standard parsing failed: {str(e1)}")
                try:
                    # Try with different quote character
                    df = pd.read_csv(file_path, quotechar='"', escapechar='\\')
                except Exception as e2:
                    parsing_errors.append(f"Quote parsing failed: {str(e2)}")
                    try:
                        # Try with different encoding
                        df = pd.read_csv(file_path, encoding='utf-8')
                    except Exception as e3:
                        parsing_errors.append(f"UTF-8 parsing failed: {str(e3)}")
                        try:
                            # Try with different delimiter
                            df = pd.read_csv(file_path, sep=',', engine='python')
                        except Exception as e4:
                            parsing_errors.append(f"Python engine parsing failed: {str(e4)}")
                            # If all parsing attempts fail, return error
                            analysis['issues'].extend(parsing_errors)
                            analysis['issues'].append("Unable to parse CSV file. File may be corrupted or in an unsupported format.")
                            return analysis
            
            if df is None:
                analysis['issues'].append("Failed to read CSV file")
                return analysis
                
            analysis['columns'] = list(df.columns)
            analysis['total_rows'] = len(df)
            
            # Get sample data (first 3 rows to avoid large descriptions)
            if len(df) > 0:
                try:
                    sample_df = df.head(3)
                    # Convert to dict but handle large text fields
                    sample_data = []
                    for _, row in sample_df.iterrows():
                        row_dict = {}
                        for col, val in row.items():
                            if pd.isna(val):
                                row_dict[col] = None
                            else:
                                val_str = str(val)
                                # Truncate very long descriptions
                                if len(val_str) > 100:
                                    row_dict[col] = val_str[:100] + "..."
                                else:
                                    row_dict[col] = val_str
                        sample_data.append(row_dict)
                    analysis['sample_data'] = sample_data
                except Exception as e:
                    analysis['issues'].append(f"Error creating sample data: {str(e)}")
            
            # Check for common issues
            if len(df) == 0:
                analysis['issues'].append("File is empty")
            
            # Check for missing values in key columns
            key_columns = self._get_key_columns(source)
            found_columns = []
            
            # Define optional columns for different sources
            optional_columns = {
                'Chase': ['Balance', 'Check or Slip', 'Type', 'Details'],
                'BankOfAmerica': ['Status'],
                'RestaurantDepot': [],
                'Sysco': []
            }
            source_optional_cols = optional_columns.get(source, [])
            
            for col in key_columns:
                if col in df.columns:
                    found_columns.append(col)
                    try:
                        missing_count = df[col].isna().sum()
                        if missing_count > 0:
                            # For optional columns, only report if ALL values are missing
                            if col in source_optional_cols:
                                if missing_count == len(df):
                                    analysis['issues'].append(f"Optional column '{col}' has no data")
                                else:
                                    # Log info about optional column usage
                                    populated_count = len(df) - missing_count
                                    analysis['info'] = f"Optional column '{col}' has {populated_count} populated values out of {len(df)} total"
                            else:
                                # For required columns, report any missing values
                                analysis['issues'].append(f"Column '{col}' has {missing_count} missing values")
                    except Exception as e:
                        analysis['issues'].append(f"Error checking column '{col}': {str(e)}")
                else:
                    # Only report missing required columns, not optional ones
                    if col not in source_optional_cols:
                        analysis['issues'].append(f"Missing key column: {col}")
            
            # Provide column mapping information
            if found_columns:
                analysis['info'] = f"Found expected columns: {', '.join(found_columns)}"
            
            # Check for data type issues
            if 'Date' in df.columns or 'Posting Date' in df.columns or 'Transaction Date' in df.columns:
                date_col = 'Date' if 'Date' in df.columns else ('Posting Date' if 'Posting Date' in df.columns else 'Transaction Date')
                try:
                    pd.to_datetime(df[date_col], errors='coerce')
                except Exception as e:
                    analysis['issues'].append(f"Date column contains invalid date formats: {str(e)}")
            
            if 'Amount' in df.columns or 'Debit' in df.columns or 'Credit' in df.columns:
                amount_col = 'Amount' if 'Amount' in df.columns else ('Debit' if 'Debit' in df.columns else 'Credit')
                try:
                    df[amount_col].apply(CSVUtils.clean_amount)
                except Exception as e:
                    analysis['issues'].append(f"Amount column contains invalid number formats: {str(e)}")
            
            # Provide recommendations
            if len(analysis['issues']) == 0:
                analysis['recommendations'].append("File appears to be in good format")
            else:
                analysis['recommendations'].append("Review and fix the issues listed above")
            
        except Exception as e:
            analysis['issues'].append(f"Error reading file: {str(e)}")
        
        return analysis
    
    def _get_key_columns(self, source: str) -> List[str]:
        """Get key columns for a specific source."""
        if source == "BankOfAmerica":
            return ['Status', 'Date', 'Original Description', 'Amount']
        elif source == "Chase":
            return ['Posting Date', 'Description', 'Amount', 'Details', 'Type', 'Balance', 'Check or Slip']
        elif source in ["RestaurantDepot", "Sysco"]:
            return ['Date', 'Description', 'Amount', 'Total']
        else:
            return [] 