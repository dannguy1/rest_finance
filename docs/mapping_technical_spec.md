# Source Mapping Technical Specification

## System Architecture

### 1. Data Flow Overview

```
Upload File → Source Detection → Mapping Validation → Data Transformation → Normalized Output
     ↓              ↓                ↓                ↓                ↓
File Service → Mapping Manager → Validation Service → Data Processor → Output Service
```

### 2. Component Responsibilities

#### Mapping Manager (`app/config/source_mapping.py`)
- **Configuration Storage**: Maintains mapping configurations in memory
- **Validation Logic**: Validates mapping configurations
- **Template Generation**: Creates mapping templates for new sources
- **API Integration**: Provides mapping data to API endpoints

#### File Service (`app/services/file_service.py`)
- **File Operations**: Handles file upload, storage, and retrieval
- **Source Detection**: Analyzes file headers to suggest mappings
- **Processing Coordination**: Orchestrates the processing pipeline

#### Validation Service (`app/services/validation_service.py`)
- **Column Validation**: Validates required columns are present
- **Data Type Validation**: Ensures data types match expectations
- **Format Validation**: Validates date/amount formats
- **Mapping Validation**: Validates mapping configurations

#### Data Processor (`app/services/data_processor.py`)
- **Data Transformation**: Applies mappings to transform data
- **Format Standardization**: Converts dates/amounts to standard formats
- **Optional Field Processing**: Handles additional mapped fields
- **Output Generation**: Creates normalized CSV files

## API Design

### 1. Mapping Management Endpoints

#### List All Mappings
```http
GET /api/mappings
```

**Response:**
```json
{
  "mappings": {
    "bankofamerica": {
      "source_id": "bankofamerica",
      "display_name": "Bank of America",
      "description": "Bank statement processing",
      "required_columns": ["Date", "Original Description", "Amount"],
      "optional_columns": ["Status"],
      "date_format": "MM/DD/YYYY",
      "amount_format": "USD"
    }
  },
  "count": 4
}
```

#### Get Specific Mapping
```http
GET /api/mappings/{source_id}
```

**Response:**
```json
{
  "mapping": {
    "source_id": "chase",
    "display_name": "Chase",
    "description": "Chase bank statement processing",
    "icon": "credit-card",
    "date_mapping": {
      "source_column": "Posting Date",
      "target_field": "date",
      "mapping_type": "date",
      "required": true,
      "date_format": "MM/DD/YYYY"
    },
    "description_mapping": {
      "source_column": "Description",
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
    "optional_mappings": [
      {
        "source_column": "Type",
        "target_field": "transaction_type",
        "mapping_type": "optional",
        "required": false,
        "description": "Transaction type"
      }
    ],
    "expected_columns": ["Posting Date", "Description", "Amount", "Type"],
    "required_columns": ["Posting Date", "Description", "Amount"],
    "example_data": [
      {
        "Posting Date": "01/15/2024",
        "Description": "VERIZON WIRELESS",
        "Amount": "-421.50",
        "Type": "DEBIT"
      }
    ]
  },
  "summary": {
    "source_id": "chase",
    "display_name": "Chase",
    "required_columns": ["Posting Date", "Description", "Amount"],
    "optional_columns": ["Type"]
  }
}
```

#### Create New Mapping
```http
POST /api/mappings
Content-Type: application/json

{
  "source_id": "newbank",
  "display_name": "New Bank",
  "description": "New bank statement processing",
  "icon": "bank",
  "date_mapping": {
    "source_column": "Transaction Date",
    "target_field": "date",
    "mapping_type": "date",
    "required": true,
    "date_format": "MM/DD/YYYY"
  },
  "description_mapping": {
    "source_column": "Transaction Description",
    "target_field": "description",
    "mapping_type": "description",
    "required": true
  },
  "amount_mapping": {
    "source_column": "Transaction Amount",
    "target_field": "amount",
    "mapping_type": "amount",
    "required": true,
    "amount_format": "USD"
  },
  "optional_mappings": [
    {
      "source_column": "Account Number",
      "target_field": "account_id",
      "mapping_type": "optional",
      "required": false,
      "description": "Account identifier"
    }
  ],
  "expected_columns": ["Transaction Date", "Transaction Description", "Transaction Amount", "Account Number"],
  "required_columns": ["Transaction Date", "Transaction Description", "Transaction Amount"],
  "example_data": [
    {
      "Transaction Date": "01/15/2024",
      "Transaction Description": "GROCERY STORE",
      "Transaction Amount": "-45.67",
      "Account Number": "1234567890"
    }
  ]
}
```

