"""
Data processing service for Financial Data Processor.
"""
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from pathlib import Path
import asyncio
import dataclasses
from datetime import datetime, timedelta
from app.config import settings
from app.utils.logging import processing_logger
from app.utils.file_utils import FileUtils
from app.utils.csv_utils import CSVUtils
from app.models.file_models import ProcessingOptions
from dataclasses import dataclass
from app.config.source_mapping import mapping_manager
from app.utils.csv_loader import load_csv_robust


@dataclass
class ProcessingOptions:
    """Options for data processing."""
    year: Optional[int] = None
    month: Optional[int] = None
    include_metadata: bool = True
    force_reprocess: bool = False


@dataclass
class ProcessingResult:
    """Result of data processing operation."""
    success: bool
    files_processed: int
    output_files: List[str]
    processing_time: float = 0.0
    error_message: Optional[str] = None


def source_id_to_legacy_enum(source_id: str) -> str:
    """Convert source ID to legacy source enum format."""
    mapping = {
        "bankofamerica": "BankOfAmerica",
        "chase": "Chase", 
        "restaurantdepot": "RestaurantDepot",
        "sysco": "Sysco",
        "gg": "GG",
        "ar": "AR"
    }
    return mapping.get(source_id, source_id)


class DataProcessor:
    """Core data processing engine."""
    
    def __init__(self, data_dir: Optional[str] = None):
        """Initialize data processor."""
        self.data_dir = Path(data_dir) if data_dir else settings.data_path
        processing_logger.log_system_event("DataProcessor initialized", details={"data_dir": str(self.data_dir)})
    
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
            
            # 3. Group by month only
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
                processing_time=0.0,
                error_message=str(e)
            )
    
    async def _get_input_files(self, source: str) -> List[Path]:
        """Get all input files for a source."""
        # Use source ID directly for directory paths (not legacy enum)
        source_dir = self.data_dir / source / "input"
        if not source_dir.exists():
            return []
        
        # Handle both CSV and PDF files
        files = []
        for f in source_dir.iterdir():
            if f.is_file() and f.suffix.lower() in ['.csv', '.pdf']:
                files.append(f)
        
        return files
    
    async def _parse_files(self, files: List[Path], source: str) -> List[Dict[str, Any]]:
        """Parse files based on source type using configuration."""
        # Convert PDF files to CSV first
        processed_files = []
        for file_path in files:
            if file_path.suffix.lower() == '.pdf':
                from app.services.pdf_service import pdf_service
                csv_path = pdf_service.process_merchant_statement(file_path, source)
                if csv_path:
                    processed_files.append(csv_path)
                else:
                    processing_logger.log_system_event(
                        f"Failed to convert PDF to CSV: {file_path.name}", 
                        level="warning"
                    )
            else:
                processed_files.append(file_path)
        
        # Get the source mapping configuration
        mapping = mapping_manager.get_mapping(source)
        if not mapping:
            # Fall back to legacy parsing if no mapping found
            legacy_source = source_id_to_legacy_enum(source)
            if legacy_source == "BankOfAmerica":
                return await self._parse_boa_files(processed_files)
            elif legacy_source == "Chase":
                return await self._parse_chase_files(processed_files)
            elif legacy_source == "RestaurantDepot":
                return await self._parse_restaurant_depot_files(processed_files)
            elif legacy_source == "Sysco":
                return await self._parse_sysco_files(processed_files)
            elif legacy_source == "GG":
                return await self._parse_gg_files(processed_files)
            elif legacy_source == "AR":
                return await self._parse_ar_files(processed_files)
            else:
                raise ValueError(f"Unsupported source type: {source} (mapped to {legacy_source})")
        
        # Use configuration-based parsing for multiple files
        all_transactions = []
        for file_path in processed_files:
            file_transactions = await self._parse_with_config(file_path, mapping)
            all_transactions.extend(file_transactions)
        
        return all_transactions
    
    async def _parse_boa_files(self, files: List[Path]) -> List[Dict[str, Any]]:
        """Parse Bank of America CSV files."""
        all_transactions = []
        
        for file_path in files:
            try:
                # Use robust CSV parsing to handle mixed data types
                df = pd.read_csv(file_path, dtype=str, na_filter=False)
                
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
                # Use robust CSV parsing to handle mixed data types
                df = pd.read_csv(file_path, dtype=str, na_filter=False)
                
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
                # Use robust CSV parsing to handle mixed data types
                df = pd.read_csv(file_path, dtype=str, na_filter=False)
                
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
                # Use robust CSV parsing to handle mixed data types
                df = pd.read_csv(file_path, dtype=str, na_filter=False)
                
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
    
    async def _generate_monthly_files(self, source: str, year: int, grouped_data: Dict[str, List[Dict[str, Any]]], 
                                    options: ProcessingOptions) -> List[str]:
        """Generate monthly CSV files."""
        output_files = []
        
        for month_key, month_data in grouped_data.items():
            year_part, month_part = month_key.split('_')
            if int(year_part) != year:
                continue
            
            # Create output directory using source ID directly
            output_dir = self.data_dir / source / "output" / str(year)
            FileUtils.ensure_directory(output_dir)
            
            # Generate CSV content
            # Support both Pydantic v1 (dict) and v2 (model_dump)
            if hasattr(options, 'model_dump'):
                options_dict = options.model_dump()
            elif hasattr(options, 'dict'):
                options_dict = options.dict()
            else:
                options_dict = {}
            csv_content = CSVUtils.generate_csv_content(month_data, options_dict)
            
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
            # Use source ID directly for directory paths
            output_dir = self.data_dir / source / "output" / str(year)
            if not output_dir.exists():
                return {"total_files": 0, "total_records": 0, "total_amount": 0.0}
            
            total_files = 0
            total_records = 0
            total_amount = 0.0
            
            for csv_file in output_dir.iterdir():
                if csv_file.is_file() and csv_file.suffix.lower() == '.csv':
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
        """
        Process a single file for a specific source.
        Handles both PDF (extract then process) and CSV (process directly).
        For GG merchant PDFs: extract and rename/move the CSV as-is without modification.
        """
        start_time = datetime.now()
        
        if options is None:
            options = ProcessingOptions()
        
        try:
            processing_logger.log_processing_job(
                "system", source, "processing", 0.0, f"Starting processing for {source} file {filename}"
            )
            
            # 1. Get the specific file using source ID directly
            file_path = self.data_dir / source / "input" / filename
            
            if not file_path.exists():
                return ProcessingResult(
                    success=False,
                    files_processed=0,
                    output_files=[],
                    processing_time=0.0,
                    error_message=f"File {filename} not found for {source}"
                )
            
            # 2. If PDF file, extract to CSV first
            csv_path = file_path
            extracted_csv = None
            if filename.lower().endswith('.pdf'):
                processing_logger.log_system_event(
                    f"PDF file detected: {filename}, extracting data...", level="info"
                )
                from app.services.pdf_service import pdf_service
                
                extracted_csv = pdf_service.process_merchant_statement(file_path, source)
                if not extracted_csv or not extracted_csv.exists():
                    return ProcessingResult(
                        success=False,
                        files_processed=0,
                        output_files=[],
                        processing_time=(datetime.now() - start_time).total_seconds(),
                        error_message=f"Failed to extract data from PDF: {filename}"
                    )
                
                csv_path = extracted_csv
                processing_logger.log_system_event(
                    f"PDF extraction successful: {filename} -> {csv_path.name}", level="info"
                )
                
                # For GG merchant PDFs, just rename and move the extracted CSV as-is
                if source == "gg":
                    import pandas as pd
                    import shutil
                    
                    # Read the CSV to get the date from first row
                    df = pd.read_csv(csv_path)
                    if len(df) == 0:
                        return ProcessingResult(
                            success=False,
                            files_processed=0,
                            output_files=[],
                            processing_time=(datetime.now() - start_time).total_seconds(),
                            error_message=f"Extracted CSV is empty: {csv_path.name}"
                        )
                    
                    # Get year and month from FULL_DATE column
                    first_date = pd.to_datetime(df['FULL_DATE'].iloc[0])
                    year = first_date.year
                    month = first_date.month
                    
                    # Create output directory
                    output_dir = self.data_dir / source / "output" / str(year)
                    FileUtils.ensure_directory(output_dir)
                    
                    # Copy the file with the new name: MM_YYYY.csv
                    output_file = output_dir / f"{month:02d}_{year}.csv"
                    shutil.copy2(csv_path, output_file)
                    
                    processing_logger.log_file_operation(
                        "copy", output_file.name, source, True, 
                        f"Copied extracted CSV as-is from {csv_path.name}"
                    )
                    
                    processing_time = (datetime.now() - start_time).total_seconds()
                    processing_logger.log_processing_job(
                        "system", source, "completed", 100.0, 
                        f"Processing completed for {source} file {filename}"
                    )
                    
                    return ProcessingResult(
                        success=True,
                        files_processed=1,
                        output_files=[str(output_file)],
                        processing_time=processing_time
                    )
            
            # 3. Parse the CSV file (original or extracted)
            parsed_data = await self._parse_single_file(csv_path, source)
            processing_logger.log_system_event(
                f"[DEBUG] Parsed {len(parsed_data)} transactions from {csv_path.name}", level="info"
            )
            if parsed_data:
                processing_logger.log_system_event(
                    f"[DEBUG] Sample transaction: {parsed_data[0]}", level="info"
                )
            else:
                processing_logger.log_system_event(
                    f"[DEBUG] No transactions parsed from {csv_path.name}", level="warning"
                )
            
            # 4. Group by month only
            grouped_data = CSVUtils.group_transactions_by_month(parsed_data)
            processing_logger.log_system_event(
                f"[DEBUG] Grouping keys: {list(grouped_data.keys())}", level="info"
            )
            
            # 5. Generate monthly CSV files for all years found in the data
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
            import traceback
            error_details = traceback.format_exc()
            processing_logger.log_processing_job(
                "system", source, "error", 0.0, f"Processing failed for {source} file {filename}: {str(e)}\n{error_details}"
            )
            return ProcessingResult(
                success=False,
                files_processed=0,
                output_files=[],
                processing_time=0.0,
                error_message=str(e)
            )

    async def _parse_single_file(self, file_path: Path, source: str) -> List[Dict[str, Any]]:
        """Parse a single file based on source type using configuration."""
        # Get the source mapping configuration
        mapping = mapping_manager.get_mapping(source)
        processing_logger.log_system_event(
            f"Parsing file {file_path.name} for source {source}, mapping found: {mapping is not None}"
        )
        
        if not mapping:
            # Fall back to legacy parsing if no mapping found
            legacy_source = source_id_to_legacy_enum(source)
            processing_logger.log_system_event(
                f"Using legacy parser for {source} (mapped to {legacy_source})"
            )
            if legacy_source == "BankOfAmerica":
                return await self._parse_boa_single_file(file_path)
            elif legacy_source == "Chase":
                return await self._parse_chase_single_file(file_path)
            elif legacy_source == "RestaurantDepot":
                return await self._parse_restaurant_depot_single_file(file_path)
            elif legacy_source == "Sysco":
                return await self._parse_sysco_single_file(file_path)
            else:
                raise ValueError(f"Unsupported source type: {source} (mapped to {legacy_source})")
        
        # Use configuration-based parsing
        processing_logger.log_system_event(
            f"Using configuration-based parser for {source}"
        )
        return await self._parse_with_config(file_path, mapping)

    async def _parse_with_config(self, file_path: Path, mapping) -> List[Dict[str, Any]]:
        """Parse a file using source mapping configuration with robust CSV loading."""
        transactions = []

        def resolve_column(col_mapping, df_columns: list) -> Optional[str]:
            """Return the first matching column name (primary or alias)."""
            if col_mapping.source_column in df_columns:
                return col_mapping.source_column
            for alias in getattr(col_mapping, 'column_aliases', []):
                if alias in df_columns:
                    return alias
            return None

        try:
            # Build flexible required_columns: each entry is a list of alternatives
            # so csv_loader accepts any file where one candidate per group is present
            flex_required = []
            for cm in [mapping.date_mapping, mapping.description_mapping, mapping.amount_mapping]:
                candidates = [cm.source_column] + list(getattr(cm, 'column_aliases', []))
                flex_required.append(candidates)

            # Convert mapping to metadata dict for robust CSV loader
            metadata = {
                'required_columns': flex_required,
                'header_match': getattr(mapping, 'header_match', None),
                'min_row_fields': getattr(mapping, 'min_row_fields', None),
                'encoding': getattr(mapping, 'encoding', None)
            }

            # Use robust CSV loader with metadata
            df = load_csv_robust(
                file_path,
                metadata=metadata,
                logger_instance=processing_logger
            )
            
            # Log the actual columns found for debugging
            processing_logger.log_system_event(
                f"[DEBUG] CSV columns in {file_path.name}: {list(df.columns)}"
            )
            
            # Log the first few rows for debugging
            if len(df) > 0:
                first_row = df.iloc[0]
                processing_logger.log_system_event(
                    f"[DEBUG] First row data: {dict(first_row)}"
                )
            
            # Validate required columns — accept primary OR alias for each
            df_cols = list(df.columns)
            for candidates in flex_required:
                if not any(c in df_cols for c in candidates):
                    raise ValueError(
                        f"Missing required column in {file_path.name}. "
                        f"Expected one of {candidates}, found: {df_cols}"
                    )

            # Resolve actual column names (primary or alias)
            date_col = resolve_column(mapping.date_mapping, df_cols)
            desc_col = resolve_column(mapping.description_mapping, df_cols)
            amt_col  = resolve_column(mapping.amount_mapping, df_cols)

            if not date_col:
                raise ValueError(f"Date column not found. Expected '{mapping.date_mapping.source_column}' or aliases.")
            if not desc_col:
                raise ValueError(f"Description column not found. Expected '{mapping.description_mapping.source_column}' or aliases.")
            if not amt_col:
                raise ValueError(f"Amount column not found. Expected '{mapping.amount_mapping.source_column}' or aliases.")

            for idx, row in df.iterrows():
                try:
                    transaction = {
                        'source_file': file_path.name
                    }

                    # Map required columns using resolved names
                    date_value        = str(row[date_col])
                    description_value = str(row[desc_col])
                    amount_value      = CSVUtils.clean_amount(row[amt_col])

                    transaction[mapping.date_mapping.target_field]        = date_value
                    transaction[mapping.description_mapping.target_field] = description_value
                    transaction[mapping.amount_mapping.target_field]      = amount_value

                    # Map optional columns if they exist in the data
                    for opt_mapping in mapping.optional_mappings:
                        opt_col = resolve_column(opt_mapping, df_cols)
                        if opt_col:
                            value = row[opt_col]
                            if opt_mapping.mapping_type == "amount":
                                transaction[opt_mapping.target_field] = CSVUtils.clean_amount(value)
                            else:
                                transaction[opt_mapping.target_field] = str(value)
                    
                    # Log the first transaction for debugging
                    if idx == 0:
                        processing_logger.log_system_event(
                            f"[DEBUG] First transaction: {transaction}"
                        )
                    
                    transactions.append(transaction)
                except Exception as e:
                    processing_logger.log_system_event(
                        f"Error parsing row {idx} in {file_path.name}: {str(e)}", level="warning"
                    )
                    continue
                    
        except Exception as e:
            processing_logger.log_file_operation("parse", file_path.name, mapping.source_id, False, str(e))
            raise
        
        return transactions

    async def _parse_boa_single_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Parse a single Bank of America CSV file."""
        transactions = []
        
        try:
            # Use robust CSV parsing to handle mixed data types
            df = pd.read_csv(file_path, dtype=str, na_filter=False)
            
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
        """Parse a single Chase CSV file with malformed data structure."""
        transactions = []
        
        try:
            # Use robust CSV parsing to handle mixed data types
            df = pd.read_csv(file_path, dtype=str, na_filter=False)
            
            # Chase files have malformed data where the actual transaction data
            # is in the "Description" column instead of "Posting Date"
            # The "Posting Date" column contains dates, but "Description" contains
            # the complex transaction data that should be parsed for dates
            
            if 'Posting Date' not in df.columns or 'Description' not in df.columns or 'Amount' not in df.columns:
                raise ValueError(f"Missing required columns in {file_path.name}")
            
            for _, row in df.iterrows():
                try:
                    # Extract date from the "Posting Date" column (this contains actual dates)
                    date_str = str(row['Posting Date']).strip()
                    
                    # Extract description from the "Description" column (contains complex transaction data)
                    description_data = str(row['Description']).strip()
                    
                    # Try to extract a meaningful description from the complex transaction data
                    description = self._extract_chase_description(description_data)
                    
                    # Extract amount from the "Amount" column
                    amount = CSVUtils.clean_amount(row['Amount'])
                    
                    transaction = {
                        'date': date_str,
                        'description': description,
                        'amount': amount,
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
    
    def _extract_chase_description(self, description_data: str) -> str:
        """Extract meaningful description from Chase transaction data."""
        try:
            # Look for company name in the transaction data
            if 'ORIG CO NAME:' in description_data:
                # Extract company name
                start = description_data.find('ORIG CO NAME:') + 13
                end = description_data.find(' ', start)
                if end > start:
                    company_name = description_data[start:end].strip()
                    return company_name
            
            # Look for individual name
            if 'IND NAME:' in description_data:
                start = description_data.find('IND NAME:') + 9
                end = description_data.find(' ', start)
                if end > start:
                    individual_name = description_data[start:end].strip()
                    return individual_name
            
            # If no structured data found, take first 50 characters
            return description_data[:50].strip()
            
        except Exception:
            # Fallback to first 50 characters
            return description_data[:50].strip()

    async def _parse_restaurant_depot_single_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Parse a single Restaurant Depot invoice file."""
        transactions = []
        
        try:
            # Use robust CSV parsing to handle mixed data types
            df = pd.read_csv(file_path, dtype=str, na_filter=False)
            
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
            # Use robust CSV parsing to handle mixed data types
            df = pd.read_csv(file_path, dtype=str, na_filter=False)
            
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

    async def _parse_gg_files(self, files: List[Path]) -> List[Dict[str, Any]]:
        """Parse GG merchant statement files."""
        all_transactions = []
        
        for file_path in files:
            try:
                # Use robust CSV parsing to handle mixed data types
                df = pd.read_csv(file_path, dtype=str, na_filter=False)
                
                # Validate required columns
                required_columns = ['Date', 'Description', 'Amount']
                if not all(col in df.columns for col in required_columns):
                    raise ValueError(f"Missing required columns in {file_path.name}")
                
                for _, row in df.iterrows():
                    try:
                        transaction = {
                            'date': str(row['Date']),
                            'description': str(row['Description']),
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
                processing_logger.log_file_operation("parse", file_path.name, "GG", False, str(e))
                raise
        
        return all_transactions

    async def _parse_ar_files(self, files: List[Path]) -> List[Dict[str, Any]]:
        """Parse AR merchant statement files."""
        all_transactions = []
        
        for file_path in files:
            try:
                # Use robust CSV parsing to handle mixed data types
                df = pd.read_csv(file_path, dtype=str, na_filter=False)
                
                # Validate required columns
                required_columns = ['Date', 'Description', 'Amount']
                if not all(col in df.columns for col in required_columns):
                    raise ValueError(f"Missing required columns in {file_path.name}")
                
                for _, row in df.iterrows():
                    try:
                        transaction = {
                            'date': str(row['Date']),
                            'description': str(row['Description']),
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
                processing_logger.log_file_operation("parse", file_path.name, "AR", False, str(e))
                raise
        
        return all_transactions

    async def _parse_gg_single_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Parse a single GG merchant statement file."""
        transactions = []
        
        try:
            # Use robust CSV parsing to handle mixed data types
            df = pd.read_csv(file_path, dtype=str, na_filter=False)
            
            # Validate required columns
            required_columns = ['Date', 'Description', 'Amount']
            if not all(col in df.columns for col in required_columns):
                raise ValueError(f"Missing required columns in {file_path.name}")
            
            for _, row in df.iterrows():
                try:
                    transaction = {
                        'date': str(row['Date']),
                        'description': str(row['Description']),
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
            processing_logger.log_file_operation("parse", file_path.name, "GG", False, str(e))
            raise
        
        return transactions

    async def _parse_ar_single_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Parse a single AR merchant statement file."""
        transactions = []
        
        try:
            # Use robust CSV parsing to handle mixed data types
            df = pd.read_csv(file_path, dtype=str, na_filter=False)
            
            # Validate required columns
            required_columns = ['Date', 'Description', 'Amount']
            if not all(col in df.columns for col in required_columns):
                raise ValueError(f"Missing required columns in {file_path.name}")
            
            for _, row in df.iterrows():
                try:
                    transaction = {
                        'date': str(row['Date']),
                        'description': str(row['Description']),
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
            processing_logger.log_file_operation("parse", file_path.name, "AR", False, str(e))
            raise
        
        return transactions 