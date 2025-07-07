# Financial Data Processor - Management Scripts

This directory contains management scripts for starting, stopping, and monitoring the Financial Data Processor backend and frontend services.

## Scripts Overview

### Backend Management
- **`manage_backend.sh`** - Manages the FastAPI backend service
- **`backend.env`** - Backend configuration file

### Frontend Management  
- **`manage_frontend.sh`** - Manages the static frontend server
- **`frontend.env`** - Frontend configuration file

## Quick Start

1. **Start Backend:**
   ```bash
   ./scripts/manage_backend.sh start -b
   ```

2. **Start Frontend:**
   ```bash
   ./scripts/manage_frontend.sh start -b
   ```

3. **Check Status:**
   ```bash
   ./scripts/manage_backend.sh status
   ./scripts/manage_frontend.sh status
   ```

4. **View Logs:**
   ```bash
   ./scripts/manage_backend.sh logs
   ./scripts/manage_frontend.sh logs
   ```

5. **Stop Services:**
   ```bash
   ./scripts/manage_backend.sh stop
   ./scripts/manage_frontend.sh stop
   ```

## Configuration

Both scripts use environment configuration files to avoid hardcoded values:

### Backend Configuration (`backend.env`)
```bash
# Service Configuration
SERVICE_NAME=finance-backend
APP_MODULE=app.api.main:app

# Server Configuration  
HOST=0.0.0.0
PORT=8000
RELOAD=true
LOG_LEVEL=info

# Python Configuration
PYTHON_PATH=python3
# PYTHON_PATH=venv/bin/python  # Uncomment to use virtual environment

# File Paths
PID_FILE=logs/finance-backend.pid
LOG_FILE=logs/finance-backend.log
```

### Frontend Configuration (`frontend.env`)
```bash
# Service Configuration
SERVICE_NAME=finance-frontend
FRONTEND_DIR=app/static

# Server Configuration
HOST=0.0.0.0
PORT=3000

# File Paths
PID_FILE=logs/finance-frontend.pid
LOG_FILE=logs/finance-frontend.log
```

## Commands

Both scripts support the same commands:

- `start` - Start the service
- `stop` - Stop the service  
- `restart` - Restart the service
- `status` - Show service status
- `logs` - Show service logs
- `help` - Show help message

### Options

- `-b, --background` - Start in background mode
- `-f, --foreground` - Start in foreground mode (default)

## Examples

```bash
# Start backend in background
./scripts/manage_backend.sh start -b

# Start frontend in foreground
./scripts/manage_frontend.sh start

# Restart both services in background
./scripts/manage_backend.sh restart -b
./scripts/manage_frontend.sh restart -b

# Check status of both services
./scripts/manage_backend.sh status
./scripts/manage_frontend.sh status

# View logs
./scripts/manage_backend.sh logs
./scripts/manage_frontend.sh logs

# Stop both services
./scripts/manage_backend.sh stop
./scripts/manage_frontend.sh stop
```

## Log Files

Log files are stored in the `logs/` directory:
- `logs/finance-backend.log` - Backend service logs
- `logs/finance-frontend.log` - Frontend service logs

## PID Files

PID files track running processes:
- `logs/finance-backend.pid` - Backend process ID
- `logs/finance-frontend.pid` - Frontend process ID

## Troubleshooting

### Service Won't Start
1. Check if required packages are installed
2. Verify configuration files exist and are readable
3. Check log files for error messages
4. Ensure ports are not already in use

### Service Won't Stop
1. Check if PID file exists and contains valid process ID
2. Manually kill process if needed: `kill -9 <PID>`
3. Remove stale PID file: `rm logs/finance-*.pid`

### Configuration Issues
1. Ensure environment files are properly formatted (no spaces around `=`)
2. Check that all required variables are set
3. Verify file paths are correct for your system

## Development Workflow

1. **Start Development Environment:**
   ```bash
   # Start backend
   ./scripts/manage_backend.sh start -b
   
   # Start frontend  
   ./scripts/manage_frontend.sh start -b
   ```

2. **Monitor During Development:**
   ```bash
   # Watch backend logs
   ./scripts/manage_backend.sh logs
   
   # Watch frontend logs
   ./scripts/manage_frontend.sh logs
   ```

3. **Restart After Changes:**
   ```bash
   # Restart backend after code changes
   ./scripts/manage_backend.sh restart -b
   
   # Restart frontend after static file changes
   ./scripts/manage_frontend.sh restart -b
   ```

4. **Stop Development Environment:**
   ```bash
   ./scripts/manage_backend.sh stop
   ./scripts/manage_frontend.sh stop
   ```

# PDF Table Extraction Tools

This directory contains tools for extracting merchant statement tables from PDF files with automatic validation, row cleanup, and date formatting.

## Tools

### `extract_pdf_table.py`

A command-line tool for extracting merchant statement tables from PDF files with automatic validation, row cleanup, and date formatting.

#### Features

- **Vendor-specific extraction**: Supports different merchant statement formats (GG, AR, etc.)
- **Flexible column matching**: Handles OCR artifacts, case variations, and spacing differences
- **Automatic validation**: Removes invalid/malformed rows based on data patterns
- **Date formatting**: Converts MM/DD dates to YYYY-MM-DD format with year input
- **Table analysis**: Provides detailed statistics about extracted data
- **Multi-page support**: Handles tables that span across multiple pages
- **Debug mode**: Print diagnostic information for troubleshooting
- **Robust row parsing**: Uses regex patterns to handle variable formatting and missing fields