### 2. File Processing with Mapping

#### Upload with Mapping Validation
```http
POST /api/files/upload/{source_id}
Content-Type: multipart/form-data

files: [file1.csv, file2.csv]
mapping_override: {
  "date_mapping": {
    "source_column": "Custom Date",
    "target_field": "date"
  }
}
```

#### Process with Mapping
```http
POST /api/files/process/{source_id}/{filename}
Content-Type: application/json

{
  "mapping_override": {
    "optional_mappings": [
      {
        "source_column": "Category",
        "target_field": "category",
        "mapping_type": "optional"
      }
    ]
  },
  "processing_options": {
    "include_optional_fields": true,
    "date_format": "MM/DD/YYYY",
    "amount_format": "USD"
  }
}
```

### 3. Analysis Endpoints

#### Analyze File Structure
```http
GET /api/files/analyze/{source_id}/{filename}
```

**Response:**
```json
{
  "filename": "chase_statement.csv",
  "source": "chase",
  "analysis": {
    "detected_columns": ["Posting Date", "Description", "Amount", "Type", "Balance"],
    "suggested_mappings": {
      "date_mapping": {
        "source_column": "Posting Date",
        "confidence": 0.95
      },
      "description_mapping": {
        "source_column": "Description", 
        "confidence": 0.90
      },
      "amount_mapping": {
        "source_column": "Amount",
        "confidence": 0.85
      }
    },
    "data_samples": [
      {
        "Posting Date": "01/15/2024",
        "Description": "VERIZON WIRELESS",
        "Amount": "-421.50",
        "Type": "DEBIT",
        "Balance": "15420.67"
      }
    ],
    "format_analysis": {
      "date_format": "MM/DD/YYYY",
      "amount_format": "USD",
      "has_negative_amounts": true
    }
  }
}
```

## Data Processing Pipeline

### 1. Source Detection Algorithm

```python
def detect_source(file_headers: List[str]) -> Dict[str, float]:
    """
    Analyze file headers to suggest source mappings.
    Returns confidence scores for each known source.
    """
    suggestions = {}
    
    for source_id, mapping in mapping_manager.get_all_mappings().items():
        score = 0
        total_columns = len(mapping.expected_columns)
        
        for expected_col in mapping.expected_columns:
            for header in file_headers:
                similarity = calculate_similarity(expected_col, header)
                if similarity > 0.8:
                    score += similarity
                    break
        
        confidence = score / total_columns
        if confidence > 0.5:
            suggestions[source_id] = confidence
    
    return suggestions
```

### 2. Data Transformation Process

```python
def transform_data(
    source_data: List[Dict], 
    mapping: SourceMappingConfig
) -> List[Dict]:
    """
    Transform source data using mapping configuration.
    """
    transformed_data = []
    
    for row in source_data:
        transformed_row = {
            "source_file": source_file,
            "processed_date": datetime.now().isoformat()
        }
        
        # Apply required mappings
        transformed_row["date"] = transform_date(
            row[mapping.date_mapping.source_column],
            mapping.date_mapping.date_format
        )
        
        transformed_row["description"] = row[mapping.description_mapping.source_column]
        
        transformed_row["amount"] = transform_amount(
            row[mapping.amount_mapping.source_column],
            mapping.amount_mapping.amount_format
        )
        
        # Apply optional mappings
        for opt_mapping in mapping.optional_mappings:
            if opt_mapping.source_column in row:
                transformed_row[opt_mapping.target_field] = row[opt_mapping.source_column]
        
        transformed_data.append(transformed_row)
    
    return transformed_data
```

### 3. Validation Process

