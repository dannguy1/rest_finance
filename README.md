# Garlic and Chives - Financial Data Processor

A full-stack web application for processing and validating financial data from multiple sources with intelligent mapping and validation capabilities.

## Features

- **Multi-Source Data Processing**: Support for various financial institutions (Chase, Bank of America, etc.)
- **Intelligent Column Mapping**: Automatic detection and mapping of financial data columns
- **Advanced Validation**: Multi-level validation including structural, format, and data quality checks
- **Metadata-Based Processing**: Enhanced validation using saved metadata from previous uploads
- **Real-time Processing**: WebSocket support for real-time status updates
- **Modern Web Interface**: Clean, responsive UI built with FastAPI and Jinja2
- **PDF Merchant Statement Processing**: Extract and convert merchant statement PDFs to CSV format
- **Multi-Level Table Sorting**: Advanced sorting with primary, secondary, and tertiary levels

## PDF Extraction & Processing

### Merchant Statement Support
- **GG (Garlic & Chives)**: Process merchant statements with "SUMMARY OF MONETARY BATCHES" section
- **AR (Example)**: Support for additional merchant types
- **Flexible Column Matching**: Handles OCR artifacts, case variations, and spacing differences
- **Robust Row Parsing**: Uses regex patterns to handle variable formatting and missing fields
- **Date Formatting**: Converts MM/DD dates to YYYY-MM-DD format with year input
- **Validation & Cleanup**: Removes invalid rows and provides detailed extraction statistics

### CLI Tools
```bash
# Extract merchant statement
python3 scripts/extract_pdf_table.py --pdf data/gg/input/Jan2025.pdf --vendor gg --year 2025

# With debug information
python3 scripts/extract_pdf_table.py --pdf data/gg/input/Jan2025.pdf --vendor gg --year 2025 --debug

# Custom output path
python3 scripts/extract_pdf_table.py --pdf data/gg/input/Jan2025.pdf --vendor gg --year 2025 --output data/gg/processed/Jan2025.csv
```

### Adding New Vendors
1. Create configuration file in `config/` directory
2. Define section header, expected columns, and validation rules
3. Test extraction with debug mode
4. Integrate with web interface

See `scripts/README.md` for detailed documentation.

## Technology Stack

- **Backend**: FastAPI, Python 3.10+
- **Frontend**: Jinja2 templates, JavaScript
- **Data Processing**: Pandas, Pydantic
- **Database**: SQLite (via SQLAlchemy)
- **Validation**: Custom validation service with metadata support
- **PDF Processing**: PyMuPDF for text extraction and table parsing

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd rest_finance
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   cp scripts/backend.env.example scripts/backend.env
   # Edit scripts/backend.env with your configuration
   ```

4. **Run the application**:
   ```bash
   python main.py
   ```

The application will be available at `http://localhost:8000`

## Project Structure

```
rest_finance/
├── app/
│   ├── api/              # FastAPI routes and endpoints
│   ├── config/           # Configuration and settings
│   ├── middleware/       # Custom middleware
│   ├── models/           # Data models
│   ├── services/         # Business logic services
│   ├── static/           # Static assets (CSS, JS)
│   ├── templates/        # Jinja2 templates
│   └── utils/            # Utility functions
├── config/               # Configuration files (including vendor PDF extraction configs)
├── data/                 # Data storage
├── scripts/              # Utility scripts (including PDF extraction tools)
├── tests/                # Test files
└── docs/                 # Documentation
```

## Key Components

### Source Mapping System
- Intelligent column mapping for different financial institutions
- Automatic detection of date, description, and amount columns
- Support for optional columns and custom formats

### Validation Service
- Multi-level validation (structural, format, data quality)
- Metadata-based validation using saved column information
- Real-time validation feedback

### File Processing
- Support for CSV file uploads
- Automatic format detection and correction
- Batch processing capabilities

### PDF Processing Service
- Merchant statement PDF extraction
- Vendor-specific configuration and validation
- Robust table parsing with error handling
- Integration with main data pipeline

## API Endpoints

- `GET /` - Main application interface
- `GET /api/sources` - List available data sources
- `POST /api/files/upload/{source_id}` - Upload files for processing
- `GET /api/files/validate/{source_id}` - Validate uploaded files
- `GET /api/sample-data/sources/{source_id}/metadata` - Get source metadata

## Development

### Running Tests
```bash
pytest tests/
```

### Code Formatting
```bash
black .
```

### Type Checking
```bash
mypy app/
```

## Configuration

The application uses environment variables for configuration. Key settings include:

- `HOST`: Application host (default: 0.0.0.0)
- `PORT`: Application port (default: 8000)
- `DEBUG`: Debug mode (default: False)
- `LOG_LEVEL`: Logging level (default: INFO)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions, please create an issue in the repository. 