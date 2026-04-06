# Validation System

## Purpose
Validation ensures source files are structurally sound and compatible with mappings before processing. It combines structural checks, source-specific logic, and metadata-based validation.

## Core Components

- `ValidationService` (`app/services/validation_service.py`)
  - Structural validation
  - Source-specific heuristics (BoA, Chase, etc.)
  - Metadata-based validation when sample data exists

- Robust CSV loading
  - `app/utils/csv_loader.py` provides tolerant CSV parsing
  - Used by `DataProcessor` when parsing files with mappings

## Validation Flow

1. **Basic Checks**
   - File exists
   - Allowed file types (CSV/Excel)
   - Size limits

2. **Structure Checks**
   - Required columns present
   - Format checks for dates and amounts

3. **Source-Specific Checks**
   - Known issue detection and warnings
   - Fix suggestions for common issues

4. **Metadata-Based Validation**
   - Compare uploaded file structure to saved sample metadata
   - Produce compatibility score and warnings

## API Endpoints

From `/api/files`:
- `GET /api/files/validate/{source}/{filename}`
- `POST /api/files/validate/{source}`
- `GET /api/files/analyze/{source}/{filename}`
- `POST /api/files/fix/{source}/{filename}`

From `/api/sample-data`:
- `POST /api/sample-data/sources/{source_id}/validate-file`

## Notes
- Validation is designed for CSV and Excel inputs.
- PDF validation exists at the file-service level, but PDF uploads are not enabled in the current upload endpoint.
