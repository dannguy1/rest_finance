"""
Data processing service for Financial Data Processor.
"""
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from pathlib import Path
import asyncio
from datetime import datetime
from app.config import settings
from app.utils.logging import processing_logger
from app.utils.file_utils import FileUtils
from app.utils.csv_utils import CSVUtils
from app.models.file_models import ProcessingOptions, ProcessingResult


class DataProcessor:
    """Core data processing engine."""
    
    def __init__(self, data_dir: Optional[str] = None):
        """Initialize data processor."""
        self.data_dir = Path(data_dir) if data_dir else settings.data_path
        processing_logger.log_system_event("DataProcessor initialized", {"data_dir": str(self.data_dir)})
    
    async def process_source(self, source: str, options: Optional[ProcessingOptions] = None) -> ProcessingResult:
        """Process all files for a specific source, automatically generating files for all years found in the data."""
        start_time = datetime.now()
        
        if options is None:
            options = ProcessingOptions()
        
        try:
            processing_logger.log_processing_job(
                "system", source, "processing", 0.0, f"Starting processing for {source}"
            )
            
            # 1. Read input files
            input_files = await self._get_input_files(source)
            if not input_files:
                return ProcessingResult(
                    success=False,
                    files_processed=0,
                    output_files=[],
                    error_message=f"No input files found for {source}"
                )
            
            # 2. Parse and validate data
            parsed_data = await self._parse_files(input_files, source)
            if not parsed_data:
                return ProcessingResult(
                    success=False,
                    files_processed=0,
                    output_files=[],
                    error_message=f"No valid data found in files for {source}"
                )
            
            # 3. Group by month and description
            grouped_data = CSVUtils.group_transactions_by_month(parsed_data)
            
            # 4. Generate monthly CSV files for all years found in the data
            output_files = []
            for month_key in grouped_data.keys():
                year_part, month_part = month_key.split('_')
                year = int(year_part)
                
                # Generate files for this year
                year_output_files = await self._generate_monthly_files(source, year, {month_key: grouped_data[month_key]}, options)
                output_files.extend(year_output_files)
                
                # Update metadata for this year
                await self._update_processing_history(source, year, year_output_files)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            processing_logger.log_processing_job(
                "system", source, "completed", 100.0, f"Processing completed for {source}"
            )
            
            return ProcessingResult(
                success=True,
                files_processed=len(input_files),
                output_files=output_files,
                processing_time=processing_time
            )
            
        except Exception as e:
            processing_logger.log_processing_job(
                "system", source, "error", 0.0, f"Processing failed for {source}: {str(e)}"
            )
            return ProcessingResult(
                success=False,
                files_processed=0,
                output_files=[],
                error_message=str(e)
            )
    
    async def _get_input_files(self, source: str) -> List[Path]:
        """Get all input files for a source."""
        source_dir = self.data_dir / source / "input"
        if not source_dir.exists():
            return []
        
        return list(source_dir.glob("*.csv"))
    
    async def _parse_files(self, files: List[Path], source: str) -> List[Dict[str, Any]]:
        """Parse files based on source type."""
        if source == "BankOfAmerica":
            return await self._parse_boa_files(files)
        elif source == "Chase":
            return await self._parse_chase_files(files)
        elif source == "RestaurantDepot":
            return await self._parse_restaurant_depot_files(files)
        elif source == "Sysco":
            return await self._parse_sysco_files(files)
        else:
            raise ValueError(f"Unsupported source type: {source}")
    
    async def _parse_boa_files(self, files: List[Path]) -> List[Dict[str, Any]]:
        """Parse Bank of America CSV files."""
        all_transactions = []
        
        for file_path in files:
            try:
                df = pd.read_csv(file_path)
                
                # Validate required columns
                required_columns = ['Status', 'Date', 'Original Description', 'Amount']
                if not all(col in df.columns for col in required_columns):
                    raise ValueError(f"Missing required columns in {file_path.name}")
                
                for _, row in df.iterrows():
                    try:
                        transaction = {
                            'date': str(row['Date']),
                            'description': str(row['Original Description']),
                            'amount': CSVUtils.clean_amount(row['Amount']),
                            'source_file': file_path.name
                        }
                        all_transactions.append(transaction)
                    except Exception as e:
                        processing_logger.log_system_event(
                            f"Error parsing row in {file_path.name}: {str(e)}", level="warning"
                        )
                        continue
                        
            except Exception as e:
                processing_logger.log_file_operation("parse", file_path.name, "BankOfAmerica", False, str(e))
                raise
        
        return all_transactions
    
    async def _parse_chase_files(self, files: List[Path]) -> List[Dict[str, Any]]:
        """Parse Chase CSV files."""
        all_transactions = []
        
        for file_path in files:
            try:
                df = pd.read_csv(file_path)
                
                # Chase files use 'Posting Date', 'Description', 'Amount'
                # Check for the actual column names in Chase files
                date_column = None
                if 'Posting Date' in df.columns:
                    date_column = 'Posting Date'
                elif 'Date' in df.columns:
                    date_column = 'Date'
                else:
                    raise ValueError(f"Missing date column in {file_path.name}")
                
                description_column = 'Description'
                amount_column = 'Amount'
                
                # Validate required columns
                required_columns = [date_column, description_column, amount_column]
                if not all(col in df.columns for col in required_columns):
                    raise ValueError(f"Missing required columns in {file_path.name}")
                
                for _, row in df.iterrows():
                    try:
                        transaction = {
                            'date': str(row[date_column]),
                            'description': str(row[description_column]),
                            'amount': CSVUtils.clean_amount(row[amount_column]),
                            'source_file': file_path.name
                        }
                        all_transactions.append(transaction)
                    except Exception as e:
                        processing_logger.log_system_event(
                            f"Error parsing row in {file_path.name}: {str(e)}", level="warning"
                        )
                        continue
                        
            except Exception as e:
                processing_logger.log_file_operation("parse", file_path.name, "Chase", False, str(e))
                raise
        
        return all_transactions
    
    async def _parse_restaurant_depot_files(self, files: List[Path]) -> List[Dict[str, Any]]:
        """Parse Restaurant Depot invoice files."""
        all_transactions = []
        
        for file_path in files:
            try:
                df = pd.read_csv(file_path)
                
                # Extract invoice number and date from header
                invoice_number = file_path.stem  # Use filename as invoice number
                
                # Find date in the data (usually in first few rows)
                date_found = False
                for _, row in df.iterrows():
                    if 'Date' in str(row).lower() or 'Invoice' in str(row).lower():
                        # Extract date from this row
                        date_str = CSVUtils.extract_date_from_row(row)
                        if date_str:
                            transaction = {
                                'date': date_str,
                                'description': f"Invoice {invoice_number}",
                                'amount': CSVUtils.extract_total_amount(df),
                                'source_file': file_path.name
                            }
                            all_transactions.append(transaction)
                            date_found = True
                            break
                
                if not date_found:
                    # Use current date if no date found
                    transaction = {
                        'date': datetime.now().strftime('%m/%d/%Y'),
                        'description': f"Invoice {invoice_number}",
                        'amount': CSVUtils.extract_total_amount(df),
                        'source_file': file_path.name
                    }
                    all_transactions.append(transaction)
                    
            except Exception as e:
                processing_logger.log_file_operation("parse", file_path.name, "RestaurantDepot", False, str(e))
                raise
        
        return all_transactions
    
    async def _parse_sysco_files(self, files: List[Path]) -> List[Dict[str, Any]]:
        """Parse Sysco invoice files."""
        all_transactions = []
        
        for file_path in files:
            try:
                df = pd.read_csv(file_path)
                
                # Extract invoice number and date from header
                invoice_number = file_path.stem  # Use filename as invoice number
                
                # Find date in the data
                date_found = False
                for _, row in df.iterrows():
                    if 'Date' in str(row).lower() or 'Invoice' in str(row).lower():
                        date_str = CSVUtils.extract_date_from_row(row)
                        if date_str:
                            transaction = {
                                'date': date_str,
                                'description': f"Sysco Invoice {invoice_number}",
                                'amount': CSVUtils.extract_total_amount(df),
                                'source_file': file_path.name
                            }
                            all_transactions.append(transaction)
                            date_found = True
                            break
                
                if not date_found:
                    transaction = {
                        'date': datetime.now().strftime('%m/%d/%Y'),
                        'description': f"Sysco Invoice {invoice_number}",
                        'amount': CSVUtils.extract_total_amount(df),
                        'source_file': file_path.name
                    }
                    all_transactions.append(transaction)
                    
            except Exception as e:
                processing_logger.log_file_operation("parse", file_path.name, "Sysco", False, str(e))
                raise
        
        return all_transactions
    
    async def _generate_monthly_files(self, source: str, year: int, grouped_data: Dict[str, Dict[str, List[Dict[str, Any]]]], 
                                    options: ProcessingOptions) -> List[str]:
        """Generate monthly CSV files."""
        output_files = []
        
        for month_key, month_data in grouped_data.items():
            year_part, month_part = month_key.split('_')
            if int(year_part) != year:
                continue
            
            # Create output directory
            output_dir = self.data_dir / source / "output" / str(year)
            FileUtils.ensure_directory(output_dir)
            
            # Generate CSV content
            csv_content = CSVUtils.generate_csv_content(month_data, options.dict())
            
            # Write to file
            output_file = output_dir / f"{month_part}_{year}.csv"
            success = await FileUtils.write_file_content(output_file, csv_content)
            
            if success:
                output_files.append(str(output_file))
                processing_logger.log_file_operation(
                    "generate", output_file.name, source, True
                )
            else:
                processing_logger.log_file_operation(
                    "generate", output_file.name, source, False, "Failed to write file"
                )
        
        return output_files
    
    async def _update_processing_history(self, source: str, year: int, output_files: List[str]) -> None:
        """Update processing history (placeholder for database integration)."""
        processing_logger.log_system_event(
            f"Processing history updated for {source} year {year}",
            {"output_files": output_files}
        )
    
    async def get_processing_summary(self, source: str, year: int) -> Dict[str, Any]:
        """Get processing summary for a source and year."""
        try:
            output_dir = self.data_dir / source / "output" / str(year)
            if not output_dir.exists():
                return {"total_files": 0, "total_records": 0, "total_amount": 0.0}
            
            total_files = 0
            total_records = 0
            total_amount = 0.0
            
            for csv_file in output_dir.glob("*.csv"):
                total_files += 1
                df = pd.read_csv(csv_file)
                total_records += len(df)
                if 'Amount' in df.columns:
                    total_amount += df['Amount'].sum()
            
            return {
                "total_files": total_files,
                "total_records": total_records,
                "total_amount": total_amount
            }
            
        except Exception as e:
            processing_logger.log_system_event(
                f"Error getting processing summary: {str(e)}", level="error"
            )
            return {"total_files": 0, "total_records": 0, "total_amount": 0.0}

    async def process_single_file(self, source: str, filename: str, options: Optional[ProcessingOptions] = None) -> ProcessingResult:
        """Process a single file for a specific source."""
        start_time = datetime.now()
        
        if options is None:
            options = ProcessingOptions()
        
        try:
            processing_logger.log_processing_job(
                "system", source, "processing", 0.0, f"Starting processing for {source} file {filename}"
            )
            
            # 1. Get the specific file
            file_path = self.data_dir / source / "input" / filename
            if not file_path.exists():
                return ProcessingResult(
                    success=False,
                    files_processed=0,
                    output_files=[],
                    error_message=f"File {filename} not found for {source}"
                )
            
            # 2. Parse the specific file
            parsed_data = await self._parse_single_file(file_path, source)
            if not parsed_data:
                return ProcessingResult(
                    success=False,
                    files_processed=0,
                    output_files=[],
                    error_message=f"No valid data found in {filename}"
                )
            
            # 3. Group by month and description
            grouped_data = CSVUtils.group_transactions_by_month(parsed_data)
            
            # 4. Generate monthly CSV files for all years found in the data
            output_files = []
            for month_key in grouped_data.keys():
                year_part, month_part = month_key.split('_')
                year = int(year_part)
                
                # Generate files for this year
                year_output_files = await self._generate_monthly_files(source, year, {month_key: grouped_data[month_key]}, options)
                output_files.extend(year_output_files)
                
                # Update metadata for this year
                await self._update_processing_history(source, year, year_output_files)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            processing_logger.log_processing_job(
                "system", source, "completed", 100.0, f"Processing completed for {source} file {filename}"
            )
            
            return ProcessingResult(
                success=True,
                files_processed=1,
                output_files=output_files,
                processing_time=processing_time
            )
            
        except Exception as e:
            processing_logger.log_processing_job(
                "system", source, "error", 0.0, f"Processing failed for {source} file {filename}: {str(e)}"
            )
            return ProcessingResult(
                success=False,
                files_processed=0,
                output_files=[],
                error_message=str(e)
            )

    async def _parse_single_file(self, file_path: Path, source: str) -> List[Dict[str, Any]]:
        """Parse a single file based on source type."""
        if source == "BankOfAmerica":
            return await self._parse_boa_single_file(file_path)
        elif source == "Chase":
            return await self._parse_chase_single_file(file_path)
        elif source == "RestaurantDepot":
            return await self._parse_restaurant_depot_single_file(file_path)
        elif source == "Sysco":
            return await self._parse_sysco_single_file(file_path)
        else:
            raise ValueError(f"Unsupported source type: {source}")

    async def _parse_boa_single_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Parse a single Bank of America CSV file."""
        transactions = []
        
        try:
            df = pd.read_csv(file_path)
            
            # Validate required columns
            required_columns = ['Status', 'Date', 'Original Description', 'Amount']
            if not all(col in df.columns for col in required_columns):
                raise ValueError(f"Missing required columns in {file_path.name}")
            
            for _, row in df.iterrows():
                try:
                    transaction = {
                        'date': str(row['Date']),
                        'description': str(row['Original Description']),
                        'amount': CSVUtils.clean_amount(row['Amount']),
                        'source_file': file_path.name
                    }
                    transactions.append(transaction)
                except Exception as e:
                    processing_logger.log_system_event(
                        f"Error parsing row in {file_path.name}: {str(e)}", level="warning"
                    )
                    continue
                    
        except Exception as e:
            processing_logger.log_file_operation("parse", file_path.name, "BankOfAmerica", False, str(e))
            raise
        
        return transactions

    async def _parse_chase_single_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Parse a single Chase CSV file."""
        transactions = []
        
        try:
            df = pd.read_csv(file_path)
            
            # Chase files use 'Posting Date', 'Description', 'Amount'
            # Check for the actual column names in Chase files
            date_column = None
            if 'Posting Date' in df.columns:
                date_column = 'Posting Date'
            elif 'Date' in df.columns:
                date_column = 'Date'
            else:
                raise ValueError(f"Missing date column in {file_path.name}")
            
            description_column = 'Description'
            amount_column = 'Amount'
            
            # Validate required columns
            required_columns = [date_column, description_column, amount_column]
            if not all(col in df.columns for col in required_columns):
                raise ValueError(f"Missing required columns in {file_path.name}")
            
            for _, row in df.iterrows():
                try:
                    transaction = {
                        'date': str(row[date_column]),
                        'description': str(row[description_column]),
                        'amount': CSVUtils.clean_amount(row[amount_column]),
                        'source_file': file_path.name
                    }
                    transactions.append(transaction)
                except Exception as e:
                    processing_logger.log_system_event(
                        f"Error parsing row in {file_path.name}: {str(e)}", level="warning"
                    )
                    continue
                    
        except Exception as e:
            processing_logger.log_file_operation("parse", file_path.name, "Chase", False, str(e))
            raise
        
        return transactions

    async def _parse_restaurant_depot_single_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Parse a single Restaurant Depot invoice file."""
        transactions = []
        
        try:
            df = pd.read_csv(file_path)
            
            # Extract invoice number and date from header
            invoice_number = file_path.stem  # Use filename as invoice number
            
            # Find date in the data (usually in first few rows)
            date_found = False
            for _, row in df.iterrows():
                if 'Date' in str(row).lower() or 'Invoice' in str(row).lower():
                    # Extract date from this row
                    date_str = CSVUtils.extract_date_from_row(row)
                    if date_str:
                        transaction = {
                            'date': date_str,
                            'description': f"Invoice {invoice_number}",
                            'amount': CSVUtils.extract_total_amount(df),
                            'source_file': file_path.name
                        }
                        transactions.append(transaction)
                        date_found = True
                        break
            
            if not date_found:
                # Use current date if no date found
                transaction = {
                    'date': datetime.now().strftime('%m/%d/%Y'),
                    'description': f"Invoice {invoice_number}",
                    'amount': CSVUtils.extract_total_amount(df),
                    'source_file': file_path.name
                }
                transactions.append(transaction)
                
        except Exception as e:
            processing_logger.log_file_operation("parse", file_path.name, "RestaurantDepot", False, str(e))
            raise
        
        return transactions

    async def _parse_sysco_single_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Parse a single Sysco invoice file."""
        transactions = []
        
        try:
            df = pd.read_csv(file_path)
            
            # Extract invoice number and date from header
            invoice_number = file_path.stem  # Use filename as invoice number
            
            # Find date in the data
            date_found = False
            for _, row in df.iterrows():
                if 'Date' in str(row).lower() or 'Invoice' in str(row).lower():
                    date_str = CSVUtils.extract_date_from_row(row)
                    if date_str:
                        transaction = {
                            'date': date_str,
                            'description': f"Sysco Invoice {invoice_number}",
                            'amount': CSVUtils.extract_total_amount(df),
                            'source_file': file_path.name
                        }
                        transactions.append(transaction)
                        date_found = True
                        break
            
            if not date_found:
                transaction = {
                    'date': datetime.now().strftime('%m/%d/%Y'),
                    'description': f"Sysco Invoice {invoice_number}",
                    'amount': CSVUtils.extract_total_amount(df),
                    'source_file': file_path.name
                }
                transactions.append(transaction)
                
        except Exception as e:
            processing_logger.log_file_operation("parse", file_path.name, "Sysco", False, str(e))
            raise
        
        return transactions 