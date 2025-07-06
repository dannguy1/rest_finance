# Enhanced Mapping Validation System

## Overview

The enhanced validation system provides multiple levels of validation for source mapping configurations, from basic structural checks to comprehensive data testing against sample files. The system now includes a **robust CSV decoder** that handles real-world CSV parsing challenges and provides metadata-driven validation.

## Robust CSV Decoder Implementation

### 🚀 **Core Features**

The robust CSV decoder (`app/utils/csv_loader.py`) provides enterprise-grade CSV parsing with:

- **✅ Flexible Header Detection**: Uses metadata patterns to find headers anywhere in the file
- **✅ Encoding Auto-Detection**: Automatically detects file encoding (UTF-8, UTF-8-BOM, etc.)
- **✅ Malformed Row Filtering**: Intelligently filters out invalid rows while preserving good data
- **✅ Metadata-Driven Validation**: Uses source-specific rules for validation
- **✅ Comprehensive Error Handling**: Detailed logging and graceful error recovery

### 📋 **Metadata Configuration**

Each source can define comprehensive validation metadata:

```json
{
  "source_id": "chase",
  "header_match": [
    ["Posting Date", "Description", "Amount"],
    ["Details", "Posting Date", "Description", "Amount", "Type", "Balance", "Check or Slip #"]
  ],
  "required_columns": ["Posting Date", "Description", "Amount"],
  "min_row_fields": 3,
  "encoding": "utf-8"
}
```

**Metadata Fields:**
- `header_match`: Array of possible header patterns for flexible detection
- `required_columns`: Columns that must be present and non-empty
- `min_row_fields`: Minimum non-empty required fields per row
- `encoding`: Expected file encoding (optional, auto-detected if not specified)

### 🔧 **CLI Validation Tool**

A comprehensive command-line tool for CSV validation:

```bash
# Validate Chase CSV with source metadata
python3 tools/csv_validator.py data/chase/input/AR-Chase-General_Activity_20230618.CSV --source chase --verbose

# Validate with custom metadata
python3 tools/csv_validator.py data/test.csv --metadata '{"required_columns": ["Date", "Amount"]}'

# Save validation results to file
python3 tools/csv_validator.py data/test.csv --source chase --output validation_result.json
```

**CLI Features:**
- ✅ Source-specific metadata lookup
- ✅ Custom metadata support
- ✅ Detailed validation reports
- ✅ Sample data preview
- ✅ JSON output for automation

## Validation Levels

### 🔍 Level 1: Basic Structural Validation
**Always Available** - No sample data required

Checks:
- ✅ Required mappings exist (date, description, amount)
- ✅ No duplicate source columns
- ✅ Mapped columns are in expected_columns list
- ✅ Basic format validation (date/amount formats)

**Example:**
```python
# This will always work, even without sample data
result = mapping_validation_service.validate_mapping_comprehensive(mapping)
```

### 🔍 Level 2: Format Validation
**Uses Sample Data** - Tests format parsing

Checks:
- ✅ Date format parsing (e.g., "MM/DD/YYYY")
- ✅ Amount format validation (USD, EUR, etc.)
- ✅ Basic data type conversion

**Example:**
```python
# Test with sample data
sample_data = [
    {"Date": "01/15/2024", "Description": "SAMPLE", "Amount": "100.00"}
]
result = mapping_validation_service.validate_mapping_comprehensive(mapping, sample_data)
```

### 🔍 Level 3: Data Conversion Testing
**Requires Sample Data** - Tests actual data processing

Checks:
- ✅ Date parsing with real data
- ✅ Amount parsing (handles $, commas, etc.)
- ✅ Success rates for each column
- ✅ Data quality metrics

**Example:**
```python
# Comprehensive testing with sample data
sample_data = [
    {"Posting Date": "01/15/2024", "Description": "ATM WITHDRAWAL", "Amount": "$100.00"},
    {"Posting Date": "01/16/2024", "Description": "DEPOSIT", "Amount": "$500.00"}
]
result = mapping_validation_service.validate_mapping_comprehensive(mapping, sample_data)
```

### 🔍 Level 4: File Validation with Robust CSV Decoder
**Requires Actual File** - Tests against real files using robust parsing

Checks:
- ✅ File format support (CSV with edge case handling)
- ✅ Required columns exist in file
- ✅ Data quality (empty values, format issues)
- ✅ Real-world conversion testing
- ✅ Malformed row detection and filtering
- ✅ Encoding detection and handling

**Example:**
```python
# Test against actual uploaded file with robust parsing
file_path = Path("uploads/chase_data.csv")
result = mapping_validation_service.validate_file_against_mapping(file_path, mapping)
```

