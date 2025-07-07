import re
import json
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
import pandas as pd
import fitz  # PyMuPDF
from datetime import datetime
from difflib import get_close_matches


def load_vendor_config(vendor: str) -> Dict[str, Any]:
    """Load vendor configuration from JSON file."""
    config_path = Path("config") / f"{vendor}.json"
    if not config_path.exists():
        raise ValueError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    return config


def validate_pdf_format(pdf_path: Path, vendor: str) -> Tuple[bool, str]:
    """
    Validate that PDF format matches vendor configuration.
    Returns: (is_valid, error_message)
    """
    try:
        config = load_vendor_config(vendor)
        pdf_config = config.get("pdf_extraction", {})
        
        if not pdf_config.get("enabled", False):
            return False, f"PDF extraction not enabled for vendor '{vendor}'"
        
        # Extract text and check for required section
        doc = fitz.open(pdf_path)
        text = "".join(page.get_text() for page in doc)
        doc.close()
        
        section_header = pdf_config.get("section_header")
        if not section_header:
            return False, f"No section header configured for vendor '{vendor}'"
        
        # Check if section exists
        if section_header not in text:
            if pdf_config.get("error_on_section_not_found", True):
                return False, f"Required section '{section_header}' not found in PDF"
            else:
                return True, "Section not found but error_on_section_not_found is False"
        
        # Check if expected columns are present in the text using flexible matching
        expected_columns = pdf_config.get("expected_columns", [])
        missing_columns = []
        found_columns = []
        
        # Extract lines from the section to check for columns
        section_start = text.find(section_header)
        section_text = text[section_start:section_start + 2000]  # Check first 2000 chars
        lines = section_text.splitlines()
        
        # Use flexible column matching
        norm_expected = [_normalize_colname(col) for col in expected_columns]
        
        for line in lines[:20]:  # Check first 20 lines
            parts = re.split(r'\s{2,}|\t|\|', line.strip())
            norm_parts = [_normalize_colname(p) for p in parts]
            
            for exp, n_exp in zip(expected_columns, norm_expected):
                if n_exp in norm_parts:
                    found_columns.append(exp)
                else:
                    # Try fuzzy matching
                    close = get_close_matches(n_exp, norm_parts, n=1, cutoff=0.7)
                    if close:
                        found_columns.append(exp)
        
        # Check which columns are missing
        for col in expected_columns:
            if col not in found_columns:
                missing_columns.append(col)
        
        if missing_columns and pdf_config.get("error_on_format_mismatch", True):
            return False, f"Expected columns not found in PDF: {missing_columns}. Found: {list(set(found_columns))}"
        
        return True, "PDF format validation passed"
        
    except Exception as e:
        return False, f"Error validating PDF format: {str(e)}"


def extract_section_table_from_pdf_with_config(
    pdf_path: Path,
    vendor: str,
    year: int,
    output_csv: Optional[Path] = None,
    validate_format: bool = True,
    debug: bool = False,
) -> pd.DataFrame:
    """
    Extract table from PDF using vendor configuration.
    Args:
        pdf_path: Path to PDF file
        vendor: Vendor key (e.g., 'gg', 'ar')
        year: Year to add to date column
        output_csv: Optional output CSV path
        validate_format: Whether to validate PDF format before extraction
        debug: Print debug/diagnostic extraction info
    Returns:
        DataFrame of extracted table
    """
    # Load vendor configuration
    config = load_vendor_config(vendor)
    pdf_config = config.get("pdf_extraction", {})
    
    if not pdf_config.get("enabled", False):
        raise ValueError(f"PDF extraction not enabled for vendor '{vendor}'")
    
    # Validate PDF format if requested
    if validate_format:
        is_valid, error_msg = validate_pdf_format(pdf_path, vendor)
        if not is_valid:
            raise ValueError(error_msg)
    
    # Extract table using configuration
    section_header = pdf_config["section_header"]
    columns = pdf_config["expected_columns"]
    
    df = extract_section_table_from_pdf(
        pdf_path=pdf_path,
        section_header=section_header,
        columns=columns,
        output_csv=None,  # We'll save after processing
        row_pattern=pdf_config.get("row_pattern"),
        stop_headers=pdf_config.get("stop_headers"),
        validate_rows=pdf_config.get("validate_rows", True),
        debug=debug
    )
    
    # Validate minimum rows
    min_rows = pdf_config.get("validation_rules", {}).get("min_rows", 1)
    if len(df) < min_rows:
        if pdf_config.get("error_on_no_valid_rows", True):
            raise ValueError(f"Extracted {len(df)} rows, minimum required: {min_rows}")
    
    # Add year to date column
    date_column = pdf_config.get("date_column", "Date")
    if date_column in df.columns:
        df = add_year_to_date_column(df, year, date_column)
    
    # Save to CSV if requested
    if output_csv:
        df.to_csv(output_csv, index=False)
    
    return df


