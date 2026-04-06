# Merchant Processing (PDF + CSV)

## Purpose
Merchant sources (GG, AR) support PDF extraction during processing. This document summarizes the flow and links to the vendor extraction guide.

## Current Behavior

- **Upload endpoints** only accept CSV/Excel.
- **Processing endpoints** can process PDF files if they already exist in `data/{source}/input/`.
- PDF extraction happens at processing time, not upload time.

## File Flow

1. Place PDF in `data/{source}/input/`
2. Call `POST /api/processing/process-file/{source}/{filename}`
3. `PDFService` extracts to CSV
4. Processing continues on extracted CSV
5. Output written to `data/{source}/output/{year}/{month}_{year}.csv`

## Supported Vendors

- GG: uses `scripts/extract_gg_merchant_batches.py`
- AR: uses vendor-config extraction via `app/utils/pdf_table_extractor.py`

For vendor-specific extraction requirements and agent blueprint, see `docs/pdf_extraction.md`.

## Source File Layout

```
data/{source}/
├── input/
│   ├── <uploaded>.csv
│   └── <uploaded>.pdf
└── output/
    └── {year}/
        └── {month}_{year}.csv
```

## Relevant APIs

- `POST /api/processing/process-file/{source}/{filename}`
- `GET /api/files/list/{source}`
- `GET /api/files/preview-uploaded/{source}`
- `GET /api/files/analyze/{source}/{filename}`

## Known Gaps

- PDF uploads are not supported in `/api/files/upload/{source}`.
- The UI does not expose a PDF upload flow.

These are good candidates for the next phase.