## Robust CSV Decoder Features

### 🛡️ **Edge Case Handling**

The robust CSV decoder handles common real-world issues:

**1. Inconsistent Quoting**
```csv
Date,Description,Amount
2023-01-01,"Test, Transaction with comma",100.50
2023-01-02,"Another, Transaction",-50.25
```

**2. Trailing Empty Columns**
```csv
Date,Description,Amount,,
2023-01-01,Test Transaction,100.50,,
2023-01-02,Another Transaction,-50.25,,
```

**3. Mixed Line Endings**
```csv
Date,Description,Amount\r\n
2023-01-01,Test Transaction,100.50\n
2023-01-02,Another Transaction,-50.25\r\n
```

**4. Variable Header Location**
```csv
Some other data
More data
Date,Description,Amount
2023-01-01,Test Transaction,100.50
```

**5. Malformed Rows**
```csv
Date,Description,Amount
2023-01-01,Test Transaction,100.50
2023-01-02,Another Transaction
2023-01-03,Extra,Columns,Here,Too,Many
2023-01-04,Valid Transaction,-50.25
```

### 📊 **Validation Metrics**

The robust decoder provides detailed validation metrics:

```json
{
  "valid": true,
  "rows_loaded": 675,
  "columns": ["Details", "Posting Date", "Description", "Amount", "Type", "Balance", "Check or Slip #"],
  "warnings": [
    "Found 5 malformed rows (excluded)",
    "Detected encoding: utf-8 (confidence: 0.95)"
  ],
  "sample_data": [
    {
      "Details": "CREDIT",
      "Posting Date": "12/30/2022",
      "Description": "ORIG CO NAME:BANKCARD 8076...",
      "Amount": "263.92",
      "Type": "ACH_CREDIT"
    }
  ]
}
```

## API Endpoints

### Basic Validation
```http
POST /api/mappings/{source_id}/validate
Content-Type: application/json

{
  "source_id": "chase",
  "display_name": "Chase Bank",
  "date_mapping": {
    "source_column": "Posting Date",
    "target_field": "date",
    "mapping_type": "date",
    "date_format": "MM/DD/YYYY"
  },
  "description_mapping": {
    "source_column": "Description", 
    "target_field": "description",
    "mapping_type": "description"
  },
  "amount_mapping": {
    "source_column": "Amount",
    "target_field": "amount", 
    "mapping_type": "amount",
    "amount_format": "USD"
  },
  "metadata": {
    "header_match": [
      ["Posting Date", "Description", "Amount"],
      ["Details", "Posting Date", "Description", "Amount", "Type", "Balance", "Check or Slip #"]
    ],
    "required_columns": ["Posting Date", "Description", "Amount"],
    "min_row_fields": 3,
    "encoding": "utf-8"
  },
  "example_data": [
    {"Posting Date": "01/15/2024", "Description": "ATM WITHDRAWAL", "Amount": "$100.00"}
  ]
}
```

**Response:**
```json
{
  "valid": true,
  "errors": [],
  "warnings": [],
  "test_results": {
    "rows_processed": 1,
    "successful_conversions": 3,
    "failed_conversions": 0,
    "column_tests": {
      "date": {
        "source_column": "Posting Date",
        "conversion_success": 1,
        "conversion_failures": 0,
        "success_rate": 1.0
      }
    }
  },
  "robust_parsing": {
    "encoding_detected": "utf-8",
    "confidence": 0.95,
    "malformed_rows_filtered": 0,
    "header_row_found": 1
  },
  "summary": {
    "total_checks": 5,
    "error_count": 0,
    "warning_count": 0,
    "sample_data_tested": true
  }
}
```

### File Testing with Robust Parser
```http
POST /api/mappings/{source_id}/test-file
Content-Type: application/json

{
  "file_path": "/uploads/chase_data.csv",
  "use_robust_parser": true
}
```

### Sample Template
```http
GET /api/mappings/{source_id}/sample-template
```

**Response:**
```json
{
  "source_id": "chase",
  "sample_template": [
    {
      "Posting Date": "01/15/2024",
      "Description": "SAMPLE TRANSACTION", 
      "Amount": "100.00"
    }
  ],
  "metadata_template": {
    "header_match": [
      ["Posting Date", "Description", "Amount"]
    ],
    "required_columns": ["Posting Date", "Description", "Amount"],
    "min_row_fields": 3,
    "encoding": "utf-8"
  },
  "instructions": [
    "Use this template to create sample data for testing your mapping",
    "Replace the sample values with realistic data from your source",
    "Include multiple rows to test different scenarios",
    "The robust parser will handle edge cases automatically"
  ]
}
```

## Validation Results

