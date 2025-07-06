# Source Mapping Configuration Design Document

## Overview

The Source Mapping Configuration system provides a flexible, user-configurable mechanism for mapping source-specific CSV columns to normalized processed data. This system enables the financial data processor to handle diverse data sources with different column names, formats, and structures while maintaining consistent output formats.

## Core Concepts

### 1. Mapping Types

The system supports four primary mapping types:

- **DATE**: Maps source date columns to normalized date field
- **DESCRIPTION**: Maps source description/transaction columns to normalized description field  
- **AMOUNT**: Maps source amount/balance columns to normalized amount field
- **OPTIONAL**: Maps additional source columns to custom output fields for future usage

### 2. Normalized Output Structure

All processed data follows a consistent structure:

```json
{
  "date": "2024-01-15",
  "description": "VERIZON WIRELESS",
  "amount": -421.50,
  "source_file": "boa_statement_2024.csv",
  "transaction_type": "DEBIT",           // Optional field
  "account_id": "1234567890",           // Optional field
  "category": "UTILITIES",               // Optional field
  "reference_number": "CHK123456",       // Optional field
  "balance": 15420.67,                  // Optional field
  "notes": "Monthly wireless bill"       // Optional field
}
```

## Design Architecture

### 1. Configuration Structure

```python
class SourceMappingConfig:
    source_id: str                    # Unique identifier (e.g., "bankofamerica")
    display_name: str                 # Human-readable name
    description: str                  # Source description
    icon: str                         # UI icon identifier
    
    # Core mappings (required)
    date_mapping: ColumnMapping
    description_mapping: ColumnMapping  
    amount_mapping: ColumnMapping
    
    # Optional mappings (extensible)
    optional_mappings: List[ColumnMapping]
    
    # Validation settings
    expected_columns: List[str]       # All possible columns
    required_columns: List[str]       # Must be present
    
    # Processing settings
    default_date_format: str
    default_amount_format: str
    
    # UI/UX
    example_data: List[Dict]         # Sample rows for UI
```

### 2. Column Mapping Structure

```python
class ColumnMapping:
    source_column: str               # Column name in source file
    target_field: str                # Field name in normalized output
    mapping_type: MappingType        # DATE, DESCRIPTION, AMOUNT, OPTIONAL
    required: bool                   # Whether column is required
    date_format: Optional[str]       # For date mappings
    amount_format: Optional[str]     # For amount mappings
    description: Optional[str]       # Human-readable description
    validation_rules: Optional[Dict] # Custom validation rules
    transformation: Optional[str]    # Data transformation function
```

## Implementation Details

### 1. Default Source Configurations

#### Bank of America
```python
{
    "source_id": "bankofamerica",
    "display_name": "Bank of America",
    "date_mapping": {"source_column": "Date", "target_field": "date"},
    "description_mapping": {"source_column": "Original Description", "target_field": "description"},
    "amount_mapping": {"source_column": "Amount", "target_field": "amount"},
    "optional_mappings": [
        {"source_column": "Status", "target_field": "transaction_type"},
        {"source_column": "Account", "target_field": "account_id"}
    ]
}
```

#### Chase
```python
{
    "source_id": "chase", 
    "display_name": "Chase",
    "date_mapping": {"source_column": "Posting Date", "target_field": "date"},
    "description_mapping": {"source_column": "Description", "target_field": "description"},
    "amount_mapping": {"source_column": "Amount", "target_field": "amount"},
    "optional_mappings": [
        {"source_column": "Type", "target_field": "transaction_type"},
        {"source_column": "Details", "target_field": "notes"},
        {"source_column": "Balance", "target_field": "balance"},
        {"source_column": "Check or Slip #", "target_field": "reference_number"}
    ]
}
```

### 2. Processing Pipeline

#### Step 1: Source Detection
- Analyze uploaded file headers
- Match against known source configurations
- Suggest mapping based on column name similarity

#### Step 2: Mapping Validation
- Verify required columns are present
- Check column data types match expectations
- Validate date/amount formats

#### Step 3: Data Transformation
- Apply column mappings to extract normalized data
- Transform dates to standard format (YYYY-MM-DD)
- Normalize amounts (remove currency symbols, handle negatives)
- Apply optional transformations (e.g., category detection)

#### Step 4: Output Generation
- Generate normalized CSV with consistent structure
- Include all mapped optional fields
- Add metadata (source file, processing timestamp)

### 3. API Endpoints

