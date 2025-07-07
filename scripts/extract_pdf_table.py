#!/usr/bin/env python3
"""
CLI tool for extracting merchant statement tables from PDF.
Usage:
  python extract_pdf_table.py --pdf path/to/file.pdf --vendor gg --year 2025 [--output path/to/output.csv]
"""
import argparse
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd

from app.utils.pdf_table_extractor import (
    extract_section_table_from_pdf_with_config,
    validate_pdf_format,
    load_vendor_config
)

def parse_args():
    parser = argparse.ArgumentParser(description="Extract merchant statement table from PDF.")
    parser.add_argument('--pdf', required=True, help='Path to PDF file')
    parser.add_argument('--vendor', required=True, help='Vendor key (e.g., gg, ar)')
    parser.add_argument('--year', required=True, type=int, help='Year to add to date column')
    parser.add_argument('--output', help='Output CSV path (default: same as PDF with .csv extension)')
    parser.add_argument('--no-validate', action='store_true', help='Skip PDF format validation')
    parser.add_argument('--verbose', action='store_true', help='Print detailed information')
    parser.add_argument('--debug', action='store_true', help='Print debug/diagnostic extraction info')
    
    return parser.parse_args()

def main():
    args = parse_args()
    
    # Validate inputs
    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        print(f"Error: PDF file not found: {pdf_path}")
        sys.exit(1)
    
    # Check if vendor configuration exists
    try:
        config = load_vendor_config(args.vendor)
        if args.verbose:
            print(f"Loaded configuration for vendor: {args.vendor}")
    except ValueError as e:
        print(f"Error: {e}")
        print(f"Available vendors: {list_available_vendors()}")
        sys.exit(1)
    
    # Validate PDF format if requested
    if not args.no_validate:
        if args.verbose:
            print("Validating PDF format...")
        
        is_valid, error_msg = validate_pdf_format(pdf_path, args.vendor)
        if not is_valid:
            print(f"Error: {error_msg}")
            sys.exit(1)
        
        if args.verbose:
            print("✓ PDF format validation passed")
    
    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = pdf_path.parent / f"{pdf_path.stem}_extracted.csv"
    
    try:
        # Extract table using configuration
        if args.verbose:
            print(f"Extracting table from {pdf_path}...")
            print(f"Adding year {args.year} to date column...")
        
        df = extract_section_table_from_pdf_with_config(
            pdf_path=pdf_path,
            vendor=args.vendor,
            year=args.year,
            output_csv=output_path,
            validate_format=not args.no_validate,
            debug=args.debug
        )
        
        # Print summary
        print(f"\n✓ Extraction completed successfully!")
        print(f"  PDF: {pdf_path}")
        print(f"  Vendor: {args.vendor}")
        print(f"  Output: {output_path}")
        print(f"  Rows extracted: {len(df)}")
        print(f"  Columns: {list(df.columns)}")
        
        if args.verbose:
            print(f"\nFirst 5 rows:")
            print(df.head().to_string(index=False))
        
    except Exception as e:
        print(f"Error during extraction: {e}")
        sys.exit(1)

def list_available_vendors():
    """List available vendor configurations."""
    config_dir = Path("config")
    vendors = []
    if config_dir.exists():
        for config_file in config_dir.glob("*.json"):
            vendor = config_file.stem
            try:
                config = load_vendor_config(vendor)
                if config.get("pdf_extraction", {}).get("enabled", False):
                    vendors.append(vendor)
            except:
                pass
    return vendors

if __name__ == "__main__":
    main() 