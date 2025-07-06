# Source Mapping Example: Adding a New Bank

## Scenario

A user wants to add support for a new bank called "Local Credit Union" that exports CSV files with different column names than the existing sources.

## Step 1: Upload and Analyze

### User uploads a sample file:
```csv
Transaction Date,Transaction Description,Transaction Amount,Account Number,Transaction Type
01/15/2024,VERIZON WIRELESS,-421.50,1234567890,DEBIT
01/20/2024,GROCERY STORE,-45.67,1234567890,DEBIT
01/25/2024,PAYROLL DEPOSIT,2500.00,1234567890,CREDIT
```

### System analyzes the file and suggests mappings:
```json
{
  "analysis": {
    "detected_columns": [
      "Transaction Date", 
      "Transaction Description", 
      "Transaction Amount", 
      "Account Number", 
      "Transaction Type"
    ],
    "suggested_mappings": {
      "date_mapping": {
        "source_column": "Transaction Date",
        "confidence": 0.95
      },
      "description_mapping": {
        "source_column": "Transaction Description",
        "confidence": 0.90
      },
      "amount_mapping": {
        "source_column": "Transaction Amount",
        "confidence": 0.85
      }
    },
    "format_analysis": {
      "date_format": "MM/DD/YYYY",
      "amount_format": "USD",
      "has_negative_amounts": true
    }
  }
}
```

## Step 2: Create Mapping Configuration

### User creates a new mapping via the web interface:

```json
{
  "source_id": "localcreditunion",
  "display_name": "Local Credit Union",
  "description": "Local Credit Union bank statement processing",
  "icon": "bank",
  "date_mapping": {
    "source_column": "Transaction Date",
    "target_field": "date",
    "mapping_type": "date",
    "required": true,
    "date_format": "MM/DD/YYYY",
    "description": "Transaction date"
  },
  "description_mapping": {
    "source_column": "Transaction Description",
    "target_field": "description",
    "mapping_type": "description",
    "required": true,
    "description": "Transaction description"
  },
  "amount_mapping": {
    "source_column": "Transaction Amount",
    "target_field": "amount",
    "mapping_type": "amount",
    "required": true,
    "amount_format": "USD",
    "description": "Transaction amount"
  },
  "optional_mappings": [
    {
      "source_column": "Account Number",
      "target_field": "account_id",
      "mapping_type": "optional",
      "required": false,
      "description": "Account identifier"
    },
    {
      "source_column": "Transaction Type",
      "target_field": "transaction_type",
      "mapping_type": "optional",
      "required": false,
      "description": "Transaction type (DEBIT/CREDIT)"
    }
  ],
  "expected_columns": [
    "Transaction Date",
    "Transaction Description", 
    "Transaction Amount",
    "Account Number",
    "Transaction Type"
  ],
  "required_columns": [
    "Transaction Date",
    "Transaction Description",
    "Transaction Amount"
  ],
  "example_data": [
    {
      "Transaction Date": "01/15/2024",
      "Transaction Description": "VERIZON WIRELESS",
      "Transaction Amount": "-421.50",
      "Account Number": "1234567890",
      "Transaction Type": "DEBIT"
    }
  ]
}
```

## Step 3: Validate Mapping

### System validates the mapping against the sample data:

```json
{
  "valid": true,
  "errors": [],
  "warnings": [],
  "mapping_summary": {
    "source_id": "localcreditunion",
    "display_name": "Local Credit Union",
    "required_columns": [
      "Transaction Date",
      "Transaction Description", 
      "Transaction Amount"
    ],
    "optional_columns": [
      "Account Number",
      "Transaction Type"
    ]
  }
}
```

## Step 4: Process Data

### User uploads a full statement file and processes it:

**Input CSV:**
```csv
Transaction Date,Transaction Description,Transaction Amount,Account Number,Transaction Type
01/15/2024,VERIZON WIRELESS,-421.50,1234567890,DEBIT
01/20/2024,GROCERY STORE,-45.67,1234567890,DEBIT
01/25/2024,PAYROLL DEPOSIT,2500.00,1234567890,CREDIT
01/30/2024,UTILITY BILL,-125.00,1234567890,DEBIT
02/05/2024,GAS STATION,-35.50,1234567890,DEBIT
```