#### Usage

```bash
# Basic extraction
python3 extract_pdf_table.py --pdf data/gg/input/Jan2025.pdf --vendor gg --year 2025

# With custom output path
python3 extract_pdf_table.py --pdf data/gg/input/Jan2025.pdf --vendor gg --year 2025 --output data/gg/processed/Jan2025.csv

# With debug information
python3 extract_pdf_table.py --pdf data/gg/input/Jan2025.pdf --vendor gg --year 2025 --debug

# Skip format validation (for testing)
python3 extract_pdf_table.py --pdf data/gg/input/Jan2025.pdf --vendor gg --year 2025 --no-validate

# Verbose output with debug
python3 extract_pdf_table.py --pdf data/gg/input/Jan2025.pdf --vendor gg --year 2025 --verbose --debug
```

#### Arguments

- `--pdf` (required): Path to PDF file
- `--vendor` (required): Vendor key (e.g., 'gg', 'ar')
- `--year` (required): Year to add to date column
- `--output` (optional): Output CSV path (default: same as PDF with '_extracted.csv' suffix)
- `--no-validate` (optional): Skip PDF format validation
- `--verbose` (optional): Print detailed information
- `--debug` (optional): Print debug/diagnostic extraction info

#### Supported Vendors

Currently configured vendors:

**GG (Garlic & Chives)**
- Section: "SUMMARY OF MONETARY BATCHES"
- Columns: Gross, R&C, Net, Date, Ref
- Date format: MM/DD (requires year input)
- Amount format: Currency with decimals

**AR (Example)**
- Section: "SUMMARY OF MONETARY BATCHES"
- Columns: Gross, R&C, Net, Date, Ref
- Similar format to GG

#### Adding New Vendors

1. Create a configuration file in `config/` directory:
   ```json
   {
     "source_id": "newvendor",
     "display_name": "New Vendor",
     "pdf_extraction": {
       "enabled": true,
       "section_header": "YOUR SECTION NAME",
       "expected_columns": ["Col1", "Col2", "Col3"],
       "date_column": "Date",
       "validation_rules": {
         "date_format": "MM/DD",
         "min_rows": 1
       }
     }
   }
   ```

2. Test the extraction:
   ```bash
   python3 extract_pdf_table.py --pdf path/to/file.pdf --vendor newvendor --year 2025 --debug
   ```

#### Data Validation

The tool performs several validation steps:

1. **Format validation**: Checks if PDF contains required section and columns
2. **Row validation**: Removes malformed rows based on data patterns
3. **Data type detection**: Automatically detects date, amount, and reference patterns
4. **Completeness check**: Ensures minimum required rows are extracted

#### Debug Mode

When using `--debug`, the tool will print:
- Detected section header location
- First 10 lines of the section
- Candidate header lines and column mapping
- Skipped rows and reasons
- Table analysis statistics

Example debug output:
```
[DEBUG] Section header found at index 27205
[DEBUG] First 10 lines of section:
    SUMMARY OF MONETARY BATCHES
                     GROSS                     R&C                     NET     DATE     REF
                     3,889.16                     .00                3,889.16   1/01 98000141449
[DEBUG] Candidate header line 2:                  GROSS                     R&C                     NET     DATE     REF
[DEBUG] Mapping: {'Gross': 'GROSS', 'R&C': 'R&C', 'Net': 'NET', 'Date': 'DATE', 'Ref': 'REF'}
[DEBUG] Table analysis: 57 valid rows, 5 invalid rows removed
```

#### Troubleshooting

**Common Issues:**

1. **"Expected columns not found in PDF"**
   - Check if the PDF format matches the vendor configuration
   - Use `--debug` to see what columns were actually found
   - Verify the section header exists in the PDF

2. **"No valid rows extracted"**
   - The PDF might have a different format than expected
   - Use `--debug` to see the raw extracted text
   - Check if the table spans multiple pages

3. **Empty or malformed CSV output**
   - Use `--debug` to see row parsing details
   - Check if the PDF has OCR artifacts or unusual formatting
   - Verify the regex pattern matches your data format

**Tips:**
- Always use `--debug` when testing new PDF formats
- Check the vendor configuration in `config/` directory
- Verify the year parameter matches the statement period
- Use `--verbose` for detailed processing information

#### Integration

The extraction tool integrates with the main application:

1. **PDF Service**: Uses the same extraction logic for web uploads
2. **Configuration**: Vendor configs are shared between CLI and web interface
3. **Validation**: Same validation rules apply to both interfaces
4. **Output**: Generated CSVs can be processed by the main data pipeline

#### Example Workflow

```bash
# 1. Extract merchant statement
python3 extract_pdf_table.py --pdf data/gg/input/Jan2025.pdf --vendor gg --year 2025 --debug

# 2. Verify output
head -10 data/gg/input/Jan2025_extracted.csv

# 3. Process through main application
# (The extracted CSV can now be uploaded and processed)
```

#### Dependencies

Required Python packages:
- `PyMuPDF` (fitz): PDF text extraction
- `pandas`: Data manipulation and CSV output
- `difflib`: Fuzzy string matching for column detection

Install with:
```bash
pip install PyMuPDF pandas
```

## Contributing

When adding new vendor support:

1. Test with sample PDF files
2. Update this README with vendor-specific information
3. Add appropriate error handling
4. Include example usage in documentation 