def add_year_to_date_column(df: pd.DataFrame, year: int, date_col: str = 'Date') -> pd.DataFrame:
    """Add year to the Date column, converting MM/DD to YYYY-MM-DD."""
    def fix_date(val):
        val = str(val).strip()
        if '/' in val:
            try:
                m, d = val.split('/')
                return f"{year:04d}-{int(m):02d}-{int(d):02d}"
            except Exception:
                return val
        return val
    
    if date_col in df.columns:
        df[date_col] = df[date_col].apply(fix_date)
    return df


class TableMetadata:
    """Metadata about extracted table structure and format."""
    
    def __init__(self, columns: List[str]):
        self.columns = columns
        self.column_types = {}
        self.column_patterns = {}
        self.expected_row_length = len(columns)
        self.valid_rows = 0
        self.invalid_rows = 0
        self.total_rows = 0
        
    def analyze_column_types(self, df: pd.DataFrame):
        """Analyze data types and patterns for each column."""
        for col in self.columns:
            if col in df.columns:
                sample_values = df[col].dropna().head(100)
                if len(sample_values) > 0:
                    # Analyze patterns using standalone functions
                    self.column_patterns[col] = _detect_pattern(sample_values.iloc[0])
                    self.column_types[col] = _detect_type(sample_values)


def _normalize_colname(name: str) -> str:
    """Normalize column name for flexible matching: lowercase, strip, remove spaces and common OCR artifacts."""
    return re.sub(r'[^a-z0-9]', '', name.lower())


def _find_column_line(lines: List[str], expected_columns: List[str], debug: bool = False) -> Tuple[Optional[int], List[str], Dict[str, str]]:
    """
    Find the line index in lines that matches expected columns (flexible, fuzzy).
    Returns: (line_index, candidate_lines, mapping_dict)
    mapping_dict: {expected_col: matched_col_in_line}
    """
    norm_expected = [_normalize_colname(col) for col in expected_columns]
    candidate_lines = []
    for i, line in enumerate(lines):
        # Split line into candidate columns
        parts = re.split(r'\s{2,}|\t|\|', line.strip())
        norm_parts = [_normalize_colname(p) for p in parts]
        # Count matches
        matches = sum(1 for n in norm_expected if n in norm_parts)
        if matches >= max(len(norm_expected) - 1, 1):  # allow one missing
            # Try to map expected to actual
            mapping = {}
            for exp, n_exp in zip(expected_columns, norm_expected):
                if n_exp in norm_parts:
                    idx = norm_parts.index(n_exp)
                    mapping[exp] = parts[idx]
                else:
                    # Fuzzy match
                    close = get_close_matches(n_exp, norm_parts, n=1, cutoff=0.7)
                    if close:
                        idx = norm_parts.index(close[0])
                        mapping[exp] = parts[idx]
            if debug:
                print(f"[DEBUG] Candidate header line {i}: {line}")
                print(f"[DEBUG] Mapping: {mapping}")
            return i, candidate_lines, mapping
        candidate_lines.append(line)
    return None, candidate_lines, {}