**Normalized Output CSV:**
```csv
Date,Description,Amount,Source File,Account ID,Transaction Type
2024-01-15,VERIZON WIRELESS,-421.50,localcreditunion_statement_2024.csv,1234567890,DEBIT
2024-01-20,GROCERY STORE,-45.67,localcreditunion_statement_2024.csv,1234567890,DEBIT
2024-01-25,PAYROLL DEPOSIT,2500.00,localcreditunion_statement_2024.csv,1234567890,CREDIT
2024-01-30,UTILITY BILL,-125.00,localcreditunion_statement_2024.csv,1234567890,DEBIT
2024-02-05,GAS STATION,-35.50,localcreditunion_statement_2024.csv,1234567890,DEBIT
```

## Step 5: Future Usage

### The user can now use the additional fields for analysis:

**Category Analysis:**
```sql
SELECT 
  transaction_type,
  COUNT(*) as transaction_count,
  SUM(amount) as total_amount
FROM processed_transactions 
WHERE source_file LIKE '%localcreditunion%'
GROUP BY transaction_type;
```

**Account Tracking:**
```sql
SELECT 
  account_id,
  COUNT(*) as transaction_count,
  SUM(amount) as net_flow
FROM processed_transactions 
WHERE source_file LIKE '%localcreditunion%'
GROUP BY account_id;
```

## Benefits Demonstrated

### 1. **Flexibility**
- New bank added without code changes
- Different column names handled automatically
- Custom fields (Account Number, Transaction Type) preserved

### 2. **Data Quality**
- Dates standardized to YYYY-MM-DD format
- Amounts normalized (negative for debits)
- All transactions include source file reference

### 3. **Future Extensibility**
- Account ID field enables multi-account analysis
- Transaction Type enables spending pattern analysis
- Easy to add more optional fields (Category, Reference, etc.)

### 4. **User Empowerment**
- User configured mapping themselves
- Visual feedback showed how data would be transformed
- Validation ensured data quality before processing

## Advanced Example: Adding Category Detection

### User wants to add automatic category detection:

```json
{
  "optional_mappings": [
    {
      "source_column": "Account Number",
      "target_field": "account_id",
      "mapping_type": "optional",
      "required": false
    },
    {
      "source_column": "Transaction Type", 
      "target_field": "transaction_type",
      "mapping_type": "optional",
      "required": false
    },
    {
      "source_column": "Transaction Description",
      "target_field": "category",
      "mapping_type": "optional", 
      "required": false,
      "transformation": "category_detector",
      "description": "Auto-detected category based on description"
    }
  ]
}
```

### System applies category detection during processing:

**Input:**
```csv
Transaction Date,Transaction Description,Transaction Amount
01/15/2024,VERIZON WIRELESS,-421.50
01/20/2024,GROCERY STORE,-45.67
01/25/2024,PAYROLL DEPOSIT,2500.00
```

**Output with Categories:**
```csv
Date,Description,Amount,Source File,Account ID,Transaction Type,Category
2024-01-15,VERIZON WIRELESS,-421.50,localcreditunion_statement_2024.csv,1234567890,DEBIT,UTILITIES
2024-01-20,GROCERY STORE,-45.67,localcreditunion_statement_2024.csv,1234567890,DEBIT,FOOD
2024-01-25,PAYROLL DEPOSIT,2500.00,localcreditunion_statement_2024.csv,1234567890,CREDIT,INCOME
```

### This enables advanced analytics:

**Spending by Category:**
```sql
SELECT 
  category,
  COUNT(*) as transaction_count,
  SUM(amount) as total_spent
FROM processed_transactions 
WHERE amount < 0  -- Only expenses
GROUP BY category
ORDER BY total_spent DESC;
```

**Monthly Category Trends:**
```sql
SELECT 
  DATE_FORMAT(date, '%Y-%m') as month,
  category,
  SUM(amount) as total_spent
FROM processed_transactions 
WHERE amount < 0
GROUP BY month, category
ORDER BY month, total_spent DESC;
```

## Conclusion

This example demonstrates how the mapping system provides:

1. **Immediate Value**: Quick addition of new data sources
2. **Data Quality**: Consistent, normalized output regardless of source format
3. **Future Growth**: Easy addition of new fields and transformations
4. **User Control**: Self-service configuration without technical expertise
5. **Analytics Ready**: Rich data structure supports advanced analysis

The system scales from simple bank statements to complex multi-account, multi-category financial analysis while maintaining simplicity for end users. 