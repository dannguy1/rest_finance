# Project Status

## Current State
The core system is functional for CSV/Excel ingestion, mapping, validation, processing, and analytics. The architecture is file-system based and avoids storing user data in a database.

## Implemented Features

- Source mappings for BoA, Chase, Restaurant Depot, Sysco, GG, AR
- Robust CSV parsing and validation with issue detection
- Metadata-driven validation using saved sample data
- Per-file and per-source processing with monthly outputs
- PDF extraction during processing for merchant statements
- Analytics endpoints for aggregated insights
- Web UI with upload/preview/process flows
- Health endpoints and Prometheus metrics

## Notable Gaps / Risks

- **PDF upload flow**: `/api/files/upload/{source}` only accepts CSV/Excel. PDFs must be placed in input folders manually to be processed.
- **Source configuration duplication**: processing routes hardcode source configs while mapping manager defines source config elsewhere, increasing drift risk.
- **UI coverage**: GG and AR sources are supported but not included in the default sidebar navigation.
- **Database placeholder**: settings include SQLite URL but no DB is actually used by services.

## Recommendations to Move to the Next Level

1. **Unify source configuration**
   - Consolidate `SOURCE_CONFIGS` in processing/analytics routes with the mapping manager.
   - Remove duplicated config logic.

2. **Enable PDF upload**
   - Expand allowed file types and upload endpoint validation.
   - Update frontend upload flows for PDF sources.

3. **Formalize API contract**
   - Keep `docs/api_reference.md` in sync with code.
   - Add versioning or explicit changelog for breaking changes.

4. **Document deployment and ops**
   - Add a deployment guide and production checklist.
   - Clarify file storage, backups, and retention policies.

5. **Productize source onboarding**
   - Improve mapping UI workflows for new sources.
   - Add validation feedback loops with clearer diagnostics.