def extract_section_table_from_pdf(
    pdf_path: Path,
    section_header: str,
    columns: List[str],
    output_csv: Optional[Path] = None,
    row_pattern: Optional[str] = None,
    stop_headers: Optional[List[str]] = None,
    skip_blank: bool = True,
    validate_rows: bool = True,
    debug: bool = False,
) -> pd.DataFrame:
    """
    Extract a table from a named section in a PDF and output as DataFrame or CSV.
    Args:
        pdf_path: Path to PDF file
        section_header: Section header to search for (e.g., 'SUMMARY OF MONETARY BATCHES')
        columns: List of column names for the table
        output_csv: Optional path to write CSV
        row_pattern: Optional regex to match table rows (if needed)
        stop_headers: Optional list of section headers that indicate the end of the table
        skip_blank: Skip blank/empty lines
        validate_rows: Whether to validate and clean rows based on metadata
        debug: Print diagnostic info
    Returns:
        DataFrame of the extracted table
    """
    # Extract raw text from PDF
    doc = fitz.open(pdf_path)
    text = "".join(page.get_text() for page in doc)
    doc.close()

    # Find section start
    section_start = text.find(section_header)
    if section_start == -1:
        raise ValueError(f"Section '{section_header}' not found in PDF.")
    section_text = text[section_start:]

    # Optionally stop at next section header
    if stop_headers:
        stops = [section_text.find(h) for h in stop_headers if section_text.find(h) > 0]
        if stops:
            section_text = section_text[:min(stops)]

    # Extract raw table data
    lines = section_text.splitlines()
    if debug:
        print(f"[DEBUG] Section header found at index {section_start}")
        print(f"[DEBUG] First 10 lines of section:")
        for l in lines[:10]:
            print(f"    {l}")

    # Find header line flexibly
    col_line_idx, candidate_lines, mapping = _find_column_line(lines, columns, debug=debug)
    if col_line_idx is None:
        # Suggest possible matches
        found_cols = set()
        for line in candidate_lines:
            parts = re.split(r'\s{2,}|\t|\|', line.strip())
            for p in parts:
                norm = _normalize_colname(p)
                for exp in columns:
                    if norm in _normalize_colname(exp) or _normalize_colname(exp) in norm:
                        found_cols.add(exp)
        raise ValueError(f"Could not find table header matching expected columns. Found possible columns: {sorted(found_cols)}")

    # Data lines start after col_line_idx
    data_lines = lines[col_line_idx+1:]

    # Parse rows with robust regex
    table = []
    for line in data_lines:
        if skip_blank and not line.strip():
            continue
        # Use regex to extract up to 5 fields (Gross, R&C, Net, Date, Ref)
        # Pattern: numbers (with optional minus, comma, decimal), then .00, then numbers, then date, then ref
        # Allow for missing Date/Ref
        m = re.match(r"\s*([\d,.-]+)\s+([\d,.-]+)\s+([\d,.-]+)\s+([\d]{1,2}/[\d]{2})?\s*([A-Za-z0-9]+)?", line)
        if m:
            row = list(m.groups())
            # Fill missing fields with empty string
            while len(row) < len(columns):
                row.append("")
            # Only accept rows with at least Gross, Net, Date
            if row[0] and row[2] and row[3]:
                table.append(row[:len(columns)])
            elif debug:
                print(f"[DEBUG] Skipped incomplete row: {row}")
        else:
            # fallback: whitespace split
            row = re.split(r"\s{2,}", line.strip())
            if len(row) < len(columns):
                row = re.split(r"\s+", line.strip())
            if len(row) == len(columns):
                table.append(row)
            elif debug:
                print(f"[DEBUG] Skipped unmatched row: {row}")
    
    df = pd.DataFrame(table, columns=columns)
    
    # Analyze and clean the table
    if validate_rows and len(df) > 0:
        metadata = TableMetadata(columns)
        metadata.analyze_column_types(df)
        # Clean and validate rows
        df = _clean_and_validate_table(df, metadata)
        if debug:
            print(f"[DEBUG] Table analysis: {metadata.valid_rows} valid rows, {metadata.invalid_rows} invalid rows removed")
    if output_csv:
        df.to_csv(output_csv, index=False)
    return df


def _clean_and_validate_table(df: pd.DataFrame, metadata: TableMetadata) -> pd.DataFrame:
    """Clean and validate table rows based on metadata."""
    valid_rows = []
    
    for idx, row in df.iterrows():
        if _is_valid_row(row, metadata):
            valid_rows.append(row)
            metadata.valid_rows += 1
        else:
            metadata.invalid_rows += 1
    
    metadata.total_rows = len(df)
    
    if valid_rows:
        return pd.DataFrame(valid_rows, columns=metadata.columns)
    else:
        return pd.DataFrame(columns=metadata.columns)


def _is_valid_row(row: pd.Series, metadata: TableMetadata) -> bool:
    """Check if a row is valid based on metadata patterns."""
    try:
        for col in metadata.columns:
            if col in row and col in metadata.column_patterns:
                value = str(row[col]).strip()
                if not _matches_pattern(value, metadata.column_patterns[col]):
                    return False
        return True
    except Exception:
        return False