### Success Case with Robust Parser
```json
{
  "valid": true,
  "errors": [],
  "warnings": [
    "Found 3 malformed rows (filtered out)",
    "Detected encoding: utf-8 (confidence: 0.95)"
  ],
  "test_results": {
    "rows_processed": 10,
    "successful_conversions": 30,
    "failed_conversions": 0,
    "column_tests": {
      "date": {
        "source_column": "Posting Date",
        "conversion_success": 10,
        "conversion_failures": 0,
        "success_rate": 1.0
      },
      "description": {
        "source_column": "Description", 
        "conversion_success": 10,
        "conversion_failures": 0,
        "success_rate": 1.0
      },
      "amount": {
        "source_column": "Amount",
        "conversion_success": 10, 
        "conversion_failures": 0,
        "success_rate": 1.0
      }
    }
  },
  "robust_parsing": {
    "encoding_detected": "utf-8",
    "confidence": 0.95,
    "malformed_rows_filtered": 3,
    "header_row_found": 1,
    "total_rows_processed": 13,
    "valid_rows_kept": 10
  }
}
```

### Error Case with Robust Parser
```json
{
  "valid": false,
  "errors": [
    "Date mapping is required",
    "Required column 'Posting Date' not found in sample data"
  ],
  "warnings": [
    "Low conversion success rate for amount: 60.0%",
    "Found 5 malformed rows (filtered out)",
    "Detected encoding: utf-8 (confidence: 0.85)"
  ],
  "test_results": {
    "rows_processed": 5,
    "successful_conversions": 8,
    "failed_conversions": 7,
    "column_tests": {
      "amount": {
        "source_column": "Amount",
        "conversion_success": 3,
        "conversion_failures": 2,
        "success_rate": 0.6
      }
    }
  },
  "robust_parsing": {
    "encoding_detected": "utf-8",
    "confidence": 0.85,
    "malformed_rows_filtered": 5,
    "header_row_found": 1,
    "total_rows_processed": 10,
    "valid_rows_kept": 5
  }
}
```

## User Experience

### 1. **No Sample Data Required**
Users can validate basic mapping structure immediately:
- ✅ Check required mappings exist
- ✅ Validate no duplicate columns
- ✅ Test format specifications
- ✅ Validate metadata configuration

### 2. **Sample Data Enhances Validation**
Users can provide sample data for thorough testing:
- ✅ Test actual data conversion
- ✅ Validate date/amount parsing
- ✅ Measure success rates
- ✅ Identify potential issues
- ✅ Test robust parser edge case handling

### 3. **File Upload for Real Testing**
Users can test against actual files with robust parsing:
- ✅ Validate against real data
- ✅ Check file format compatibility
- ✅ Test data quality
- ✅ Real-world validation
- ✅ Automatic encoding detection
- ✅ Malformed row filtering

### 4. **CLI Tool for Quick Validation**
Users can validate files from command line:
- ✅ Quick validation without web interface
- ✅ Detailed reports with sample data
- ✅ Integration with CI/CD pipelines
- ✅ Batch processing capabilities

### 5. **Detailed Feedback**
Validation provides comprehensive feedback:
- ✅ Clear error messages
- ✅ Warning for potential issues
- ✅ Success rate metrics
- ✅ Column-specific test results
- ✅ Robust parser statistics
- ✅ Encoding detection results

## Implementation Details

### Robust CSV Loader
```python
class RobustCSVLoader:
    def load_csv_robust(self, file_path: Path, metadata: Optional[dict] = None) -> pd.DataFrame:
        """
        Load CSV file with robust parsing and metadata-driven validation.
        
        Features:
        - Flexible header detection using header_match patterns
        - Automatic encoding detection
        - Malformed row filtering
        - Metadata-driven validation
        - Comprehensive error handling
        """
```

### Validation Service
```python
class MappingValidationService:
    def validate_mapping_comprehensive(self, mapping, sample_data=None):
        """Comprehensive validation with optional sample data."""
        
    def validate_file_against_mapping(self, file_path, mapping):
        """Validate against actual file using robust parser."""
        
    def generate_sample_data_template(self, mapping):
        """Generate template for sample data."""
```

### CLI Validation Tool
```python
class CSVValidator:
    def validate_csv(self, file_path: Path, source_id: Optional[str] = None, 
                    metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Validate CSV file using metadata-driven validation.
        
        Features:
        - Source-specific metadata lookup
        - Custom metadata support
        - Detailed validation reports
        - Sample data preview
        - JSON output for automation
        """
```

