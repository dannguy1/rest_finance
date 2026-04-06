# System Overview

## Purpose
Garlic and Chives is a multi-source financial data processor. It ingests source files (currently CSV/Excel uploads), applies source-specific mapping and validation, and produces normalized monthly CSV outputs organized by source and year.

## Core Concepts

### Source Mapping
Each source has a mapping configuration that describes how its columns map to normalized fields (date, description, amount). Mappings live in `config/{source_id}.json` and are managed in-memory by `SourceMappingManager`.

### Sample Metadata
Sample data is processed and stored as metadata to improve validation and mapping usability. This metadata is stored on disk at `data/source_metadata/{source_id}/`.

### Processing Pipeline
1. **Upload** CSV/Excel to `data/{source}/input/`
2. **Validate** file structure and data quality
3. **Map** to normalized fields
4. **Transform** and group by month
5. **Write** monthly outputs to `data/{source}/output/{year}/{month}_{year}.csv`

### PDF Support (Merchant Statements)
The processing engine can extract PDFs to CSV during processing. However, the current upload endpoint only accepts CSV/Excel. PDFs must already exist in the source input folder to be processed.

## High-Level Architecture

- **API + Web UI**: FastAPI with server-side templates
- **Frontend**: Jinja2 templates + vanilla JS (no SPA)
- **Storage**: File system only (no DB in active use)
- **Processing Engine**: `DataProcessor` orchestrates parsing, validation, and output

```
User -> FastAPI -> FileService -> Validation -> Processing -> File System
```

## Key Directories

```
app/                   # FastAPI application code
config/                # Source mapping JSON configs
data/{source}/input/   # Uploaded source files
data/{source}/output/  # Processed monthly output files
data/source_metadata/  # Sample metadata per source
docs/                  # Project documentation
```

## System Status Snapshot

Implemented:
- Source mappings for BoA, Chase, Restaurant Depot, Sysco, GG, AR
- CSV validation and robust parsing
- Per-file and per-source processing
- Analytics endpoints
- Web UI for upload/process/preview

In-progress / gaps:
- PDF upload flow in the web UI (processing supports PDFs if present on disk)
- Unified API reference doc (provided in this documentation rewrite)
- Clear project status tracking (provided in `docs/project_status.md`)

## Documentation Map

- `docs/backend.md`: Backend architecture and flows
- `docs/frontend.md`: Templates and JS structure
- `docs/mapping.md`: Source mapping system
- `docs/validation.md`: Validation approach
- `docs/merchant_processing.md`: Merchant/PDF processing details
- `docs/pdf_extraction.md`: Vendor PDF extraction guide
- `docs/api_reference.md`: API endpoints
- `docs/project_status.md`: Status, gaps, and next-level recommendations