# Configuration Directory

This directory contains JSON configuration files for source mapping configurations in the Financial Data Processor.

## Structure

Each source has its own JSON file named `{source_id}.json` (e.g., `bankofamerica.json`).

## File Format

Each configuration file contains a complete `SourceMappingConfig` object with the following structure:

```json
{
  "source_id": "bankofamerica",
  "display_name": "Bank of America",
  "description": "Bank statement processing and management",
  "icon": "bank",
  "date_mapping": {
    "source_column": "Date",
    "target_field": "date",
    "mapping_type": "date",
    "required": true,
    "date_format": "MM/DD/YYYY",
    "description": "Transaction date"
  },
  "description_mapping": {
    "source_column": "Original Description",
    "target_field": "description",
    "mapping_type": "description",
    "required": true,
    "description": "Transaction description"
  },
  "amount_mapping": {
    "source_column": "Amount",
    "target_field": "amount",
    "mapping_type": "amount",
    "required": true,
    "amount_format": "USD",
    "description": "Transaction amount"
  },
  "optional_mappings": [
    {
      "source_column": "Status",
      "target_field": "status",
      "mapping_type": "optional",
      "required": false,
      "description": "Transaction status"
    }
  ],
  "expected_columns": ["Status", "Date", "Original Description", "Amount"],
  "required_columns": ["Date", "Original Description", "Amount"],
  "default_date_format": "MM/DD/YYYY",
  "default_amount_format": "USD",
  "example_data": [
    {
      "Status": "Posted",
      "Date": "01/15/2024",
      "Original Description": "VERIZON WIRELESS",
      "Amount": "-421.50"
    }
  ]
}
```

## Current Sources

- `bankofamerica.json` - Bank of America bank statements
- `chase.json` - Chase bank statements  
- `restaurantdepot.json` - Restaurant Depot supplier receipts
- `sysco.json` - Sysco supplier receipts

## Management

- **Loading**: Mappings are automatically loaded from JSON files on startup
- **Saving**: Changes made through the web interface are automatically saved to JSON files
- **Deletion**: Removing a mapping also deletes its JSON file
- **Backup**: Files are version controlled and can be backed up

## Adding New Sources

1. Create a new JSON file with the source_id as the filename
2. Follow the structure above
3. Restart the application or the mapping will be loaded automatically
4. Use the web interface to edit and validate the configuration

## Validation

All configurations are validated against the `SourceMappingConfig` Pydantic model to ensure:
- Required fields are present
- Data types are correct
- Column mappings are valid
- No duplicate source columns 