def _detect_pattern(value: str) -> str:
    """Detect the pattern type of a value."""
    if not value:
        return "empty"
    
    # Date patterns
    if re.match(r"\d{1,2}/\d{1,2}", value):
        return "date"
    
    # Amount patterns
    if re.match(r"[\d,]+\.\d{2}", value) or re.match(r"[\d,]+\.\d{2}-", value):
        return "amount"
    
    # Reference patterns (alphanumeric)
    if re.match(r"[A-Za-z0-9]+", value):
        return "reference"
    
    # Default
    return "text"


def _detect_type(values: pd.Series) -> str:
    """Detect the data type of a column."""
    if values.empty:
        return "unknown"
    
    # Check if all values are dates
    date_count = 0
    amount_count = 0
    reference_count = 0
    
    for value in values:
        if re.match(r"\d{1,2}/\d{1,2}", str(value)):
            date_count += 1
        elif re.match(r"[\d,]+\.\d{2}", str(value)) or re.match(r"[\d,]+\.\d{2}-", str(value)):
            amount_count += 1
        elif re.match(r"[A-Za-z0-9]+", str(value)):
            reference_count += 1
    
    total = len(values)
    if date_count / total > 0.8:
        return "date"
    elif amount_count / total > 0.8:
        return "amount"
    elif reference_count / total > 0.8:
        return "reference"
    else:
        return "text"


def _matches_pattern(value: str, pattern: str) -> bool:
    """Check if a value matches the expected pattern."""
    if pattern == "empty":
        return not value or value.strip() == ""
    elif pattern == "date":
        return bool(re.match(r"\d{1,2}/\d{1,2}", value))
    elif pattern == "amount":
        return bool(re.match(r"[\d,]+\.\d{2}", value) or re.match(r"[\d,]+\.\d{2}-", value))
    elif pattern == "reference":
        return bool(re.match(r"[A-Za-z0-9]+", value))
    else:
        return True  # text pattern accepts anything


def analyze_table_structure(df: pd.DataFrame) -> Dict[str, Any]:
    """Analyze the structure of an extracted table."""
    analysis = {
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "columns": list(df.columns),
        "column_analysis": {},
        "data_quality": {}
    }
    
    for col in df.columns:
        col_analysis = {
            "non_null_count": df[col].notna().sum(),
            "null_count": df[col].isna().sum(),
            "unique_values": df[col].nunique(),
            "data_type": _detect_type(df[col].dropna()),
            "sample_values": df[col].dropna().head(3).tolist()
        }
        analysis["column_analysis"][col] = col_analysis
    
    # Overall data quality
    analysis["data_quality"] = {
        "completeness": df.notna().sum().sum() / (len(df) * len(df.columns)),
        "duplicate_rows": df.duplicated().sum(),
        "empty_rows": (df.isna().all(axis=1)).sum()
    }
    
    return analysis


# Example config for GG merchant statement
GG_CONFIG = {
    "section_header": "SUMMARY OF MONETARY BATCHES",
    "columns": ["Gross", "R&C", "Net", "Date", "Ref"],
    "validate_rows": True,
    # Optionally, add row_pattern or stop_headers if needed
}

# Example config for AR merchant statement (if different format)
AR_CONFIG = {
    "section_header": "SUMMARY OF MONETARY BATCHES",  # Same as GG for now
    "columns": ["Gross", "R&C", "Net", "Date", "Ref"],
    "validate_rows": True,
    # Can be customized if AR has different format
}

# Example config for a different vendor with different section name
EXAMPLE_VENDOR_CONFIG = {
    "section_header": "TRANSACTION SUMMARY",
    "columns": ["Date", "Description", "Amount", "Reference"],
    "stop_headers": ["END OF TRANSACTIONS", "SUMMARY"],  # Stop at these headers
    "validate_rows": True,
}

# Example config for a vendor with regex pattern matching
ADVANCED_VENDOR_CONFIG = {
    "section_header": "DAILY SETTLEMENTS",
    "columns": ["Date", "Batch", "Amount", "Fee", "Net"],
    "row_pattern": r"(\d{2}/\d{2}/\d{4})\s+(\w+)\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})",
    "stop_headers": ["TOTAL", "END OF REPORT"],
    "validate_rows": True,
} 