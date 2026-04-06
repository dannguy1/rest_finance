# Backend Architecture

## Purpose
The backend is a FastAPI application that provides file management, processing, mapping, validation, analytics, and health endpoints. It also renders the web UI using Jinja2 templates.

## Main Entry Points
- `main.py`: Uvicorn entry
- `app/api/main.py`: FastAPI app configuration and route registration

## Route Groups

### Files (`/api/files`)
Responsible for upload, file listing, preview, validation, and processing of a single file.

Key routes:
- `POST /api/files/upload/{source}`
- `GET /api/files/list/{source}`
- `GET /api/files/validate/{source}/{filename}`
- `GET /api/files/preview-uploaded/{source}`
- `GET /api/files/preview-uploaded-full/{source}`
- `POST /api/files/process/{source}/{filename}`
- `GET /api/files/output/{source}`
- `GET /api/files/download/{source}/{year}/{month}`
- `DELETE /api/files/processed/{source}/{year}/{month}`

### Processing (`/api/processing`)
Batch processing, single-file processing, and processing summaries.

Key routes:
- `POST /api/processing/process/{source}`
- `POST /api/processing/process-file/{source}/{filename}`
- `GET /api/processing/status/{source}`
- `GET /api/processing/summary/{source}/{year}`
- `GET /api/processing/years/{source}`
- `GET /api/processing/months/{source}/{year}`
- `GET /api/processing/sources`

### Mapping (`/api/mappings`)
CRUD and validation for source mappings.

Key routes:
- `GET /api/mappings`
- `GET /api/mappings/{source_id}`
- `POST /api/mappings`
- `PUT /api/mappings/{source_id}`
- `DELETE /api/mappings/{source_id}`
- `POST /api/mappings/{source_id}/validate`
- `GET /api/mappings/{source_id}/template`

### Sample Data (`/api/sample-data`)
Sample metadata processing and validation.

Key routes:
- `GET /api/sample-data/sources`
- `GET /api/sample-data/sources/{source_id}`
- `GET /api/sample-data/sources/{source_id}/metadata`
- `POST /api/sample-data/sources/{source_id}/validate-file`
- `POST /api/sample-data/sources/{source_id}/update-config`

### Analytics (`/api/files/analytics`)
Aggregations over uploaded or processed files.

Key routes:
- `GET /api/files/analytics/{source}/group-by-description`
- `GET /api/files/analytics/{source}/monthly-summary`
- `GET /api/files/analytics/{source}/amount-analysis`
- `GET /api/files/analytics/{source}/trends`

### Health (`/api/health`)
Service health and metrics.

Key routes:
- `GET /api/health`
- `GET /api/health/detailed`
- `GET /api/health/ready`
- `GET /api/health/live`
- `GET /api/health/metrics`
- `GET /api/health/prometheus`

### Web UI (server-rendered)
Routes in `app/api/routes/web_routes.py` render templates under `app/templates/`.

## Core Services

### `FileService`
Manages storage under `data/{source}/input` and `data/{source}/output`, preview helpers, and deletion.

### `DataProcessor`
Orchestrates parsing, grouping, and output. Handles PDFs during processing by extracting to CSV first.

### `ValidationService`
Validates CSV structure and data quality. Supports metadata-based validation using saved sample data.

### `PDFService`
Vendor-specific PDF extraction, primarily for merchant statements (GG and AR).

### `SampleDataService`
Persists sample metadata in `data/source_metadata/{source_id}/`.

## Processing Flow

1. Upload to `data/{source}/input/`
2. Validate via `ValidationService`
3. Parse via mapping config or legacy parsing
4. Group by year/month
5. Write output files to `data/{source}/output/{year}/{month}_{year}.csv`

## Configuration

- `app/config/settings.py`: global settings (paths, limits, CORS)
- `app/config/source_mapping.py`: default mappings and JSON mapping loader
- `config/{source_id}.json`: per-source mapping overrides

## Error Handling and Logging

- `app/middleware/error_middleware.py`: consistent error responses
- `app/middleware/logging_middleware.py`: request/response logging
- `app/utils/logging.py`: structured processing logs

## Storage Notes

The application currently uses the file system for all data storage. The SQLite settings entry is a placeholder and not used by the services.
