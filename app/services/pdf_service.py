"""
PDF processing service for Financial Data Processor.
Handles PDF to CSV conversion for merchant statements.
"""
import os
import tempfile
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any
import pandas as pd
import logging

from app.utils.logging import processing_logger
from app.utils.pdf_table_extractor import extract_section_table_from_pdf, GG_CONFIG, AR_CONFIG, extract_section_table_from_pdf_with_config, validate_pdf_format, load_vendor_config


class PDFService:
    """Service for processing PDF files and converting them to CSV."""
    
    def __init__(self):
        self.logger = processing_logger
    
    def convert_pdf_to_csv(self, pdf_path: Path, output_path: Optional[Path] = None) -> Optional[Path]:
        """
        Convert a PDF file to CSV format.
        
        Args:
            pdf_path: Path to the PDF file
            output_path: Optional output path for CSV file
            
        Returns:
            Path to the generated CSV file, or None if conversion failed
        """
        try:
            if not pdf_path.exists():
                self.logger.log_system_event(f"PDF file not found: {pdf_path}", level="error")
                return None
            
            # Generate output path if not provided
            if output_path is None:
                output_path = pdf_path.parent / f"{pdf_path.stem}.csv"
            
            # Try different PDF to CSV conversion methods
            csv_path = self._try_pdfplumber_conversion(pdf_path, output_path)
            if csv_path:
                return csv_path
            
            csv_path = self._try_pymupdf_conversion(pdf_path, output_path)
            if csv_path:
                return csv_path
            
            csv_path = self._try_tabula_conversion(pdf_path, output_path)
            if csv_path:
                return csv_path
            
            self.logger.log_system_event(f"All PDF conversion methods failed for {pdf_path}", level="error")
            return None
            
        except Exception as e:
            self.logger.log_system_event(f"Error converting PDF {pdf_path}: {str(e)}", level="error")
            return None
    
    def _try_pdfplumber_conversion(self, pdf_path: Path, output_path: Path) -> Optional[Path]:
        """Try converting PDF using pdfplumber library."""
        try:
            import pdfplumber
            
            with pdfplumber.open(pdf_path) as pdf:
                all_tables = []
                
                for page in pdf.pages:
                    tables = page.extract_tables()
                    if tables:
                        all_tables.extend(tables)
                
                if all_tables:
                    # Combine all tables into one DataFrame
                    all_rows = []
                    for table in all_tables:
                        if table:
                            all_rows.extend(table)
                    
                    if all_rows:
                        # Create DataFrame and save as CSV
                        df = pd.DataFrame(all_rows[1:], columns=all_rows[0])
                        df.to_csv(output_path, index=False)
                        
                        self.logger.log_system_event(
                            f"Successfully converted PDF to CSV using pdfplumber: {output_path}", 
                            level="info"
                        )
                        return output_path
            
            return None
            
        except ImportError:
            self.logger.log_system_event("pdfplumber not available", level="warning")
            return None
        except Exception as e:
            self.logger.log_system_event(f"pdfplumber conversion failed: {str(e)}", level="warning")
            return None
    
    def _try_pymupdf_conversion(self, pdf_path: Path, output_path: Path) -> Optional[Path]:
        """Try converting PDF using PyMuPDF (fitz) library."""
        try:
            import fitz
            
            doc = fitz.open(pdf_path)
            all_tables = []
            
            for page in doc:
                # Extract text and try to parse as table
                text = page.get_text()
                lines = text.split('\n')
                
                # Simple table parsing
                table_data = []
                for line in lines:
                    if line.strip():
                        # Split by common delimiters
                        row = [cell.strip() for cell in line.split('\t')]
                        if len(row) == 1:
                            row = [cell.strip() for cell in line.split('  ') if cell.strip()]
                        table_data.append(row)
                
                if table_data:
                    all_tables.extend(table_data)
            
            doc.close()
            
            if all_tables:
                # Try to identify headers and data
                if len(all_tables) > 1:
                    # Assume first row is header
                    headers = all_tables[0]
                    data_rows = all_tables[1:]
                    
                    # Create DataFrame
                    df = pd.DataFrame(data_rows, columns=headers)
                    df.to_csv(output_path, index=False)
                    
                    self.logger.log_system_event(
                        f"Successfully converted PDF to CSV using PyMuPDF: {output_path}", 
                        level="info"
                    )
                    return output_path
            
            return None
            
        except ImportError:
            self.logger.log_system_event("PyMuPDF not available", level="warning")
            return None
        except Exception as e:
            self.logger.log_system_event(f"PyMuPDF conversion failed: {str(e)}", level="warning")
            return None
    
    def _try_tabula_conversion(self, pdf_path: Path, output_path: Path) -> Optional[Path]:
        """Try converting PDF using tabula-py library (requires Java)."""
        try:
            import tabula
            
            # Read all tables from PDF
            tables = tabula.read_pdf(str(pdf_path), pages='all')
            
            if tables:
                # Combine all tables
                combined_df = pd.concat(tables, ignore_index=True)
                combined_df.to_csv(output_path, index=False)
                
                self.logger.log_system_event(
                    f"Successfully converted PDF to CSV using tabula: {output_path}", 
                    level="info"
                )
                return output_path
            
            return None
            
        except ImportError:
            self.logger.log_system_event("tabula-py not available", level="warning")
            return None
        except Exception as e:
            self.logger.log_system_event(f"tabula conversion failed: {str(e)}", level="warning")
            return None
    
    def extract_text_from_pdf(self, pdf_path: Path) -> Optional[str]:
        """Extract text content from PDF file."""
        try:
            import fitz
            
            doc = fitz.open(pdf_path)
            text = ""
            
            for page in doc:
                text += page.get_text()
            
            doc.close()
            return text
            
        except ImportError:
            self.logger.log_system_event("PyMuPDF not available for text extraction", level="warning")
            return None
        except Exception as e:
            self.logger.log_system_event(f"Text extraction failed: {str(e)}", level="error")
            return None
    
    def validate_pdf_content(self, pdf_path: Path) -> Dict[str, Any]:
        """
        Validate PDF content and return metadata.
        
        Returns:
            Dictionary with validation results and metadata
        """
        try:
            result = {
                "is_valid": False,
                "pages": 0,
                "has_tables": False,
                "has_text": False,
                "file_size": 0,
                "error": None
            }
            
            if not pdf_path.exists():
                result["error"] = "File not found"
                return result
            
            result["file_size"] = pdf_path.stat().st_size
            
            # Try to extract text
            text = self.extract_text_from_pdf(pdf_path)
            if text and text.strip():
                result["has_text"] = True
                result["is_valid"] = True
            
            # Try to extract tables
            try:
                import pdfplumber
                with pdfplumber.open(pdf_path) as pdf:
                    result["pages"] = len(pdf.pages)
                    
                    for page in pdf.pages:
                        tables = page.extract_tables()
                        if tables:
                            result["has_tables"] = True
                            break
            except:
                pass
            
            return result
            
        except Exception as e:
            return {
                "is_valid": False,
                "pages": 0,
                "has_tables": False,
                "has_text": False,
                "file_size": 0,
                "error": str(e)
            }
    
    def extract_vendor_section_table_to_csv(self, pdf_path: Path, vendor: str, year: int, output_csv: Optional[Path] = None) -> Optional[Path]:
        """
        Extract a vendor-specific section table from a PDF and write to CSV.
        Args:
            pdf_path: Path to PDF file
            vendor: Vendor key (e.g., 'gg', 'ar')
            year: Year to add to date column
            output_csv: Optional path to write CSV
        Returns:
            Path to CSV or None
        """
        try:
            if output_csv is None:
                output_path = pdf_path.parent / f"{pdf_path.stem}_extracted.csv"
            else:
                output_path = output_csv
            
            # Validate PDF format first
            is_valid, error_msg = validate_pdf_format(pdf_path, vendor)
            if not is_valid:
                raise ValueError(f"PDF format validation failed: {error_msg}")
            
            # Extract table using configuration
            df = extract_section_table_from_pdf_with_config(
                pdf_path=pdf_path,
                vendor=vendor,
                year=year,
                output_csv=output_path,
                validate_format=True
            )
            
            return output_path
            
        except Exception as e:
            self.logger.log_system_event(f"Error extracting vendor table: {e}", level="error")
            return None

    def process_merchant_statement(self, pdf_path: Path, source: str, year: int) -> Optional[Path]:
        """
        Process a merchant statement PDF and convert to CSV.
        Args:
            pdf_path: Path to PDF file
            source: Source identifier (e.g., 'gg', 'ar')
            year: Year to add to date column
        Returns:
            Path to generated CSV or None
        """
        try:
            # Validate that PDF extraction is enabled for this vendor
            config = load_vendor_config(source)
            pdf_config = config.get("pdf_extraction", {})
            
            if not pdf_config.get("enabled", False):
                self.logger.log_system_event(f"PDF extraction not enabled for vendor '{source}'", level="warning")
                return None
            
            # Extract table using vendor configuration
            csv_path = self.extract_vendor_section_table_to_csv(pdf_path, source, year)
            
            if csv_path:
                self.logger.log_system_event(f"Successfully processed merchant statement: {csv_path}", level="info")
                return csv_path
            else:
                self.logger.log_system_event(f"Failed to process merchant statement: {pdf_path}", level="error")
                return None
                
        except Exception as e:
            self.logger.log_system_event(f"Error processing merchant statement: {e}", level="error")
            return None


# Global PDF service instance
pdf_service = PDFService() 