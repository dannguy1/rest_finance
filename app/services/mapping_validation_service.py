"""
Enhanced mapping validation service for testing configurations against sample data.
"""
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from app.config.source_mapping import SourceMappingConfig, ColumnMapping
from app.utils.logging import processing_logger


class MappingValidationService:
    """Service for validating mapping configurations against sample data."""
    
    def __init__(self):
        self.validation_results = []
    
    def validate_mapping_comprehensive(self, mapping: SourceMappingConfig, sample_data: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Comprehensive validation of a mapping configuration.
        
        Args:
            mapping: The mapping configuration to validate
            sample_data: Optional sample data to test against
            
        Returns:
            Dictionary with validation results
        """
        errors = []
        warnings = []
        test_results = {}
        
        # 1. Basic structural validation
        structural_errors = self._validate_structure(mapping)
        errors.extend(structural_errors)
        
        # 2. Format validation
        format_errors, format_warnings = self._validate_formats(mapping)
        errors.extend(format_errors)
        warnings.extend(format_warnings)
        
        # 3. Sample data validation (if provided)
        if sample_data:
            data_errors, data_warnings, test_results = self._validate_against_sample_data(mapping, sample_data)
            errors.extend(data_errors)
            warnings.extend(data_warnings)
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "test_results": test_results,
            "summary": {
                "total_checks": len(errors) + len(warnings),
                "error_count": len(errors),
                "warning_count": len(warnings),
                "sample_data_tested": sample_data is not None
            }
        }
    
    def _validate_structure(self, mapping: SourceMappingConfig) -> List[str]:
        """Validate the basic structure of the mapping."""
        errors = []
        
        # Check required mappings exist
        if not mapping.date_mapping:
            errors.append("Date mapping is required")
        if not mapping.description_mapping:
            errors.append("Description mapping is required")
        if not mapping.amount_mapping:
            errors.append("Amount mapping is required")
        
        # Check for duplicate source columns
        source_columns = []
        if mapping.date_mapping:
            source_columns.append(mapping.date_mapping.source_column)
        if mapping.description_mapping:
            source_columns.append(mapping.description_mapping.source_column)
        if mapping.amount_mapping:
            source_columns.append(mapping.amount_mapping.source_column)
        
        source_columns.extend([opt.source_column for opt in mapping.optional_mappings])
        
        if len(source_columns) != len(set(source_columns)):
            errors.append("Duplicate source columns found")
        
        # Check that expected columns include all mapped columns
        mapped_columns = set(source_columns)
        expected_columns = set(mapping.expected_columns)
        
        if not mapped_columns.issubset(expected_columns):
            missing = mapped_columns - expected_columns
            errors.append(f"Expected columns missing mapped columns: {missing}")
        
        return errors
    
    def _validate_formats(self, mapping: SourceMappingConfig) -> Tuple[List[str], List[str]]:
        """Validate date and amount formats."""
        errors = []
        warnings = []
        
        # Validate date format
        if mapping.date_mapping and mapping.date_mapping.date_format:
            try:
                # Convert common format strings to Python datetime format
                format_str = mapping.date_mapping.date_format
                if format_str == "MM/DD/YYYY":
                    format_str = "%m/%d/%Y"
                elif format_str == "DD/MM/YYYY":
                    format_str = "%d/%m/%Y"
                elif format_str == "YYYY-MM-DD":
                    format_str = "%Y-%m-%d"
                elif format_str == "MM-DD-YYYY":
                    format_str = "%m-%d-%Y"
                
                # Test the date format with a sample date
                test_date = "01/15/2024"
                datetime.strptime(test_date, format_str)
            except ValueError:
                errors.append(f"Invalid date format: {mapping.date_mapping.date_format}")
        
        # Validate amount format
        if mapping.amount_mapping and mapping.amount_mapping.amount_format:
            valid_formats = ["USD", "EUR", "GBP", "CAD"]
            if mapping.amount_mapping.amount_format not in valid_formats:
                warnings.append(f"Unknown amount format: {mapping.amount_mapping.amount_format}")
        
        return errors, warnings
    
    def _validate_against_sample_data(self, mapping: SourceMappingConfig, sample_data: List[Dict[str, Any]]) -> Tuple[List[str], List[str], Dict[str, Any]]:
        """Validate mapping against sample data."""
        errors = []
        warnings = []
        test_results = {
            "rows_processed": 0,
            "successful_conversions": 0,
            "failed_conversions": 0,
            "column_tests": {}
        }
        
        if not sample_data:
            return errors, warnings, test_results
        
        try:
            # Convert sample data to DataFrame
            df = pd.DataFrame(sample_data)
            test_results["rows_processed"] = len(df)
            
            # Test each required mapping
            required_mappings = [
                ("date", mapping.date_mapping),
                ("description", mapping.description_mapping),
                ("amount", mapping.amount_mapping)
            ]
            
            for field_name, column_mapping in required_mappings:
                if not column_mapping:
                    continue
                
                source_col = column_mapping.source_column
                if source_col not in df.columns:
                    errors.append(f"Required column '{source_col}' not found in sample data")
                    continue
                
                # Test data conversion
                conversion_success = 0
                conversion_failures = 0
                
                for idx, value in enumerate(df[source_col]):
                    try:
                        if field_name == "date":
                            # Test date parsing
                            if pd.notna(value):
                                # Convert common format strings to Python datetime format
                                format_str = mapping.date_mapping.date_format
                                if format_str == "MM/DD/YYYY":
                                    format_str = "%m/%d/%Y"
                                elif format_str == "DD/MM/YYYY":
                                    format_str = "%d/%m/%Y"
                                elif format_str == "YYYY-MM-DD":
                                    format_str = "%Y-%m-%d"
                                elif format_str == "MM-DD-YYYY":
                                    format_str = "%m-%d-%Y"
                                
                                pd.to_datetime(value, format=format_str)
                                conversion_success += 1
                            else:
                                conversion_failures += 1
                        elif field_name == "amount":
                            # Test amount parsing
                            if pd.notna(value):
                                # Handle various amount formats
                                amount_str = str(value).strip()
                                # Remove currency symbols and commas
                                amount_str = amount_str.replace('$', '').replace(',', '').replace('(', '').replace(')', '')
                                # Handle negative amounts in parentheses
                                if amount_str.startswith('-') or amount_str.endswith('-'):
                                    amount_str = '-' + amount_str.replace('-', '')
                                float(amount_str)
                                conversion_success += 1
                            else:
                                conversion_failures += 1
                        else:
                            # Test description (just check it's not empty)
                            if pd.notna(value) and str(value).strip():
                                conversion_success += 1
                            else:
                                conversion_failures += 1
                    except Exception:
                        conversion_failures += 1
                
                test_results["column_tests"][field_name] = {
                    "source_column": source_col,
                    "conversion_success": conversion_success,
                    "conversion_failures": conversion_failures,
                    "success_rate": conversion_success / len(df) if len(df) > 0 else 0
                }
                
                test_results["successful_conversions"] += conversion_success
                test_results["failed_conversions"] += conversion_failures
                
                # Add warnings for low success rates
                success_rate = conversion_success / len(df) if len(df) > 0 else 0
                if success_rate < 0.8:
                    warnings.append(f"Low conversion success rate for {field_name}: {success_rate:.1%}")
            
            # Test optional mappings
            for opt_mapping in mapping.optional_mappings:
                source_col = opt_mapping.source_column
                if source_col in df.columns:
                    # Optional columns are not required to have data
                    non_empty_count = df[source_col].notna().sum()
                    test_results["column_tests"][f"optional_{opt_mapping.target_field}"] = {
                        "source_column": source_col,
                        "non_empty_count": non_empty_count,
                        "total_count": len(df)
                    }
                else:
                    warnings.append(f"Optional column '{source_col}' not found in sample data")
            
        except Exception as e:
            errors.append(f"Error processing sample data: {str(e)}")
        
        return errors, warnings, test_results
    
    def generate_sample_data_template(self, mapping: SourceMappingConfig) -> List[Dict[str, Any]]:
        """Generate a template for sample data based on the mapping."""
        template = {}
        
        # Add required columns
        if mapping.date_mapping:
            template[mapping.date_mapping.source_column] = "01/15/2024"
        if mapping.description_mapping:
            template[mapping.description_mapping.source_column] = "SAMPLE TRANSACTION"
        if mapping.amount_mapping:
            template[mapping.amount_mapping.source_column] = "100.00"
        
        # Add optional columns
        for opt_mapping in mapping.optional_mappings:
            template[opt_mapping.source_column] = "SAMPLE_VALUE"
        
        return [template]
    
    def validate_file_against_mapping(self, file_path: Path, mapping: SourceMappingConfig) -> Dict[str, Any]:
        """Validate an actual file against the mapping configuration."""
        errors = []
        warnings = []
        test_results = {}
        
        try:
            # Read the file
            if file_path.suffix.lower() == '.csv':
                df = pd.read_csv(file_path)
            elif file_path.suffix.lower() in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
            else:
                errors.append(f"Unsupported file format: {file_path.suffix}")
                return {"valid": False, "errors": errors, "warnings": warnings}
            
            # Check if required columns exist
            required_columns = [
                mapping.date_mapping.source_column,
                mapping.description_mapping.source_column,
                mapping.amount_mapping.source_column
            ]
            
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                errors.append(f"Missing required columns: {missing_columns}")
            
            # Test data conversion on first few rows
            sample_df = df.head(10)
            _, _, test_results = self._validate_against_sample_data(mapping, sample_df.to_dict('records'))
            
            # Check for empty required columns
            for col in required_columns:
                if col in df.columns:
                    empty_count = df[col].isna().sum()
                    if empty_count > 0:
                        warnings.append(f"Column '{col}' has {empty_count} empty values")
            
        except Exception as e:
            errors.append(f"Error reading file: {str(e)}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "test_results": test_results
        }


# Global validation service instance
mapping_validation_service = MappingValidationService() 