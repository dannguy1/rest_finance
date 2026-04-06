# API Reference (Current)

Base path: `/api`

## Files (`/api/files`)

- `POST /api/files/upload/{source}`
- `GET /api/files/list/{source}`
- `GET /api/files/{source}` (processed files list)
- `DELETE /api/files/{source}/{filename}`
- `GET /api/files/validate/{source}/{filename}`
- `POST /api/files/validate/{source}` (validate all uploaded files)
- `GET /api/files/analyze/{source}/{filename}`
- `POST /api/files/fix/{source}/{filename}`
- `GET /api/files/formats/{source}`
- `GET /api/files/view-pdf/{source}?file=...`
- `GET /api/files/preview/{source}?file=...`
- `GET /api/files/preview-full/{source}?file=...`
- `GET /api/files/preview-uploaded/{source}?file=...`
- `GET /api/files/preview-uploaded-full/{source}?file=...`
- `GET /api/files/output/{source}?year=...`
- `GET /api/files/download/{source}/{year}/{month}`
- `GET /api/files/download/{source}?file=...`
- `POST /api/files/process/{source}/{filename}`
- `DELETE /api/files/processed/{source}/{year}/{month}`
- `POST /api/files/backup/{source}/{filename}`

## Processing (`/api/processing`)

- `POST /api/processing/process/{source}`
- `POST /api/processing/process-file/{source}/{filename}`
- `GET /api/processing/status/{source}`
- `GET /api/processing/summary/{source}/{year}`
- `GET /api/processing/download/{source}/{year}/{month}`
- `GET /api/processing/sources`
- `GET /api/processing/years/{source}`
- `GET /api/processing/months/{source}/{year}`
- `GET /api/processing/ws/{source}/{year}` (WebSocket)

## Mapping (`/api/mappings`)

- `GET /api/mappings`
- `GET /api/mappings/{source_id}`
- `POST /api/mappings`
- `PUT /api/mappings/{source_id}`
- `DELETE /api/mappings/{source_id}`
- `POST /api/mappings/{source_id}/validate`
- `GET /api/mappings/{source_id}/template`
- `GET /api/mappings/{source_id}/format`
- `POST /api/mappings/{source_id}/test-file`
- `GET /api/mappings/{source_id}/sample-template`

### Mapping Utilities (also under `/api/mappings`)
- `POST /api/mappings/process-sample-file`
- `GET /api/mappings/list-sample-files`
- `POST /api/mappings/process-existing-file`
- `GET /api/mappings/sample-data/{source_id}`
- `GET /api/mappings/sample-data`
- `DELETE /api/mappings/sample-data/{source_id}`
- `POST /api/mappings/sample-data/{source_id}/validate`

## Sample Data (`/api/sample-data`)

- `GET /api/sample-data/sources`
- `GET /api/sample-data/sources/{source_id}`
- `GET /api/sample-data/sources/{source_id}/full`
- `GET /api/sample-data/sources/{source_id}/metadata`
- `POST /api/sample-data/sources/{source_id}/validate`
- `POST /api/sample-data/sources/{source_id}/validate-file`
- `POST /api/sample-data/sources/{source_id}/update-config`
- `GET /api/sample-data/config/{source_id}`
- `DELETE /api/sample-data/sources/{source_id}`

## Analytics (`/api/files/analytics`)

All analytics endpoints require query parameters:
- `fileType`: `uploaded` or `processed`
- `filePath`: path relative to source input/output

Endpoints:
- `GET /api/files/analytics/{source}/group-by-description`
- `GET /api/files/analytics/{source}/monthly-summary`
- `GET /api/files/analytics/{source}/amount-analysis`
- `GET /api/files/analytics/{source}/trends`

## Health (`/api/health`)

- `GET /api/health`
- `GET /api/health/detailed`
- `GET /api/health/ready`
- `GET /api/health/live`
- `GET /api/health/metrics`
- `GET /api/health/prometheus`

## Web UI

Rendered pages are served by `app/api/routes/web_routes.py` (no `/api` prefix).

## API Docs (debug only)

- `GET /api/docs`
- `GET /api/redoc`