```python
def validate_mapping_with_data(
    mapping: SourceMappingConfig,
    sample_data: List[Dict]
) -> ValidationResult:
    """
    Validate mapping configuration against sample data.
    """
    errors = []
    warnings = []
    
    # Check required columns exist
    for required_col in mapping.required_columns:
        if not any(required_col in row for row in sample_data):
            errors.append(f"Required column '{required_col}' not found")
    
    # Validate data types and formats
    for row in sample_data[:10]:  # Check first 10 rows
        # Date validation
        if mapping.date_mapping.source_column in row:
            try:
                parse_date(row[mapping.date_mapping.source_column], 
                          mapping.date_mapping.date_format)
            except ValueError:
                errors.append(f"Invalid date format in column '{mapping.date_mapping.source_column}'")
        
        # Amount validation
        if mapping.amount_mapping.source_column in row:
            try:
                parse_amount(row[mapping.amount_mapping.source_column])
            except ValueError:
                errors.append(f"Invalid amount format in column '{mapping.amount_mapping.source_column}'")
    
    return ValidationResult(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings
    )
```

## Database Schema (Future)

### 1. Mapping Configurations Table

```sql
CREATE TABLE source_mappings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id VARCHAR(50) UNIQUE NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    description TEXT,
    icon VARCHAR(50),
    config_json TEXT NOT NULL,  -- JSON serialized mapping config
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);
```

### 2. Mapping History Table

```sql
CREATE TABLE mapping_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id VARCHAR(50) NOT NULL,
    action VARCHAR(20) NOT NULL,  -- 'created', 'updated', 'deleted'
    old_config_json TEXT,
    new_config_json TEXT,
    user_id VARCHAR(50),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Security Considerations

### 1. Input Validation
- **Column Name Validation**: Prevent injection attacks in column names
- **JSON Validation**: Validate all JSON input for mapping configurations
- **File Type Validation**: Ensure uploaded files are valid CSV format

### 2. Access Control
- **Mapping Permissions**: Control who can create/modify mappings
- **Source Isolation**: Ensure mappings are source-specific
- **Audit Logging**: Log all mapping changes for compliance

### 3. Data Protection
- **Sensitive Data**: Handle account numbers and financial data securely
- **Data Retention**: Implement appropriate data retention policies
- **Encryption**: Encrypt sensitive mapping configurations

## Performance Considerations

### 1. Caching Strategy
- **Mapping Cache**: Cache frequently used mappings in memory
- **Validation Cache**: Cache validation results for similar files
- **Template Cache**: Cache mapping templates for quick access

### 2. Processing Optimization
- **Batch Processing**: Process multiple files with same mapping
- **Parallel Processing**: Process large files in chunks
- **Memory Management**: Stream large files instead of loading entirely

### 3. Scalability
- **Horizontal Scaling**: Support multiple processing nodes
- **Database Optimization**: Index mapping configurations for fast lookup
- **CDN Integration**: Serve static mapping templates via CDN

## Testing Strategy

### 1. Unit Tests
- **Mapping Validation**: Test mapping configuration validation
- **Data Transformation**: Test data transformation functions
- **API Endpoints**: Test all mapping API endpoints

### 2. Integration Tests
- **End-to-End Processing**: Test complete file processing pipeline
- **Source Detection**: Test source detection with various file formats
- **Error Handling**: Test error scenarios and edge cases

### 3. Performance Tests
- **Large File Processing**: Test processing of large CSV files
- **Concurrent Processing**: Test multiple simultaneous uploads
- **Memory Usage**: Monitor memory usage during processing

## Deployment Considerations

### 1. Configuration Management
- **Environment Variables**: Use environment variables for sensitive config
- **Mapping Backups**: Regular backups of mapping configurations
- **Version Control**: Track mapping configuration changes

### 2. Monitoring
- **Processing Metrics**: Monitor processing times and success rates
- **Error Tracking**: Track and alert on mapping validation errors
- **Usage Analytics**: Monitor mapping usage patterns

### 3. Rollback Strategy
- **Mapping Versioning**: Support rolling back to previous mapping versions
- **Data Recovery**: Ability to reprocess files with different mappings
- **Configuration Backup**: Regular backups of mapping configurations 