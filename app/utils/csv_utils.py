"""
CSV utility functions for Financial Data Processor.
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from app.utils.logging import processing_logger


class CSVUtils:
    """Utility class for CSV processing operations."""
    
    @staticmethod
    def validate_csv_structure(file_path: Path, source: str) -> Tuple[bool, List[str]]:
        """Validate CSV file structure for a specific source."""
        errors = []
        
        try:
            df = pd.read_csv(file_path, nrows=5)  # Read first 5 rows for validation
            
            if source == "BankOfAmerica":
                required_columns = ['Status', 'Date', 'Original Description', 'Amount']
                for col in required_columns:
                    if col not in df.columns:
                        errors.append(f"Missing required column: {col}")
            
            elif source == "Chase":
                # Chase files have specific structure: Details, Posting Date, Description, Amount, Type, Balance, Check or Slip
                # We focus on: Posting Date, Description, Amount
                required_columns = ['Posting Date', 'Description', 'Amount']
                for col in required_columns:
                    if col not in df.columns:
                        errors.append(f"Missing required column: {col}")
                
                # Check for optional columns
                optional_columns = ['Details', 'Type', 'Balance', 'Check or Slip']
                found_optional = [col for col in optional_columns if col in df.columns]
                if found_optional:
                    processing_logger.log_system_event(
                        f"Found additional Chase columns: {', '.join(found_optional)}", level="info"
                    )
            
            elif source in ["RestaurantDepot", "Sysco"]:
                # These sources may have varying structures
                invoice_indicators = ['Invoice', 'Date', 'Total', 'Amount', 'Item']
                found_indicators = [col for col in df.columns if any(indicator in col for indicator in invoice_indicators)]
                
                if len(found_indicators) < 2:
                    errors.append("File may not be in expected format")
            
            # General validation
            if len(df) == 0:
                errors.append("File is empty")
            
            if len(df) != len(df.drop_duplicates()):
                errors.append("File contains duplicate rows")
            
            return len(errors) == 0, errors
            
        except Exception as e:
            errors.append(f"File reading error: {str(e)}")
            return False, errors
    
    @staticmethod
    def parse_date(date_str: str, date_format: str = "MM/DD/YYYY") -> Optional[datetime]:
        """Parse date string with various formats."""
        if pd.isna(date_str) or not date_str:
            return None
        
        date_str = str(date_str).strip()
        
        # Try common date formats
        formats = [
            "%m/%d/%Y",
            "%Y-%m-%d", 
            "%m-%d-%Y",
            "%d/%m/%Y",
            "%Y/%m/%d"
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        return None
    
    @staticmethod
    def extract_date_from_row(row: pd.Series) -> Optional[str]:
        """Extract date from a row in various formats."""
        for value in row.values:
            if pd.notna(value):
                value_str = str(value)
                # Try to parse common date formats
                for fmt in ['%m/%d/%Y', '%Y-%m-%d', '%m-%d-%Y']:
                    try:
                        datetime.strptime(value_str, fmt)
                        return value_str
                    except ValueError:
                        continue
        return None
    
    @staticmethod
    def extract_total_amount(df: pd.DataFrame) -> float:
        """Extract total amount from invoice data."""
        # Look for total amount in common column names
        total_columns = ['Total', 'Amount', 'Sum', 'Grand Total']
        
        for col in total_columns:
            if col in df.columns:
                # Get the last non-null value
                values = df[col].dropna()
                if not values.empty:
                    try:
                        return float(values.iloc[-1])
                    except (ValueError, TypeError):
                        continue
        
        # If no total found, sum all numeric columns
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        if not numeric_columns.empty:
            return float(df[numeric_columns].sum().sum())
        
        return 0.0
    
    @staticmethod
    def clean_amount(amount_str: str) -> float:
        """Clean and convert amount string to float."""
        if pd.isna(amount_str):
            return 0.0
        
        amount_str = str(amount_str).strip()
        
        # Remove currency symbols and commas
        amount_str = amount_str.replace('$', '').replace(',', '')
        
        # Handle parentheses for negative amounts
        if amount_str.startswith('(') and amount_str.endswith(')'):
            amount_str = '-' + amount_str[1:-1]
        
        try:
            return float(amount_str)
        except ValueError:
            return 0.0
    
    @staticmethod
    def group_transactions_by_month(transactions: List[Dict[str, Any]]) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
        """Group transactions by month and description."""
        grouped_data = {}
        
        for transaction in transactions:
            try:
                # Parse date to extract month and year
                date_obj = CSVUtils.parse_date(transaction['date'])
                if not date_obj:
                    continue
                
                month_key = f"{date_obj.year}_{date_obj.month:02d}"
                description = transaction['description']
                
                if month_key not in grouped_data:
                    grouped_data[month_key] = {}
                
                if description not in grouped_data[month_key]:
                    grouped_data[month_key][description] = []
                
                grouped_data[month_key][description].append(transaction)
                
            except Exception as e:
                processing_logger.log_system_event(
                    f"Error grouping transaction: {str(e)}", level="warning"
                )
                continue
        
        return grouped_data
    
    @staticmethod
    def generate_csv_content(month_data: Dict[str, List[Dict[str, Any]]], 
                           options: Dict[str, Any]) -> str:
        """Generate CSV content for a month."""
        rows = []
        
        for description, transactions in month_data.items():
            group_total = sum(t['amount'] for t in transactions)
            
            for transaction in transactions:
                # Start with the basic required fields
                row = {
                    'Date': transaction['date'],
                    'Description': description,
                    'Amount': transaction['amount'],
                    'Group Total': group_total
                }
                
                # Add all additional fields from the transaction
                for key, value in transaction.items():
                    if key not in ['date', 'description', 'amount', 'source_file']:
                        row[key] = value
                
                if options.get('include_source_file', True):
                    row['Source File'] = transaction['source_file']
                
                rows.append(row)
        
        # Convert to DataFrame and generate CSV
        df = pd.DataFrame(rows)
        return df.to_csv(index=False)
    
    @staticmethod
    def validate_data_types(df: pd.DataFrame, source: str) -> List[str]:
        """Validate data types in DataFrame."""
        errors = []
        
        if source == "BankOfAmerica":
            if 'Amount' in df.columns:
                # Check if Amount column contains valid numbers
                invalid_amounts = df['Amount'].apply(lambda x: not CSVUtils.is_valid_amount(x))
                if invalid_amounts.any():
                    errors.append(f"Found {invalid_amounts.sum()} invalid amounts")
            
            if 'Date' in df.columns:
                # Check if Date column contains valid dates
                invalid_dates = df['Date'].apply(lambda x: CSVUtils.parse_date(x) is None)
                if invalid_dates.any():
                    errors.append(f"Found {invalid_dates.sum()} invalid dates")
        
        return errors
    
    @staticmethod
    def is_valid_amount(value: Any) -> bool:
        """Check if value is a valid amount."""
        if pd.isna(value):
            return False
        
        try:
            CSVUtils.clean_amount(str(value))
            return True
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def get_column_mapping(source: str) -> Dict[str, str]:
        """Get column mapping for different sources."""
        mappings = {
            "BankOfAmerica": {
                "date": "Date",
                "description": "Original Description", 
                "amount": "Amount",
                "status": "Status"
            },
            "Chase": {
                "date": "Posting Date",
                "description": "Description",
                "amount": "Amount",
                "details": "Details",
                "type": "Type",
                "balance": "Balance",
                "check_slip": "Check or Slip"
            },
            "RestaurantDepot": {
                "date": "Date",
                "description": "Description", 
                "amount": "Total"
            },
            "Sysco": {
                "date": "Date",
                "description": "Description",
                "amount": "Total"
            }
        }
        
        return mappings.get(source, {}) 