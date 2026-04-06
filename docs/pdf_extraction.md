# PDF Extraction Guide (Vendor-Specific)

## Purpose
This document describes how PDF extraction works today and provides a repeatable blueprint for building vendor-specific extraction agents. The priority is accuracy and traceability from PDF → CSV.

## Current Extraction Path

1. PDF exists in `data/{source}/input/`
2. Processing endpoint calls `PDFService.process_merchant_statement()`
3. Vendor-specific extraction:
   - GG uses `scripts/extract_gg_merchant_batches.py`
   - AR (and other vendors) use config-driven extraction in `app/utils/pdf_table_extractor.py`
4. Extracted CSV is then processed into monthly output

## Vendor Config Contract

Config file location:
```
config/{vendor}.json
```

Required `pdf_extraction` keys (used by `pdf_table_extractor.py`):
- `enabled` (bool)
- `section_header` (string)
- `expected_columns` (list of strings)

Optional keys:
- `row_pattern` (regex string)
- `stop_headers` (list of section headers)
- `validate_rows` (bool, default true)
- `date_column` (string, default "Date")
- `validation_rules.min_rows` (int)
- `error_on_section_not_found` (bool)
- `error_on_format_mismatch` (bool)
- `error_on_no_valid_rows` (bool)

## Extraction Flow (Config-Driven)

1. **Format validation**
   - Locate `section_header` in PDF text
   - Validate presence of `expected_columns` using flexible matching
2. **Table extraction**
   - Extract lines from section
   - Identify header row
   - Parse data rows using either `row_pattern` or built-in regex
3. **Row validation**
   - Remove rows that do not match detected column patterns
4. **Date normalization**
   - Add year to date column when `MM/DD` format is used
5. **CSV output**
   - Write extracted rows to CSV (output path set by caller)

## GG Extraction (Script-Based)

Script: `scripts/extract_gg_merchant_batches.py`

Behavior summary:
- Parses the "SUMMARY OF MONETARY BATCHES" section
- Handles continuation pages
- Regex row parsing: `gross`, `r_and_c`, `net`, `date`, `ref`
- Adds `FULL_DATE` by inferring year from filename
- Outputs columns: `FULL_DATE`, `DATE`, `GROSS`, `R&C`, `NET`, `REF`

## AR Extraction (Config-Driven)

AR uses `pdf_table_extractor.py` and `config/ar.json`:
- Extracts the configured section
- Validates expected columns
- Normalizes dates with inferred year
- Writes extracted rows to CSV

## Vendor Agent Blueprint

Each vendor agent should deliver these artifacts:

1. **Config**
   - `config/{vendor}.json` with `pdf_extraction` section
2. **Parser**
   - If config-driven extraction is sufficient, no custom script required
   - If layout is irregular, create a vendor script in `scripts/`
3. **Validation checklist**
   - Confirm section header detection
   - Confirm column detection and row count
   - Verify totals against PDF (gross/net/fees if available)
4. **Test fixture**
   - Store a representative PDF sample (out of git if sensitive)
   - Keep a small anonymized CSV sample for regression tests

## Accuracy Requirements

For each vendor, document:
- Expected row count vs extracted row count
- Total sum comparisons (`gross`, `net`, `amount`)
- Known formatting exceptions (negative amounts, missing rows, split lines)
- Section and header variations across months

## Recommended Testing Workflow

1. Run extraction script or config-based extraction
2. Compare:
   - Row counts
   - Min/max dates
   - Totals
3. Validate output columns match downstream processing needs

## Known Gaps

- UI does not support PDF uploads (manual placement required)
- PDF extraction logic is split between script-based and config-based paths
- No central regression harness for vendor extraction accuracy
