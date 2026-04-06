# Source Mapping System

## Purpose
Mappings define how each source’s columns map to normalized fields used by the processor. This enables source-specific formats without code changes.

## Mapping Model
Mappings are defined by `SourceMappingConfig` in `app/config/source_mapping.py`.

Core fields:
- `source_id`, `display_name`, `description`, `icon`
- `date_mapping`, `description_mapping`, `amount_mapping`
- `optional_mappings`
- `expected_columns`, `required_columns`
- `default_date_format`, `default_amount_format`
- `example_data` (optional)

### Column Mapping
Each column mapping defines:
- `source_column`
- `target_field`
- `mapping_type` (`date`, `description`, `amount`, `optional`)
- `required`
- `date_format` / `amount_format` (optional)

## Storage

- Default mappings live in `app/config/source_mapping.py`
- Overrides are stored as JSON files in `config/{source_id}.json`
- Mappings are loaded at runtime by `SourceMappingManager`

## Sample Metadata Integration

Sample data metadata is stored in:
```
data/source_metadata/{source_id}/{source_id}_sample_data.json
```

This metadata is used by validation and to prefill mapping UI selections.

## Mapping API

- `GET /api/mappings`
- `GET /api/mappings/{source_id}`
- `POST /api/mappings`
- `PUT /api/mappings/{source_id}`
- `DELETE /api/mappings/{source_id}`
- `POST /api/mappings/{source_id}/validate`
- `GET /api/mappings/{source_id}/template`

## Sample Data API

- `GET /api/sample-data/sources`
- `GET /api/sample-data/sources/{source_id}`
- `GET /api/sample-data/sources/{source_id}/metadata`
- `POST /api/sample-data/sources/{source_id}/validate-file`
- `POST /api/sample-data/sources/{source_id}/update-config`

## Example (Minimal Mapping)

```json
{
  "source_id": "bankofamerica",
  "display_name": "Bank of America",
  "description": "Bank statement processing",
  "icon": "bank",
  "date_mapping": {
    "source_column": "Date",
    "target_field": "date",
    "mapping_type": "date",
    "required": true,
    "date_format": "MM/DD/YYYY"
  },
  "description_mapping": {
    "source_column": "Original Description",
    "target_field": "description",
    "mapping_type": "description",
    "required": true
  },
  "amount_mapping": {
    "source_column": "Amount",
    "target_field": "amount",
    "mapping_type": "amount",
    "required": true,
    "amount_format": "USD"
  },
  "optional_mappings": [],
  "expected_columns": ["Status", "Date", "Original Description", "Amount"],
  "required_columns": ["Date", "Original Description", "Amount"]
}
```
