#!/usr/bin/env python3
"""
Extract "SUMMARY OF MONETARY BATCHES" table from GG merchant statement PDFs.

This script extracts batch transaction data from monthly merchant summary PDFs
and exports it to CSV format.

Usage:
    python extract_gg_merchant_batches.py <pdf_file> [output_csv]
    
Example:
    python extract_gg_merchant_batches.py data/gg/merchant/Jan2025.pdf data/gg/merchant/Jan2025_batches.csv
"""

import sys
import csv
import re
from pathlib import Path
import pdfplumber
from datetime import datetime


def extract_monetary_batches(pdf_path):
    """
    Extract the SUMMARY OF MONETARY BATCHES table from a GG merchant PDF.
    Handles tables that span multiple pages including continuation pages.
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        list: List of dictionaries containing batch data
    """
    batches = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            text = page.extract_text()
            
            if not text:
                continue
            
            lines = text.split('\n')
            
            # Check if this page contains the monetary batches table or continuation
            has_batches_section = ('SUMMARY OF MONETARY BATCHES' in text or 
                                  'BATCHES - CONTINUED' in text)
            
            if not has_batches_section:
                # Check if there are batch rows at the start of the page (continuation from previous page)
                # This handles rows that appear before the official "CONTINUED" header
                for i, line in enumerate(lines[:10]):  # Check first 10 lines
                    # Try to match a batch row pattern
                    pattern = r'([\d,.-]+)\s+([\d,.-]+)\s+([\d,.-]+)\s+(\d{1,2}/\d{2})\s+(\S+)'
                    match = re.match(pattern, line.strip())
                    if match:
                        # Found continuation rows at the top of the page
                        has_batches_section = True
                        break
            
            if has_batches_section:
                # Process this page for batch data
                in_table = False
                header_found = False
                
                for line_num, line in enumerate(lines):
                    line_stripped = line.strip()
                    
                    # Detect table header (original or continuation)
                    if 'GROSS' in line and 'R&C' in line and 'NET' in line and 'DATE' in line and 'REF' in line:
                        in_table = True
                        header_found = True
                        continue
                    
                    # Skip the "BATCHES" subheader line
                    if line_stripped == 'BATCHES':
                        continue
                    
                    # Skip section headers
                    if ('SUMMARY OF MONETARY BATCHES' in line_stripped or
                        'BATCHES - CONTINUED' in line_stripped):
                        continue
                    
                    # Detect end of table on current page
                    # Stop at page footer or new section
                    if in_table and ('about:blank' in line_stripped or 
                                    'PRIORITY PAYMENTS' in line_stripped or
                                    'CUSTOMER SERVICE TEL' in line_stripped):
                        # Don't stop completely, just exit table for this page
                        in_table = False
                        header_found = False
                        continue
                    
                    # Parse table rows (whether header was found on this page or previous page)
                    # If we haven't found a header yet, we might be in continuation rows
                    should_parse = (in_table and header_found) or (not header_found and line_num < 10)
                    
                    if should_parse and line_stripped:
                        # Parse the line with regex to handle amounts with negative signs
                        # Pattern: GROSS R&C NET DATE REF
                        # Example: 3,889.16 .00 3,889.16 1/01 98000141449
                        # Example with negative: 552.65- .00 552.65- 1/01 011925MOADJ
                        
                        pattern = r'([\d,.-]+)\s+([\d,.-]+)\s+([\d,.-]+)\s+(\d{1,2}/\d{2})\s+(\S+)'
                        match = re.match(pattern, line_stripped)
                        
                        if match:
                            gross, r_and_c, net, date, ref = match.groups()
                            
                            # Clean up amounts (remove commas, handle negative)
                            def clean_amount(amt):
                                # Check if negative (ends with -)
                                is_negative = amt.endswith('-')
                                # Remove commas and negative sign
                                cleaned = amt.replace(',', '').replace('-', '')
                                # Convert to float and apply negative if needed
                                value = float(cleaned)
                                return -value if is_negative else value
                            
                            batch = {
                                'GROSS': clean_amount(gross),
                                'R&C': clean_amount(r_and_c),
                                'NET': clean_amount(net),
                                'DATE': date,
                                'REF': ref  # Keep as string
                            }
                            batches.append(batch)
    
    return batches


