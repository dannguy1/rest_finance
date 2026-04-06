# GG Merchant Batch Extractor

## Overview

This script extracts the "SUMMARY OF MONETARY BATCHES" table from GG monthly merchant statement PDFs and exports the data to CSV format.

## Requirements

- Python 3.7+
- pdfplumber library

Install dependencies:
```bash
pip install pdfplumber
```

## Usage

### Basic Usage (auto-generate output filename)
```bash
python scripts/extract_gg_merchant_batches.py data/gg/merchant/Jan2025.pdf
```

This will create: `data/gg/merchant/Jan2025_batches.csv`

### Specify Output Filename
```bash
python scripts/extract_gg_merchant_batches.py data/gg/merchant/Jan2025.pdf output/batches_january.csv
```

### Make it Executable (Linux/Mac)
```bash
chmod +x scripts/extract_gg_merchant_batches.py
./scripts/extract_gg_merchant_batches.py data/gg/merchant/Jan2025.pdf
```

## Output Format

The script generates a CSV file with the following columns:

| Column     | Description                          | Example         |
|------------|--------------------------------------|-----------------|
| full_date  | Full date (YYYY-MM-DD)              | 2025-01-15      |
| date       | Original month/day from PDF         | 1/15            |
| gross      | Gross amount                        | 3889.16         |
| r_and_c    | Returns & Chargebacks               | 0.00            |
| net        | Net amount (gross - r_and_c)        | 3889.16         |
| reference  | Transaction reference number        | 98000141449     |

## Features

- **Automatic Year Detection**: Extracts year from PDF filename (e.g., "Jan2025.pdf")
- **Handles Negative Amounts**: Correctly processes adjustments and reversals (e.g., `552.65-`)
- **Multi-Page Support**: Extracts batches from "SUMMARY OF MONETARY BATCHES - CONTINUED" sections
- **Data Validation**: Calculates and displays totals for verification
- **Summary Display**: Shows sample records and totals before saving

## Example Output

```
Processing: data/gg/merchant/Jan2025.pdf
Output: data/gg/merchant/Jan2025_batches.csv

Found 51 batch transactions

Sample (first 5 batches):
--------------------------------------------------------------------------------
1. 2025-01-01 | $   3889.16 | Ref: 98000141449
2. 2025-01-01 | $    237.09 | Ref: 00100101849
3. 2025-01-01 | $   -552.65 | Ref: 011925MOADJ
4. 2025-01-02 | $   6376.09 | Ref: 98000241205
5. 2025-01-02 | $    167.49 | Ref: 00100102516
... and 46 more
--------------------------------------------------------------------------------

Totals:
  Gross: $79,071.36
  R&C:   $0.00
  Net:   $79,071.36

✓ Exported 51 batches to data/gg/merchant/Jan2025_batches.csv
```

## CSV Sample

```csv
full_date,date,gross,r_and_c,net,reference
2025-01-01,1/01,3889.16,0.0,3889.16,98000141449
2025-01-01,1/01,237.09,0.0,237.09,00100101849
2025-01-01,1/01,-552.65,0.0,-552.65,011925MOADJ
2025-01-02,1/02,6376.09,0.0,6376.09,98000241205
```

## Processing Multiple Files

You can process multiple PDFs using a loop:

### Bash (Linux/Mac)
```bash
for pdf in data/gg/merchant/*.pdf; do
    python scripts/extract_gg_merchant_batches.py "$pdf"
done
```

### PowerShell (Windows)
```powershell
Get-ChildItem data/gg/merchant/*.pdf | ForEach-Object {
    python scripts/extract_gg_merchant_batches.py $_.FullName
}
```

## Troubleshooting

### No batches found
- Ensure the PDF contains "SUMMARY OF MONETARY BATCHES" section
- Check that the PDF is not password protected or corrupted
- Verify the PDF is a GG merchant statement (not a different document type)

### Incorrect year in dates
- The script extracts the year from the filename (e.g., "Jan**2025**.pdf")
- If your filename doesn't include the year, it defaults to the current year
- Rename the file to include the year, or edit the year manually in the CSV

### Missing transactions
- Compare the CSV total with the PDF totals
- Check if there are additional pages with "CONTINUED" sections
- Verify the data visually in the PDF

## Integration with Main Application

To integrate this into the main financial processing workflow:

1. **Create a new source type** for GG merchant statements
2. **Add to source_mapping.py**: Define column mappings
3. **Update processing_service.py**: Call this script during processing
4. **Add validation**: Verify totals match the PDF summary

Example integration:
```python
# In processing_service.py
if source == "gg_merchant":
    # Extract batches from PDF
    csv_file = extract_gg_merchant_batches(pdf_path)
    # Process the CSV file
    result = process_csv(csv_file, source_config)
```

## Notes

- The script preserves both the original date format (M/DD) and adds a full ISO date (YYYY-MM-DD)
- Negative amounts (adjustments/reversals) are properly handled with a leading minus sign
- The R&C column is typically 0.00 for most batches
- Reference numbers uniquely identify each batch transaction

## Author

Created for the Garlic & Chives Financial Data Processor
Last Updated: November 2025