#### Mapping Management
```
GET    /api/mappings                    # List all mappings
GET    /api/mappings/{source_id}        # Get specific mapping
POST   /api/mappings                    # Create new mapping
PUT    /api/mappings/{source_id}        # Update mapping
DELETE /api/mappings/{source_id}        # Delete mapping
POST   /api/mappings/{source_id}/validate # Validate mapping
GET    /api/mappings/{source_id}/template # Get template for new source
```

#### File Processing with Mapping
```
POST   /api/files/upload/{source_id}   # Upload with mapping validation
POST   /api/files/process/{source_id}  # Process using mapping
GET    /api/files/analyze/{source_id}  # Analyze file structure
```

### 4. User Interface Components

#### Mapping Configuration Page
- **Source List**: Display all configured sources with edit/delete options
- **Mapping Editor**: Form-based editor for column mappings
- **Validation Panel**: Real-time validation feedback
- **Example Data**: Show sample data with current mapping

#### File Upload with Mapping
- **Source Selection**: Choose or create source configuration
- **Column Mapping**: Visual mapping interface
- **Preview**: Show how data will be transformed
- **Validation**: Real-time validation feedback

#### Analysis Tools
- **Column Detection**: Auto-detect potential mappings
- **Data Preview**: Show sample rows with current mapping
- **Format Analysis**: Analyze date/amount formats

## Future Extensibility

### 1. Additional Output Fields

The system is designed to support additional output fields for future usage:

#### Transaction Categorization
```python
{
    "source_column": "Category", 
    "target_field": "category",
    "mapping_type": "OPTIONAL",
    "transformation": "category_detector"
}
```

#### Account Management
```python
{
    "source_column": "Account Number",
    "target_field": "account_id", 
    "mapping_type": "OPTIONAL",
    "validation_rules": {"pattern": r"^\d{10}$"}
}
```

#### Reference Tracking
```python
{
    "source_column": "Reference",
    "target_field": "reference_number",
    "mapping_type": "OPTIONAL"
}
```

### 2. Advanced Features

#### Data Transformations
- **Date Format Conversion**: Support multiple input formats
- **Amount Normalization**: Handle different currency formats
- **Text Processing**: Clean descriptions, extract categories
- **Custom Functions**: User-defined transformation logic

#### Validation Rules
- **Pattern Matching**: Regex validation for fields
- **Range Validation**: Numeric value ranges
- **Cross-field Validation**: Dependencies between fields
- **Custom Validators**: User-defined validation logic

#### Mapping Templates
- **Industry Templates**: Pre-configured mappings for common sources
- **User Templates**: Save and reuse custom mappings
- **Import/Export**: Share mappings between users

### 3. Integration Points

#### Analytics Integration
- **Category Analysis**: Use mapped category fields for spending analysis
- **Account Tracking**: Track spending across multiple accounts
- **Trend Analysis**: Analyze patterns in transaction types

#### Reporting Features
- **Custom Reports**: Use optional fields for detailed reporting
- **Filtering**: Filter by transaction type, account, category
- **Grouping**: Group transactions by mapped fields

## Implementation Phases

### Phase 1: Core Mapping System
- [x] Basic mapping configuration structure
- [x] API endpoints for mapping management
- [x] Web interface for mapping configuration
- [x] Integration with existing file processing

### Phase 2: Enhanced Features
- [ ] Advanced validation rules
- [ ] Data transformation functions
- [ ] Mapping templates and sharing
- [ ] Auto-detection of column mappings

### Phase 3: Analytics Integration
- [ ] Category-based analysis
- [ ] Multi-account tracking
- [ ] Custom reporting based on mapped fields
- [ ] Trend analysis using optional fields

## Benefits

### 1. Flexibility
- **New Sources**: Add new data sources without code changes
- **Format Changes**: Update mappings when banks change formats
- **Custom Fields**: Add new output fields as needed

### 2. User Empowerment
- **Self-Service**: Users can configure mappings themselves
- **Visual Feedback**: Clear preview of how data will be transformed
- **Validation**: Real-time validation prevents errors

### 3. Future-Proofing
- **Extensible**: Easy to add new field types and transformations
- **Scalable**: Supports unlimited sources and field mappings
- **Maintainable**: Centralized configuration management

### 4. Data Quality
- **Consistent Output**: All sources produce normalized data
- **Validation**: Built-in validation prevents data errors
- **Traceability**: Track source of each data field

## Conclusion

The Source Mapping Configuration system provides a robust, flexible foundation for handling diverse financial data sources while maintaining data quality and consistency. The extensible design ensures the system can grow with future requirements while empowering users to manage their own data mappings. 