def determine_year_from_filename(pdf_path):
    """
    Try to determine the year from the filename or PDF path.
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        str: Year (e.g., "2025") or None
    """
    # Try to extract year from filename like "Jan2025.pdf"
    filename = Path(pdf_path).stem
    year_match = re.search(r'(20\d{2})', filename)
    if year_match:
        return year_match.group(1)
    
    # Default to current year if not found
    return str(datetime.now().year)


def add_full_date(batches, pdf_path):
    """
    Convert month/day dates to full dates with year.
    
    Args:
        batches (list): List of batch dictionaries
        pdf_path (str): Path to the PDF (used to determine year)
        
    Returns:
        list: Updated batches with FULL_DATE field
    """
    year = determine_year_from_filename(pdf_path)
    
    for batch in batches:
        date_str = batch['DATE']  # Format: M/DD
        month, day = date_str.split('/')
        batch['FULL_DATE'] = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    
    return batches


def export_to_csv(batches, output_path):
    """
    Export batches to CSV file with uppercase column names.
    
    Args:
        batches (list): List of batch dictionaries
        output_path (str): Path to output CSV file
    """
    if not batches:
        print("No batches found to export")
        return
    
    # Column names exactly as they appear in the PDF
    fieldnames = ['FULL_DATE', 'DATE', 'GROSS', 'R&C', 'NET', 'REF']
    
    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(batches)
    
    print(f"✓ Exported {len(batches)} batches to {output_path}")


def main():
    """Main execution function."""
    if len(sys.argv) < 2:
        print("Usage: python extract_gg_merchant_batches.py <pdf_file> [output_csv]")
        print("\nExample:")
        print("  python extract_gg_merchant_batches.py data/gg/merchant/Jan2025.pdf")
        print("  python extract_gg_merchant_batches.py data/gg/merchant/Jan2025.pdf output.csv")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    # Validate PDF exists
    if not Path(pdf_path).exists():
        print(f"Error: PDF file not found: {pdf_path}")
        sys.exit(1)
    
    # Determine output path
    if len(sys.argv) >= 3:
        output_path = sys.argv[2]
    else:
        # Auto-generate output filename
        pdf_stem = Path(pdf_path).stem
        output_dir = Path(pdf_path).parent
        output_path = output_dir / f"{pdf_stem}_batches.csv"
    
    print(f"Processing: {pdf_path}")
    print(f"Output: {output_path}")
    print()
    
    # Extract batches
    try:
        batches = extract_monetary_batches(pdf_path)
        
        if not batches:
            print("⚠ Warning: No batches found in the PDF")
            print("  Make sure the PDF contains 'SUMMARY OF MONETARY BATCHES' section")
            sys.exit(1)
        
        # Add full dates
        batches = add_full_date(batches, pdf_path)
        
        # Display summary
        print(f"Found {len(batches)} batch transactions")
        print()
        print("Sample (first 5 batches):")
        print("-" * 80)
        for i, batch in enumerate(batches[:5], 1):
            print(f"{i}. {batch['FULL_DATE']} | ${batch['NET']:>10.2f} | Ref: {batch['REF']}")
        
        if len(batches) > 5:
            print(f"... and {len(batches) - 5} more")
        print("-" * 80)
        print()
        
        # Calculate totals
        total_gross = sum(b['GROSS'] for b in batches)
        total_net = sum(b['NET'] for b in batches)
        total_rc = sum(b['R&C'] for b in batches)
        
        print("Totals:")
        print(f"  Gross: ${total_gross:,.2f}")
        print(f"  R&C:   ${total_rc:,.2f}")
        print(f"  Net:   ${total_net:,.2f}")
        print()
        
        # Export to CSV
        export_to_csv(batches, output_path)
        
    except Exception as e:
        print(f"Error processing PDF: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