### Integration Points
- **API Routes**: Enhanced validation endpoints with robust parser
- **Web UI**: Real-time validation feedback with parser statistics
- **File Processing**: Pre-processing validation with robust parsing
- **Error Handling**: Detailed error reporting with parser diagnostics
- **CLI Tool**: Command-line validation for automation

## Best Practices

### 1. **Always Start with Basic Validation**
```python
# Basic validation (no sample data needed)
result = mapping_validation_service.validate_mapping_comprehensive(mapping)
if not result['valid']:
    # Fix structural issues first
    return result
```

### 2. **Add Sample Data for Thorough Testing**
```python
# Enhanced validation with sample data
result = mapping_validation_service.validate_mapping_comprehensive(
    mapping, sample_data=example_data
)
```

### 3. **Test with Real Files Using Robust Parser**
```python
# Real-world validation with robust parsing
result = mapping_validation_service.validate_file_against_mapping(
    file_path, mapping
)
```

### 4. **Use CLI Tool for Quick Validation**
```bash
# Quick validation from command line
python3 tools/csv_validator.py data/chase/input/file.csv --source chase --verbose
```

### 5. **Monitor Success Rates**
- ✅ > 95%: Excellent mapping
- ✅ 80-95%: Good mapping (check warnings)
- ✅ < 80%: Needs improvement

### 6. **Configure Metadata for Robust Parsing**
```json
{
  "header_match": [
    ["Posting Date", "Description", "Amount"],
    ["Details", "Posting Date", "Description", "Amount", "Type"]
  ],
  "required_columns": ["Posting Date", "Description", "Amount"],
  "min_row_fields": 3,
  "encoding": "utf-8"
}
```

## Error Handling

### Common Errors
1. **Missing Required Mappings**
   - Date mapping is required
   - Description mapping is required
   - Amount mapping is required

2. **Column Issues**
   - Duplicate source columns found
   - Required column not found in sample data
   - Expected columns missing mapped columns

3. **Format Issues**
   - Invalid date format
   - Unknown amount format
   - Low conversion success rate

4. **Robust Parser Issues**
   - Header row not found with any pattern
   - Encoding detection failed
   - Too many malformed rows (> 70%)

### Warning Types
1. **Data Quality**
   - Low conversion success rate
   - Empty values in required columns
   - Optional column not found

2. **Format Warnings**
   - Unknown amount format
   - Date format may need adjustment

3. **Robust Parser Warnings**
   - Malformed rows detected and filtered
   - Low encoding detection confidence
   - Header detection used fallback method

## Testing

### Comprehensive Test Suite
The robust CSV decoder includes 20 comprehensive tests covering:

- ✅ Standard CSV parsing
- ✅ Quoted fields with commas
- ✅ Trailing empty columns
- ✅ Variable header location
- ✅ Mixed line endings
- ✅ Empty rows
- ✅ Malformed rows
- ✅ Encoding detection
- ✅ Metadata-driven validation
- ✅ Header pattern matching
- ✅ Chase-like complex structures
- ✅ Strict validation rules
- ✅ CLI tool integration

### Test Coverage
```bash
# Run all tests
python3 -m pytest tests/test_csv_loader.py -v

# Run specific test categories
python3 -m pytest tests/test_csv_loader.py::TestRobustCSVLoader::test_csv_with_metadata_validation -v
```

## Production Integration

### Current Status
- ✅ **Robust CSV Loader**: Production-ready with comprehensive edge case handling
- ✅ **CLI Validation Tool**: Fully functional with detailed reporting
- ✅ **Metadata Configuration**: Enhanced Chase config with robust parsing support
- ✅ **Test Suite**: 20/20 tests passing with comprehensive coverage
- ✅ **Production Testing**: Successfully processes Chase (675 transactions) and BoA files

### Performance Metrics
- **Chase Processing**: 675 transactions parsed successfully
- **Bank of America Processing**: 2785 transactions parsed successfully
- **Error Rate**: 0% for well-formed files
- **Malformed Row Filtering**: Automatic detection and exclusion
- **Encoding Detection**: 95%+ confidence for UTF-8 files

## Conclusion

The enhanced validation system with robust CSV decoder provides a comprehensive approach to ensuring mapping configurations work correctly:

- **Level 1**: Basic structural validation (always available)
- **Level 2**: Format validation (with sample data)
- **Level 3**: Data conversion testing (with sample data)
- **Level 4**: File validation with robust CSV parser (with actual files)

The robust CSV decoder handles real-world CSV parsing challenges including:
- Flexible header detection
- Automatic encoding detection
- Malformed row filtering
- Metadata-driven validation
- Comprehensive error handling

This multi-level approach ensures users can validate their mappings at whatever level of detail they need, from basic structure checks to comprehensive real-world testing with enterprise-grade CSV parsing. 