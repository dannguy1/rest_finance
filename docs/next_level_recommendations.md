# Next-Level Recommendations

## Executive Summary
The system successfully processes multi-source CSV data and supports PDF extraction for merchant sources when PDFs exist in the input folder. The primary gaps are around the user flow for PDF-driven vendors, configuration consistency, and extraction accuracy assurance. This document outlines improvements to make vendor-specific PDF ingestion reliable, auditable, and user-friendly.

## Current User Flow Effectiveness

### Product Type Selection
**Current state:** Source selection exists in the sidebar, but only a subset of sources are exposed (BoA, Chase, Sysco, Restaurant Depot). GG and AR are supported in backend processing but not included in the default navigation.

**Impact:** Users cannot reliably discover PDF-based vendors from the UI, which reduces adoption of the PDF workflow.

### Vendor Document Selection
**Current state:** Upload endpoints accept CSV/Excel only. PDFs must be manually placed into `data/{source}/input/`. There is no UI for PDF selection or upload.

**Impact:** PDF workflows require manual file system access, which blocks typical end users and makes onboarding non-intuitive.

### Extraction Accuracy
**Current state:** Extraction relies on:
- GG: a dedicated script with a vendor-specific regex parser.
- AR: config-driven extraction via `pdf_table_extractor.py`.
Validation exists but lacks a consistent regression harness or acceptance criteria across vendors.

**Impact:** Extraction quality is not systematically measured. Changes to vendor formats risk silent data loss or mis-extraction.

### Analysis & Output
**Current state:** Analytics endpoints exist but are CSV-centric and assume normalized columns. PDF extraction output depends on vendor formats and may not always align with downstream analytics expectations.

**Impact:** Analytical accuracy depends on extraction consistency and column normalization.

## Key Gaps

1. **PDF upload is not supported in the web UI or `/api/files/upload/{source}`.**
2. **Source discovery in UI is incomplete (GG/AR missing).**
3. **Extraction logic is split between script-based and config-based approaches.**
4. **No standardized extraction acceptance tests or QA metrics per vendor.**
5. **No per-vendor extraction documentation surfaced in the UI.**
6. **Source config duplication between mapping manager and processing routes risks drift.**

## Recommendations to Move to the Next Level

### 1) Make PDF Ingestion a First-Class User Flow
- Enable PDF uploads in `/api/files/upload/{source}` for vendor sources.
- Add PDF upload support in the source UI (file picker + drag/drop).
- Add file type hints based on vendor config (PDF vs CSV vs Excel).

### 2) Standardize Vendor Extraction Contracts
- Consolidate all vendor extraction rules into `config/{vendor}.json`.
- Prefer config-driven extraction for consistency.
- Only use custom scripts for edge cases and document them in `docs/pdf_extraction.md`.

### 3) Add Extraction Accuracy Harness
- Create a per-vendor regression test suite:
  - Expected row count
  - Total sum comparisons (gross, net, fees)
  - Date range checks
  - Known exceptions (negative amounts, split lines)
- Store sample PDFs outside git and keep anonymized CSV golden files for CI.

### 4) Normalize Outputs for Analytics
- Ensure vendor extraction outputs map to the same normalized schema used by CSV sources.
- Add an explicit extraction → normalization step that always emits standard columns.

### 5) Improve User Feedback
- Show extraction metrics after processing:
  - Rows extracted
  - Totals matched vs expected
  - Warnings on suspected missing rows
- Add vendor-specific extraction status and troubleshooting hints.

### 6) Unify Source Configuration
- Replace hardcoded `SOURCE_CONFIGS` in processing/analytics routes with the mapping manager.
- Maintain one authoritative source of truth per vendor.

## Proposed Vendor Agent Responsibilities

For each vendor:
1. Define `pdf_extraction` in `config/{vendor}.json`.
2. Provide a reference PDF sample (secure storage).
3. Deliver a verified extraction CSV (golden output).
4. Add acceptance thresholds for:
   - Row count
   - Total amount checks
   - Date range coverage
5. Document known layout variants or seasonal changes.

## User Journey Target State

1. User selects product type (Bank, Supplier, Merchant).
2. User selects vendor from curated list (includes GG/AR).
3. UI accepts vendor-specific file types (PDF/CSV/Excel).
4. Extraction runs with vendor agent rules.
5. User sees extraction QA metrics + output preview.
6. User downloads normalized CSV and analytics reports.

## Short-Term Roadmap

- Add PDF upload support in UI and API.
- Add GG/AR to navigation.
- Implement extraction QA report in processing response.
- Add vendor extraction acceptance checklist to `docs/pdf_extraction.md`.

## Long-Term Roadmap

- Consolidate extraction into a vendor-agent framework.
- Add automated PDF format change detection.
- Add structured data lineage (PDF → CSV → normalized output).
