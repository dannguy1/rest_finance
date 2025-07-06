# Garlic and Chives - Financial Data Processor

A full-stack web application for processing and validating financial data from multiple sources with intelligent mapping and validation capabilities.

## Features

- **Multi-Source Data Processing**: Support for various financial institutions (Chase, Bank of America, etc.)
- **Intelligent Column Mapping**: Automatic detection and mapping of financial data columns
- **Advanced Validation**: Multi-level validation including structural, format, and data quality checks
- **Metadata-Based Processing**: Enhanced validation using saved metadata from previous uploads
- **Real-time Processing**: WebSocket support for real-time status updates
- **Modern Web Interface**: Clean, responsive UI built with FastAPI and Jinja2

## Technology Stack

- **Backend**: FastAPI, Python 3.10+
- **Frontend**: Jinja2 templates, JavaScript
- **Data Processing**: Pandas, Pydantic
- **Database**: SQLite (via SQLAlchemy)
- **Validation**: Custom validation service with metadata support

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
├── config/               # Configuration files
├── data/                 # Data storage
├── scripts/              # Utility scripts
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