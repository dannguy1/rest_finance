"""
Validation service for data validation operations.
"""
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import pandas as pd
import numpy as np
from app.config import settings
from app.utils.logging import processing_logger
from app.utils.file_utils import FileUtils
from app.utils.csv_utils import CSVUtils
from app.services.sample_data_service import SampleDataService
from datetime import datetime
from app.config.source_mapping import mapping_manager
import csv
import os


class ValidationService:
    """Service for data validation operations."""
    
    def __init__(self):
        """Initialize validation service."""
        self.sample_data_service = SampleDataService()
        processing_logger.log_system_event("ValidationService initialized")
    
    def validate_csv_file(self, file_path: Path, source: str) -> Dict[str, Any]:
        """Validate CSV file for a specific source with enhanced issue detection and fixes."""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'fixes_applied': [],
            'issues_detected': [],
            'record_count': 0,
            'can_proceed': True,
            'user_action_required': False,
            'fix_suggestions': []
        }
        
        try:
            # Basic file validation
            if not file_path.exists():
                validation_result['errors'].append("File does not exist")
                validation_result['valid'] = False
                validation_result['can_proceed'] = False
                return validation_result
            
            if not FileUtils.is_valid_file_type(file_path.name):
                validation_result['errors'].append("Invalid file type")
                validation_result['valid'] = False
                validation_result['can_proceed'] = False
                return validation_result
            
            if not FileUtils.is_valid_file_size(file_path):
                validation_result['errors'].append(f"File too large (max {settings.max_file_size_mb}MB)")
                validation_result['valid'] = False
                validation_result['can_proceed'] = False
                return validation_result
            
            # Check for and fix CSV formatting issues
            original_file_path = file_path
            fixed_file_path = self._fix_csv_formatting(file_path)
            if fixed_file_path != original_file_path:
                validation_result['fixes_applied'].append("CSV formatting issues (embedded linefeeds) detected and fixed")
                validation_result['warnings'].append("CSV formatting issues were automatically fixed")
                file_path = fixed_file_path
            
            # Detect source-specific issues
            source_issues = []
            try:
                processing_logger.log_system_event(
                    f"Starting source-specific issue detection for source: {source}", level="info"
                )
                source_issues = self._detect_source_specific_issues(file_path, source)
                processing_logger.log_system_event(
                    f"Detected {len(source_issues)} source-specific issues for {source}", level="info"
                )
                validation_result['issues_detected'].extend(source_issues)
            except Exception as e:
                # If source-specific detection fails, add a fixable issue
                generic_issue = {
                    'type': 'csv_formatting',
                    'message': f'CSV formatting issue: {str(e)}',
                    'fixable': True,
                    'suggestion': 'Fix CSV formatting issues automatically'
                }
                validation_result['issues_detected'].append(generic_issue)
                source_issues.append(generic_issue)
            
            # Check if issues are fixable
            fixable_issues = [issue for issue in source_issues if issue.get('fixable', False)]
            unfixable_issues = [issue for issue in source_issues if not issue.get('fixable', False)]
            
            # Set user action required if there are any issues that need user permission
            if fixable_issues:
                validation_result['user_action_required'] = True
                validation_result['can_proceed'] = False
                # Don't apply fixes automatically - let user decide
                for issue in fixable_issues:
                    validation_result['warnings'].append(f"Fixable issue detected: {issue['message']}")
                    validation_result['fix_suggestions'].append(issue.get('suggestion', ''))
            
            if unfixable_issues:
                validation_result['user_action_required'] = True
                validation_result['can_proceed'] = False
                for issue in unfixable_issues:
                    validation_result['errors'].append(issue['message'])
                    validation_result['fix_suggestions'].append(issue.get('suggestion', ''))
            
            # CSV structure validation
            is_valid, structure_errors = CSVUtils.validate_csv_structure(file_path, source)
            if not is_valid:
                validation_result['errors'].extend(structure_errors)
                validation_result['valid'] = False
                validation_result['can_proceed'] = False
            
            # Read CSV for further validation
            try:
                # Use more robust CSV reading to handle mixed data types
                df = pd.read_csv(file_path, dtype=str, na_filter=False)
                validation_result['record_count'] = len(df)
            except Exception as e:
                validation_result['errors'].append(f"CSV parsing error: {str(e)}")
                validation_result['valid'] = False
                # Check if any fixable issues were detected earlier
                has_fixable_issue = any(issue.get('fixable', False) for issue in validation_result.get('issues_detected', []))
                validation_result['can_proceed'] = not has_fixable_issue
                # Only return early if there are no fixable issues
                if not has_fixable_issue:
                    validation_result = self._add_backward_compatibility(validation_result, source)
                    return validation_result
                # If there are fixable issues, allow the frontend to prompt for fix
                # Do not return early; let the rest of the validation flow continue (it will likely skip due to missing df)
                df = None

            # Source-specific validation
            if df is not None:
                if source == "BankOfAmerica":
                    self._validate_boa_file(df, validation_result)
                elif source == "Chase":
                    self._validate_chase_file(df, validation_result, source)
                elif source == "RestaurantDepot":
                    self._validate_restaurant_depot_file(df, validation_result)
                elif source == "Sysco":
                    self._validate_sysco_file(df, validation_result)
                else:
                    # Try to map lowercase source to proper case
                    source_mapping = {
                        "chase": "Chase",
                        "bankofamerica": "BankOfAmerica", 
                        "restaurantdepot": "RestaurantDepot",
                        "sysco": "Sysco"
                    }
                    
                    mapped_source = source_mapping.get(source.lower(), source)
                    if mapped_source != source:
                        # Retry with mapped source
                        if mapped_source == "Chase":
                            self._validate_chase_file(df, validation_result, mapped_source)
                        elif mapped_source == "BankOfAmerica":
                            self._validate_boa_file(df, validation_result)
                        elif mapped_source == "RestaurantDepot":
                            self._validate_restaurant_depot_file(df, validation_result)
                        elif mapped_source == "Sysco":
                            self._validate_sysco_file(df, validation_result)
                        else:
                            validation_result['errors'].append(f"Unknown source type: {source}")
                            validation_result['valid'] = False
                            validation_result['can_proceed'] = False
                    else:
                        validation_result['errors'].append(f"Unknown source type: {source}")
                        validation_result['valid'] = False
                        validation_result['can_proceed'] = False
                # General validation
                self._validate_general_csv(df, validation_result)
            
        except Exception as e:
            validation_result['errors'].append(f"File reading error: {str(e)}")
            validation_result['valid'] = False
            validation_result['can_proceed'] = False
        
        # Add backward compatibility for frontend
        validation_result = self._add_backward_compatibility(validation_result, source)
        
        # Debug logging for validation result
        processing_logger.log_system_event(
            f"Final validation result for {source}: issues_detected={len(validation_result.get('issues_detected', []))}, "
            f"user_action_required={validation_result.get('user_action_required', False)}, "
            f"can_proceed={validation_result.get('can_proceed', True)}", 
            level="info"
        )
        
        return validation_result
    
    def validate_file_against_metadata(self, file_path: Path, source_id: str) -> Dict[str, Any]:
        """Validate uploaded file against saved sample data metadata."""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'record_count': 0,
            'metadata_validation': {
                'has_saved_metadata': False,
                'column_match_score': 0.0,
                'structure_compatibility': True,
                'suggested_mappings': {}
            }
        }
        
        try:
            # Basic file validation first
            if not file_path.exists():
                validation_result['errors'].append("File does not exist")
                validation_result['valid'] = False
                return validation_result
            
            if not FileUtils.is_valid_file_type(file_path.name):
                validation_result['errors'].append("Invalid file type")
                validation_result['valid'] = False
                return validation_result
            
            # Get saved metadata for this source
            saved_metadata = self.sample_data_service.get_processed_data(source_id)
            
            if not saved_metadata:
                validation_result['warnings'].append("No saved metadata found for this source")
                validation_result['metadata_validation']['has_saved_metadata'] = False
                # Fall back to basic validation
                return self.validate_csv_file(file_path, source_id)
            
            validation_result['metadata_validation']['has_saved_metadata'] = True
            
            # Read the uploaded file
            df = pd.read_csv(file_path, dtype=str, na_filter=False)
            validation_result['record_count'] = len(df)
            
            # Validate against saved metadata
            metadata_validation = self._validate_against_metadata(
                df, saved_metadata, source_id
            )
            validation_result['metadata_validation'].update(metadata_validation)
            
            # If structure is incompatible, add errors
            if not metadata_validation['structure_compatibility']:
                validation_result['errors'].append(
                    "File structure is incompatible with saved metadata"
                )
                validation_result['valid'] = False
            
            # If column match score is too low, add warnings
            if metadata_validation['column_match_score'] < 0.5:
                validation_result['warnings'].append(
                    f"Low column match score ({metadata_validation['column_match_score']:.2f}). "
                    "File may have different structure than expected."
                )
            
            # Additional validation based on saved metadata
            self._validate_data_quality_against_metadata(df, saved_metadata, validation_result)
            
        except Exception as e:
            validation_result['errors'].append(f"Metadata validation error: {str(e)}")
            validation_result['valid'] = False
        
        return validation_result
    
    def _validate_against_metadata(self, df: pd.DataFrame, saved_metadata, source_id: str) -> Dict[str, Any]:
        """Validate DataFrame against saved metadata."""
        result = {
            'column_match_score': 0.0,
            'structure_compatibility': True,
            'suggested_mappings': {},
            'missing_columns': [],
            'extra_columns': [],
            'column_analysis': {}
        }
        
        # Get expected columns from saved metadata
        expected_columns = saved_metadata.columns
        actual_columns = list(df.columns)
        
        # Calculate column match score
        matching_columns = set(expected_columns) & set(actual_columns)
        result['column_match_score'] = len(matching_columns) / len(expected_columns) if expected_columns else 0.0
        
        # Identify missing and extra columns
        result['missing_columns'] = list(set(expected_columns) - set(actual_columns))
        result['extra_columns'] = list(set(actual_columns) - set(expected_columns))
        
        # Analyze each column
        for col in actual_columns:
            result['column_analysis'][col] = {
                'expected': col in expected_columns,
                'data_type': str(df[col].dtype),
                'null_count': df[col].isnull().sum(),
                'unique_count': df[col].nunique(),
                'sample_values': df[col].dropna().head(3).tolist()
            }
        
        # Check structure compatibility
        if result['column_match_score'] < 0.3:  # Less than 30% match
            result['structure_compatibility'] = False
        
        # Generate suggested mappings based on detected mappings from saved metadata
        if hasattr(saved_metadata, 'detected_mappings'):
            result['suggested_mappings'] = saved_metadata.detected_mappings
        
        return result
    
    def _validate_data_quality_against_metadata(self, df: pd.DataFrame, saved_metadata, validation_result: Dict[str, Any]):
        """Validate data quality against saved metadata."""
        try:
            # Check if we have sample data to compare against
            if hasattr(saved_metadata, 'sample_data') and saved_metadata.sample_data:
                sample_data = saved_metadata.sample_data
                
                # Compare data patterns
                for sample_row in sample_data[:3]:  # Check first 3 sample rows
                    for col, expected_value in sample_row.items():
                        if col in df.columns:
                            # Check if the column contains similar data types
                            actual_values = df[col].dropna().head(10)
                            if len(actual_values) > 0:
                                # Basic type checking
                                expected_type = type(expected_value)
                                actual_types = [type(val) for val in actual_values]
                                
                                if expected_type in actual_types:
                                    validation_result['metadata_validation']['data_quality'] = 'good'
                                else:
                                    validation_result['warnings'].append(
                                        f"Column '{col}' has different data types than expected"
                                    )
            
            # Check for reasonable data ranges based on sample data
            if hasattr(saved_metadata, 'sample_data') and saved_metadata.sample_data:
                self._check_data_ranges_against_sample(df, saved_metadata.sample_data, validation_result)
                
        except Exception as e:
            validation_result['warnings'].append(f"Data quality validation error: {str(e)}")
    
    def _check_data_ranges_against_sample(self, df: pd.DataFrame, sample_data: List[Dict], validation_result: Dict[str, Any]):
        """Check if data ranges are reasonable compared to sample data."""
        try:
            for sample_row in sample_data[:5]:  # Check first 5 sample rows
                for col, sample_value in sample_row.items():
                    if col in df.columns and sample_value is not None:
                        # Check numeric columns
                        if isinstance(sample_value, (int, float)):
                            actual_values = pd.to_numeric(df[col], errors='coerce').dropna()
                            if len(actual_values) > 0:
                                sample_val = float(sample_value)
                                actual_min = actual_values.min()
                                actual_max = actual_values.max()
                                
                                # Check if values are in reasonable range (within 10x of sample)
                                if abs(actual_min) > abs(sample_val) * 10 or abs(actual_max) > abs(sample_val) * 10:
                                    validation_result['warnings'].append(
                                        f"Column '{col}' contains values outside expected range "
                                        f"(sample: {sample_val}, actual: {actual_min} to {actual_max})"
                                    )
                        
                        # Check date columns
                        elif isinstance(sample_value, str) and self._looks_like_date(sample_value):
                            actual_dates = pd.to_datetime(df[col], errors='coerce').dropna()
                            if len(actual_dates) > 0:
                                sample_date = pd.to_datetime(sample_value, errors='coerce')
                                if pd.notna(sample_date):
                                    actual_min = actual_dates.min()
                                    actual_max = actual_dates.max()
                                    
                                    # Check if dates are within reasonable range (within 5 years)
                                    if abs((actual_min - sample_date).days) > 1825 or abs((actual_max - sample_date).days) > 1825:
                                        validation_result['warnings'].append(
                                            f"Column '{col}' contains dates outside expected range "
                                            f"(sample: {sample_date.strftime('%Y-%m-%d')}, "
                                            f"actual: {actual_min.strftime('%Y-%m-%d')} to {actual_max.strftime('%Y-%m-%d')})"
                                        )
                                        
        except Exception as e:
            validation_result['warnings'].append(f"Data range validation error: {str(e)}")
    
    def _looks_like_date(self, value: str) -> bool:
        """Check if a string value looks like a date."""
        try:
            pd.to_datetime(value)
            return True
        except:
            return False
    
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
        
        # Enhanced validation: Check for column misalignment issues
        if found_description_col and len(df) > 0:
            sample_desc = df[found_description_col].iloc[0]
            if isinstance(sample_desc, str) and len(sample_desc) > 200:
                # This indicates complex transaction data instead of simple descriptions
                result['issues_detected'].append({
                    'type': 'column_misalignment',
                    'message': 'The Description column contains complex transaction data instead of simple descriptions',
                    'fixable': False,
                    'suggestion': 'Re-export the file from Chase using the standard CSV export option. The current export format is not compatible with our parser.',
                    'details': f'Sample description length: {len(sample_desc)} characters'
                })
                result['user_action_required'] = True
                result['can_proceed'] = False
                result['fix_suggestions'].append('Re-export from Chase using standard CSV format')
        
        # Validate date format
        if found_date_col:
            invalid_dates = []
            for date_val in df[found_date_col].dropna():
                # Handle different data types properly
                if pd.isna(date_val):
                    continue
                try:
                    date_str = str(date_val)
                    if CSVUtils.parse_date(date_str) is None:
                        invalid_dates.append(date_str)
                except Exception as e:
                    # If we can't convert to string, it's likely a data type issue
                    invalid_dates.append(f"Invalid data type: {type(date_val).__name__}")
            
            if invalid_dates:
                result['warnings'].append(f"Invalid date formats found: {invalid_dates[:5]}")
        
        # Validate amounts
        if found_amount_col:
            invalid_amounts = []
            for amount_val in df[found_amount_col].dropna():
                # Handle different data types properly
                if pd.isna(amount_val):
                    continue
                try:
                    if not CSVUtils.is_valid_amount(amount_val):
                        invalid_amounts.append(str(amount_val))
                except Exception as e:
                    # If we can't validate the amount, it's likely a data type issue
                    invalid_amounts.append(f"Invalid data type: {type(amount_val).__name__}")
            
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
            if found_date_col and found_date_col in df.columns:
                try:
                    # Handle case where the column might contain complex data
                    date_series = df[found_date_col]
                    if date_series.dtype == 'object':
                        # Try to extract dates from complex strings
                        sample_value = str(date_series.iloc[0]) if len(date_series) > 0 else ""
                        if len(sample_value) > 100:  # Complex data, skip date validation
                            result['warnings'].append(f"Date column '{found_date_col}' contains complex data, skipping date validation")
                        else:
                            dates = pd.to_datetime(date_series, errors='coerce')
                            valid_dates = dates.dropna()
                            if len(valid_dates) > 0:
                                min_date = valid_dates.min()
                                max_date = valid_dates.max()
                                current_year = datetime.now().year
                                
                                if min_date.year < 2020:
                                    result['warnings'].append(f"File contains very old dates (earliest: {min_date.strftime('%Y-%m-%d')})")
                                
                                if max_date.year > current_year:
                                    result['warnings'].append(f"File contains future dates (latest: {max_date.strftime('%Y-%m-%d')})")
                    else:
                        # Numeric date column, try standard parsing
                        dates = pd.to_datetime(date_series, errors='coerce')
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
            if found_amount_col and found_amount_col in df.columns:
                try:
                    amount_series = df[found_amount_col]
                    if amount_series.dtype == 'object':
                        # Handle complex string data
                        sample_value = str(amount_series.iloc[0]) if len(amount_series) > 0 else ""
                        if len(sample_value) > 100:  # Complex data, skip amount validation
                            result['warnings'].append(f"Amount column '{found_amount_col}' contains complex data, skipping amount validation")
                        else:
                            amounts = amount_series.apply(CSVUtils.clean_amount)
                            valid_amounts = amounts[amounts != 0]
                            if len(valid_amounts) > 0:
                                min_amount = valid_amounts.min()
                                max_amount = valid_amounts.max()
                                
                                if abs(min_amount) > 1000000:  # $1M
                                    result['warnings'].append(f"File contains very large amounts (min: ${min_amount:,.2f})")
                                
                                if abs(max_amount) > 1000000:  # $1M
                                    result['warnings'].append(f"File contains very large amounts (max: ${max_amount:,.2f})")
                    else:
                        # Numeric amount column
                        amounts = amount_series.apply(CSVUtils.clean_amount)
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
            
            # Check type values if present
            if 'Type' in df.columns:
                unique_types = df['Type'].dropna().unique()
                if len(unique_types) > 0:
                    result['info'] = f"Type values found: {', '.join(unique_types)}"
    
    def _validate_restaurant_depot_file(self, df: pd.DataFrame, result: Dict[str, Any]):
        """Validate Restaurant Depot file."""
        # Restaurant Depot files have specific structure
        # Focus on basic validation for now
        if len(df.columns) < 3:
            result['errors'].append("File has too few columns for Restaurant Depot format")
            result['valid'] = False
        
        # Check for reasonable data
        if len(df) > 0:
            result['info'] = f"Found {len(df)} rows with {len(df.columns)} columns"
    
    def _validate_sysco_file(self, df: pd.DataFrame, result: Dict[str, Any]):
        """Validate Sysco file."""
        # Sysco files have specific structure
        # Focus on basic validation for now
        if len(df.columns) < 3:
            result['errors'].append("File has too few columns for Sysco format")
            result['valid'] = False
        
        # Check for reasonable data
        if len(df) > 0:
            result['info'] = f"Found {len(df)} rows with {len(df.columns)} columns"
    
    def _validate_general_csv(self, df: pd.DataFrame, result: Dict[str, Any]):
        """Validate general CSV structure and quality."""
        # Check for empty file
        if len(df) == 0:
            result['errors'].append("File is empty")
            result['valid'] = False
            return
        
        # Check for too many columns (potential parsing issues)
        if len(df.columns) > 50:
            result['warnings'].append(f"File has many columns ({len(df.columns)}), may have parsing issues")
        
        # Check for completely empty columns
        empty_columns = []
        for col in df.columns:
            if df[col].isna().all():
                empty_columns.append(col)
        
        if empty_columns:
            result['warnings'].append(f"Found empty columns: {', '.join(empty_columns)}")
        
        # Check for duplicate rows
        duplicates = df.duplicated().sum()
        if duplicates > 0:
            result['warnings'].append(f"Found {duplicates} duplicate rows")
        
        # Check for reasonable row count
        if len(df) > 100000:  # 100K rows
            result['warnings'].append(f"Large file with {len(df):,} rows, processing may take time")
        
        # Check for mixed data types in columns
        for col in df.columns:
            if df[col].dtype == 'object':  # String/object column
                # Check if it might be numeric
                numeric_count = pd.to_numeric(df[col], errors='coerce').notna().sum()
                if numeric_count > 0 and numeric_count < len(df):
                    result['warnings'].append(f"Column '{col}' contains mixed data types")
    
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
        
        # Validate include_source_file option
        if 'include_source_file' in options:
            include_source_file = options['include_source_file']
            if not isinstance(include_source_file, bool):
                errors.append("include_source_file must be a boolean")
        
        # Validate date_format option
        if 'date_format' in options:
            date_format = options['date_format']
            if not isinstance(date_format, str):
                errors.append("date_format must be a string")
            # Add more specific date format validation if needed
        
        # Validate amount_format option
        if 'amount_format' in options:
            amount_format = options['amount_format']
            if not isinstance(amount_format, str):
                errors.append("amount_format must be a string")
            elif amount_format not in ['USD', 'EUR', 'GBP']:
                errors.append("amount_format must be 'USD', 'EUR', or 'GBP'")
        
        return len(errors) == 0, errors
    
    def analyze_file_structure(self, file_path: Path, source: str) -> Dict[str, Any]:
        """Analyze file structure for mapping suggestions."""
        analysis = {
            'source': source,
            'filename': file_path.name,
            'file_size_bytes': file_path.stat().st_size,
            'columns': [],
            'sample_data': [],
            'detected_mappings': {},
            'suggestions': []
        }
        
        try:
            # Read CSV file with robust parsing
            df = pd.read_csv(file_path, dtype=str, na_filter=False)
            analysis['columns'] = list(df.columns)
            
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
            analysis['sample_data'] = sample_records
            
            # Detect potential mappings based on column names
            analysis['detected_mappings'] = self._detect_column_mappings(df.columns, source)
            
            # Generate suggestions
            analysis['suggestions'] = self._generate_mapping_suggestions(df, source)
            
        except Exception as e:
            analysis['error'] = str(e)
        
        return analysis
    
    def _detect_column_mappings(self, columns: List[str], source: str) -> Dict[str, str]:
        """Detect potential column mappings based on column names."""
        mappings = {}
        
        # Common column name patterns
        date_patterns = ['date', 'posting date', 'transaction date', 'time']
        description_patterns = ['description', 'desc', 'original description', 'details', 'memo']
        amount_patterns = ['amount', 'debit', 'credit', 'balance', 'total']
        
        for col in columns:
            col_lower = col.lower()
            
            # Date mapping
            if any(pattern in col_lower for pattern in date_patterns):
                mappings['date'] = col
            
            # Description mapping
            elif any(pattern in col_lower for pattern in description_patterns):
                mappings['description'] = col
            
            # Amount mapping
            elif any(pattern in col_lower for pattern in amount_patterns):
                mappings['amount'] = col
        
        return mappings
    
    def _generate_mapping_suggestions(self, df: pd.DataFrame, source: str) -> List[str]:
        """Generate mapping suggestions based on data analysis."""
        suggestions = []
        
        # Check for date columns
        for col in df.columns:
            if self._looks_like_date_column(df[col]):
                suggestions.append(f"Column '{col}' appears to contain dates")
        
        # Check for amount columns
        for col in df.columns:
            if self._looks_like_amount_column(df[col]):
                suggestions.append(f"Column '{col}' appears to contain amounts")
        
        # Check for description columns
        for col in df.columns:
            if self._looks_like_description_column(df[col]):
                suggestions.append(f"Column '{col}' appears to contain descriptions")
        
        return suggestions
    
    def _looks_like_date_column(self, series: pd.Series) -> bool:
        """Check if a column looks like it contains dates."""
        try:
            # Try to parse as dates
            sample_values = series.dropna().head(10)
            if len(sample_values) == 0:
                return False
            
            parsed_dates = pd.to_datetime(sample_values, errors='coerce')
            valid_dates = parsed_dates.notna().sum()
            
            return valid_dates / len(sample_values) > 0.7  # 70% success rate
        except Exception:
            return False
    
    def _looks_like_amount_column(self, series: pd.Series) -> bool:
        """Check if a column looks like it contains amounts."""
        try:
            # Try to parse as numbers
            sample_values = series.dropna().head(10)
            if len(sample_values) == 0:
                return False
            
            # Clean and parse amounts
            cleaned_values = sample_values.astype(str).str.replace('$', '').str.replace(',', '')
            parsed_amounts = pd.to_numeric(cleaned_values, errors='coerce')
            valid_amounts = parsed_amounts.notna().sum()
            
            return valid_amounts / len(sample_values) > 0.7  # 70% success rate
        except Exception:
            return False
    
    def _looks_like_description_column(self, series: pd.Series) -> bool:
        """Check if a column looks like it contains descriptions."""
        try:
            # Check for text-like characteristics
            sample_values = series.dropna().head(10)
            if len(sample_values) == 0:
                return False
            
            # Check if values are strings and have reasonable length
            string_values = sample_values.astype(str)
            avg_length = string_values.str.len().mean()
            
            return avg_length > 5 and avg_length < 200  # Reasonable description length
        except Exception:
            return False
    
    def _get_key_columns(self, source: str) -> List[str]:
        """Get key columns for a specific source."""
        if source == "BankOfAmerica":
            return ['Status', 'Date', 'Original Description', 'Amount']
        elif source == "Chase":
            return ['Posting Date', 'Description', 'Amount']
        elif source == "RestaurantDepot":
            return ['Date', 'Description', 'Amount']
        elif source == "Sysco":
            return ['Date', 'Description', 'Amount']
        else:
            return []
    
    def _fix_csv_formatting(self, file_path: Path) -> Path:
        """Fix common CSV formatting issues like embedded linefeeds."""
        try:
            # Read the original file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if file has embedded linefeeds in quoted fields
            if '\n' in content and '"' in content:
                # Create a backup of the original file
                backup_path = file_path.with_suffix('.csv.backup')
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                # Fix embedded linefeeds in quoted fields
                fixed_content = self._fix_embedded_linefeeds(content)
                
                # Write the fixed content back to the original file
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)
                
                processing_logger.log_system_event(
                    f"Fixed CSV formatting issues in {file_path.name}",
                    {"backup_created": str(backup_path)}
                )
            
            return file_path
            
        except Exception as e:
            processing_logger.log_system_event(
                f"Error fixing CSV formatting for {file_path.name}: {str(e)}",
                level="error"
            )
            return file_path
    
    def _fix_embedded_linefeeds(self, content: str) -> str:
        """Fix embedded linefeeds in quoted CSV fields."""
        lines = content.split('\n')
        fixed_lines = []
        current_line = ""
        in_quotes = False
        
        for line in lines:
            if not in_quotes:
                # Start of a new record
                current_line = line
                # Count quotes in this line
                quote_count = line.count('"')
                if quote_count % 2 == 1:
                    # Odd number of quotes means we're entering a quoted field
                    in_quotes = True
                else:
                    # Even number of quotes, complete record
                    fixed_lines.append(current_line)
            else:
                # We're inside a quoted field, append to current line
                current_line += " " + line
                # Count quotes in this line
                quote_count = line.count('"')
                if quote_count % 2 == 1:
                    # Odd number of quotes means we're exiting the quoted field
                    in_quotes = False
                    fixed_lines.append(current_line)
                    current_line = ""
        
        # If we still have an incomplete line, add it
        if current_line:
            fixed_lines.append(current_line)
        
        return '\n'.join(fixed_lines)
    
    def _detect_source_specific_issues(self, file_path: Path, source: str) -> List[Dict[str, Any]]:
        """Detect source-specific issues in the file."""
        issues = []
        
        try:
            df = pd.read_csv(file_path, dtype=str, na_filter=False)
            
            # Map source to proper case
            source_mapping = {
                "chase": "Chase",
                "bankofamerica": "BankOfAmerica", 
                "restaurantdepot": "RestaurantDepot",
                "sysco": "Sysco"
            }
            mapped_source = source_mapping.get(source.lower(), source)
            
            if mapped_source == "Chase":
                issues.extend(self._detect_chase_issues(df))
            elif mapped_source == "BankOfAmerica":
                issues.extend(self._detect_boa_issues(df))
            elif mapped_source == "RestaurantDepot":
                issues.extend(self._detect_restaurant_depot_issues(df))
            elif mapped_source == "Sysco":
                issues.extend(self._detect_sysco_issues(df))
                
        except Exception as e:
            # Make parsing errors fixable so user can decide
            error_msg = str(e)
            issues.append({
                'type': 'csv_formatting',
                'message': f"CSV formatting issue: {error_msg}",
                'fixable': True,
                'suggestion': 'Fix CSV formatting issues automatically'
            })
        
        return issues
    
    def _detect_chase_issues(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect Chase-specific issues."""
        issues = []
        
        # Debug: Log the columns to see what we're working with
        processing_logger.log_system_event(
            f"Chase file columns: {list(df.columns)}", level="info"
        )
        
        # Check for column misalignment (Description column contains complex transaction data)
        if 'Description' in df.columns and len(df) > 0:
            sample_desc = df['Description'].iloc[0]
            processing_logger.log_system_event(
                f"Sample Description value: {sample_desc[:100]}... (length: {len(str(sample_desc))})", level="info"
            )
            # Only detect if there's a real problem with very long descriptions
            if isinstance(sample_desc, str) and len(sample_desc) > 200:
                issues.append({
                    'type': 'column_misalignment',
                    'message': 'Chase file has complex transaction data in Description column',
                    'fixable': True,  # Mark as fixable since we can parse it
                    'suggestion': 'Apply automatic parsing to extract transaction details',
                    'details': f'Description length: {len(sample_desc)} characters'
                })
        else:
            # If no Description column, check if we have any column with complex data
            for col in df.columns:
                if len(df) > 0:
                    sample_value = df[col].iloc[0]
                    # Only detect if there's a real problem with very long values
                    if isinstance(sample_value, str) and len(sample_value) > 200:
                        issues.append({
                            'type': 'column_misalignment',
                            'message': f'Chase file has complex transaction data in {col} column',
                            'fixable': True,  # Mark as fixable since we can parse it
                            'suggestion': 'Apply automatic parsing to extract transaction details',
                            'details': f'{col} length: {len(sample_value)} characters'
                        })
                        break
        
        # Only add Chase optimization if there are actual issues detected
        # (Removed artificial issue to make validation more flexible)
        
        return issues
    
    def _detect_boa_issues(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect Bank of America specific issues."""
        issues = []
        
        # Check for missing required columns
        required_columns = ['Status', 'Date', 'Original Description', 'Amount']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            issues.append({
                'type': 'missing_columns',
                'message': f'Missing required columns: {", ".join(missing_columns)}',
                'fixable': False,
                'suggestion': 'Ensure the exported file includes all required columns: Status, Date, Original Description, Amount',
                'details': f'Available columns: {list(df.columns)}'
            })
        
        return issues
    
    def _detect_restaurant_depot_issues(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect Restaurant Depot specific issues."""
        issues = []
        
        # Restaurant Depot files are typically invoice files, so we check for basic structure
        if len(df.columns) < 3:
            issues.append({
                'type': 'insufficient_data',
                'message': 'File appears to have insufficient data columns for an invoice',
                'fixable': False,
                'suggestion': 'Ensure the file contains invoice data with multiple columns',
                'details': f'Found {len(df.columns)} columns'
            })
        
        return issues
    
    def _detect_sysco_issues(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect Sysco specific issues."""
        issues = []
        
        # Sysco files are typically invoice files, so we check for basic structure
        if len(df.columns) < 3:
            issues.append({
                'type': 'insufficient_data',
                'message': 'File appears to have insufficient data columns for an invoice',
                'fixable': False,
                'suggestion': 'Ensure the file contains invoice data with multiple columns',
                'details': f'Found {len(df.columns)} columns'
            })
        
        return issues
    
    def _apply_source_specific_fix(self, file_path: Path, source: str, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Apply source-specific fixes for detected issues."""
        try:
            if issue['type'] == 'csv_formatting':
                # Fix CSV formatting issues by cleaning up inconsistent rows/columns and empty values
                return self._fix_csv_formatting_issues(file_path, issue)
            
            elif issue['type'] == 'column_misalignment':
                # For Chase files with complex transaction data, we can parse and restructure
                if source.lower() == 'chase':
                    return self._fix_chase_column_misalignment(file_path, issue)
            
            elif issue['type'] == 'chase_optimization':
                # For Chase files, apply general optimization
                if source.lower() == 'chase':
                    return self._fix_chase_optimization(file_path, issue)
            
            # Add more source-specific fixes here as needed
            return {
                'success': False,
                'message': f'No automatic fix available for {issue["type"]}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error applying fix: {str(e)}'
            }
    
    def _fix_chase_column_misalignment(self, file_path: Path, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Fix Chase column misalignment by parsing complex transaction data."""
        try:
            import pandas as pd
            import re
            
            # Read the original file
            df = pd.read_csv(file_path, dtype=str, na_filter=False)
            
            # Create a backup
            backup_path = file_path.with_suffix('.csv.backup')
            df.to_csv(backup_path, index=False)
            
            # Parse complex transaction data in Description column
            if 'Description' in df.columns:
                # Extract key transaction details using regex patterns
                def extract_transaction_details(desc):
                    if pd.isna(desc) or not isinstance(desc, str):
                        return desc
                    
                    # Look for common transaction patterns
                    patterns = [
                        r'(\d{2}/\d{2}/\d{4})\s*(\d{2}:\d{2}:\d{2})?\s*(.*?)(?=\s*\d{2}/\d{2}/\d{4}|$)',
                        r'(.*?)\s*(\d{2}/\d{2}/\d{4})\s*(\d{2}:\d{2}:\d{2})?',
                        r'(.*?)\s*(\d{2}:\d{2}:\d{2})\s*(\d{2}/\d{2}/\d{4})'
                    ]
                    
                    for pattern in patterns:
                        match = re.search(pattern, desc)
                        if match:
                            return match.group(1).strip()
                    
                    # If no pattern matches, return first 100 characters
                    return desc[:100] if len(desc) > 100 else desc
                
                # Apply the fix
                df['Description'] = df['Description'].apply(extract_transaction_details)
            
            # Save the fixed file
            df.to_csv(file_path, index=False)
            
            processing_logger.log_system_event(
                f"Fixed Chase column misalignment in {file_path.name}", level="info"
            )
            
            return {
                'success': True,
                'message': 'Chase transaction data parsed and simplified',
                'backup_created': str(backup_path)
            }
            
        except Exception as e:
            processing_logger.log_system_event(
                f"Error fixing Chase column misalignment: {str(e)}", level="error"
            )
            return {
                'success': False,
                'message': f'Error fixing Chase column misalignment: {str(e)}'
            }
    
    def _fix_chase_optimization(self, file_path: Path, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Apply general Chase file optimization."""
        try:
            import pandas as pd
            import re
            
            # Read the original file
            df = pd.read_csv(file_path, dtype=str, na_filter=False)
            
            # Create a backup
            backup_path = file_path.with_suffix('.csv.backup')
            df.to_csv(backup_path, index=False)
            
            # Apply general optimizations
            optimizations_applied = []
            
            # Clean up any excessively long descriptions
            if 'Description' in df.columns:
                def clean_description(desc):
                    if pd.isna(desc) or not isinstance(desc, str):
                        return desc
                    # Remove extra whitespace and limit length
                    cleaned = re.sub(r'\s+', ' ', desc.strip())
                    return cleaned[:200] if len(cleaned) > 200 else cleaned
                
                df['Description'] = df['Description'].apply(clean_description)
                optimizations_applied.append('Cleaned and optimized Description column')
            
            # Ensure amount column is properly formatted
            if 'Amount' in df.columns:
                def clean_amount(amount):
                    if pd.isna(amount):
                        return amount
                    # Remove any non-numeric characters except decimal point and minus
                    if isinstance(amount, str):
                        cleaned = re.sub(r'[^\d.-]', '', amount)
                        try:
                            return float(cleaned)
                        except ValueError:
                            return amount
                    return amount
                
                df['Amount'] = df['Amount'].apply(clean_amount)
                optimizations_applied.append('Cleaned Amount column format')
            
            # Save the optimized file
            df.to_csv(file_path, index=False)
            
            processing_logger.log_system_event(
                f"Applied Chase optimizations to {file_path.name}", level="info"
            )
            
            return {
                'success': True,
                'message': f'Chase file optimized: {", ".join(optimizations_applied)}',
                'backup_created': str(backup_path)
            }
            
        except Exception as e:
            processing_logger.log_system_event(
                f"Error applying Chase optimization: {str(e)}", level="error"
            )
            return {
                'success': False,
                'message': f'Error applying Chase optimization: {str(e)}'
            }
    
    def _fix_csv_formatting_issues(self, file_path: Path, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Fix CSV formatting issues by cleaning up inconsistent rows/columns and empty values."""
        try:
            # Read the file line by line
            with open(file_path, 'r', newline='', encoding='utf-8') as f:
                reader = list(csv.reader(f))

            if not reader:
                processing_logger.log_system_event(f"CSV file {file_path.name} is empty.", level="warning")
                return {'success': False, 'message': 'CSV file is empty'}

            header = reader[0]
            original_row_count = len(reader)
            
            # Special handling for Chase files with column misalignment
            if 'Details' in header and 'Posting Date' in header and 'Description' in header:
                # This is likely a Chase file - fix the column misalignment
                processing_logger.log_system_event(
                    f"[CSV FIX] {file_path.name}: Detected Chase file with column misalignment", level="info"
                )
                
                # Expected Chase header: Details, Posting Date, Description, Amount, Type, Balance, Check or Slip #
                expected_header = ['Details', 'Posting Date', 'Description', 'Amount', 'Type', 'Balance', 'Check or Slip #']
                
                # Create the correct header
                cleaned_header = expected_header
                cleaned_rows = [cleaned_header]
                
                # Process each data row
                for row in reader[1:]:
                    if not any(cell.strip() for cell in row):
                        continue
                    
                    # Ensure row has the correct number of columns
                    if len(row) < len(expected_header):
                        row = row + [''] * (len(expected_header) - len(row))
                    elif len(row) > len(expected_header):
                        row = row[:len(expected_header)]
                    
                    cleaned_rows.append(row)
                
                processing_logger.log_system_event(
                    f"[CSV FIX] {file_path.name}: Chase file fixed - Original rows={original_row_count}, After clean={len(cleaned_rows)}.", level="info"
                )
                processing_logger.log_system_event(
                    f"[CSV FIX] {file_path.name}: New header: {cleaned_header}", level="info"
                )
                if len(cleaned_rows) > 1:
                    processing_logger.log_system_event(
                        f"[CSV FIX] {file_path.name}: Sample fixed row: {cleaned_rows[1]}", level="info"
                    )
            else:
                # Generic CSV fixing for other file types
                n_cols = len(header)
                cleaned_rows = [header]
                fixed_row_count = 0

                # Clean each row: pad or trim to header length, skip empty rows
                for row in reader[1:]:
                    # Remove completely empty rows
                    if not any(cell.strip() for cell in row):
                        continue
                    # Pad or trim row
                    if len(row) < n_cols:
                        row = row + [''] * (n_cols - len(row))
                    elif len(row) > n_cols:
                        row = row[:n_cols]
                    cleaned_rows.append(row)
                    fixed_row_count += 1

                # Remove completely empty columns
                # Transpose, filter, then transpose back
                transposed = list(zip(*cleaned_rows))
                non_empty_cols = [col for col in transposed if any(cell.strip() for cell in col[1:])]
                cleaned_rows = list(map(list, zip(*non_empty_cols))) if non_empty_cols else [header]

                processing_logger.log_system_event(
                    f"[CSV FIX] {file_path.name}: Generic fix - Original rows={original_row_count}, After clean={len(cleaned_rows)}.", level="info"
                )

            # Create a backup
            backup_path = file_path.with_suffix('.csv.backup')
            os.rename(file_path, backup_path)

            # Write cleaned CSV
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerows(cleaned_rows)

            processing_logger.log_system_event(
                f"Fixed CSV formatting issues in {file_path.name}", level="info"
            )
            return {
                'success': True,
                'message': 'CSV formatting issues fixed',
                'backup_created': str(backup_path)
            }
        except Exception as e:
            processing_logger.log_system_event(
                f"Error fixing CSV formatting issues: {str(e)}", level="error"
            )
            return {
                'success': False,
                'message': f'Error fixing CSV formatting issues: {str(e)}'
            }
    
    def _add_backward_compatibility(self, validation_result, source):
        # Ensure required fields for frontend compatibility
        present_columns = validation_result.get('present_columns')
        required_columns = validation_result.get('required_columns')
        missing_columns = validation_result.get('missing_columns')
        is_valid = validation_result.get('valid', False)
        
        # If not present, try to infer from issues_detected or errors
        if 'columns' in validation_result:
            present_columns = validation_result['columns']
        elif 'all_columns' in validation_result:
            present_columns = validation_result['all_columns']
        elif 'record_count' in validation_result and validation_result['record_count'] > 0:
            sample_data = validation_result.get('sample_data')
            if sample_data and isinstance(sample_data, list) and len(sample_data) > 0:
                present_columns = list(sample_data[0].keys())
        
        # Try to get required columns from mapping_manager
        if not required_columns:
            mapping = mapping_manager.get_mapping(source)
            if mapping and hasattr(mapping, 'required_columns'):
                required_columns = list(mapping.required_columns)
        
        # Compute missing columns
        if present_columns is not None and required_columns is not None:
            missing_columns = [col for col in required_columns if col not in present_columns]
            is_valid = len(missing_columns) == 0 and validation_result.get('valid', True)
        else:
            missing_columns = []
        
        # Ensure issues_detected is always an array for frontend compatibility
        if 'issues_detected' not in validation_result:
            validation_result['issues_detected'] = []
        
        # Ensure user_action_required is set if there are fixable issues
        if validation_result.get('issues_detected'):
            fixable_issues = [issue for issue in validation_result['issues_detected'] if issue.get('fixable', False)]
            if fixable_issues:
                validation_result['user_action_required'] = True
                validation_result['can_proceed'] = False
        
        validation_result['present_columns'] = present_columns or []
        validation_result['required_columns'] = required_columns or []
        validation_result['missing_columns'] = missing_columns or []
        validation_result['is_valid'] = is_valid
        
        return validation_result 