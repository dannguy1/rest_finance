# Garlic and Chives - Financial Data Processor

A full-stack web application for processing and validating financial data from multiple sources with intelligent mapping and validation capabilities.

## 🎯 Project Status (November 2024)

**Current Phase**: Phases 1-3 Substantially Complete (69%)  
**Production Launch Target**: Early January 2026  
**Status**: ✅ Monitoring & Testing Infrastructure Complete

### Quick Links
- **Implementation Progress**: [PHASES_1_2_3_README.md](PHASES_1_2_3_README.md) - Quick reference for completed work
- **Detailed Report**: [PHASE_1_2_3_COMPLETION_SUMMARY.md](PHASE_1_2_3_COMPLETION_SUMMARY.md) - Full completion details
- **Project Plan**: [PROJECT_COMPLETION_PLAN.md](PROJECT_COMPLETION_PLAN.md) - 6-8 week roadmap
- **Getting Started**: [QUICK_START.md](QUICK_START.md) - How to run the system

### What's New (Phase 1-3)
- ✅ Prometheus metrics integration (15+ metrics)
- ✅ Grafana dashboards (system health & processing metrics)
- ✅ Enhanced JSON logging with correlation IDs
- ✅ Comprehensive health checks (6 endpoints)
- ✅ Load testing framework (Locust)
- ✅ Automated security audits (Bandit, Safety, Semgrep)
- ✅ 30+ integration tests
- ✅ Route-level error handling with custom exceptions

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
   cp scripts/frontend.env.example scripts/frontend.env
   # Edit the .env files with your configuration
   ```

4. **Run the application**:
   
   **Option A: Using the unified management script (Recommended)**
   ```bash
   # Start both backend and frontend
   ./manage.sh start
   
   # Check status
   ./manage.sh status
   
   # View logs
   ./manage.sh logs
   
   # Stop all services
   ./manage.sh stop
   ```
   
   **Option B: Using individual scripts**
   ```bash
   # Start backend
   ./scripts/manage_backend.sh start -b
   
   # Start frontend (in another terminal)
   ./scripts/manage_frontend.sh start -b
   ```
   
   **Option C: Using Python directly**
   ```bash
   python main.py
   ```

The application will be available at:
- **Frontend**: `http://localhost:3000`
- **Backend API**: `http://localhost:8000`
- **API Docs**: `http://localhost:8000/docs`

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

## Project Status & Planning

**Current Status**: 85% Complete - Entering Final Phase  
**Next Milestone**: Phase 1 Security Completion (Mid-December 2025)  
**Production Target**: Early February 2026

### Quick Links
- 📊 **[PROJECT_STATUS.md](PROJECT_STATUS.md)** - Current status & how to use this repo
- 📋 **[PROJECT_COMPLETION_PLAN.md](PROJECT_COMPLETION_PLAN.md)** - Complete roadmap to production
- 🚀 **[QUICK_START.md](QUICK_START.md)** - How to run the system
- 📖 **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Error handling & best practices
- 🔍 **[CODE_REVIEW.md](CODE_REVIEW.md)** - Comprehensive code review findings
- 📝 **[CHANGELOG.md](CHANGELOG.md)** - Version history and changes

### Documentation
- **[docs/overview.md](docs/overview.md)** - System architecture & development phases
- **[docs/frontend.md](docs/frontend.md)** - Frontend specifications
- **[docs/backend.md](docs/backend.md)** - Backend API design
- **[docs/mapping_technical_spec.md](docs/mapping_technical_spec.md)** - Source mapping system
- **[docs/VALIDATION_SYSTEM.md](docs/VALIDATION_SYSTEM.md)** - Validation system details

## Contributing

**Current Focus**: Completing Phase 1 security improvements. See [PROJECT_COMPLETION_PLAN.md](PROJECT_COMPLETION_PLAN.md) for detailed tasks and timeline.

### For New Contributors

1. **Start Here**: Read [PROJECT_STATUS.md](PROJECT_STATUS.md) to understand current state
2. **Pick a Task**: Check [PROJECT_COMPLETION_PLAN.md](PROJECT_COMPLETION_PLAN.md) for available work
3. **Learn Standards**: Follow [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for coding best practices
4. **Review Docs**: See specific documentation for your area:
   - **[docs/frontend.md](docs/frontend.md)** - UI/UX development
   - **[docs/backend.md](docs/backend.md)** - API and data processing
   - **[docs/mapping_technical_spec.md](docs/mapping_technical_spec.md)** - Source mapping system
   - **[docs/modal_guidelines.md](docs/modal_guidelines.md)** - Modal dialogs

### Development Workflow

```bash
# 1. Start development environment
./manage.sh start

# 2. Make your changes
# ... edit code ...

# 3. Run tests
pytest tests/ -v

# 4. Check code quality
flake8 app/ --max-line-length=120
black app/ --check

# 5. Restart after changes
./manage.sh restart

# 6. Check status
./manage.sh status
```

### Pull Request Process

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes following [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
4. Add tests for new functionality
5. Ensure all tests pass: `pytest tests/ -v`
6. Update documentation as needed
7. Submit a pull request with clear description

## License

MIT License - see LICENSE file for details.

## Support

For technical questions or implementation details:
- **Getting Started**: See [QUICK_START.md](QUICK_START.md)
- **Current Status**: See [PROJECT_STATUS.md](PROJECT_STATUS.md)
- **Implementation Plans**: See [PROJECT_COMPLETION_PLAN.md](PROJECT_COMPLETION_PLAN.md)
- **Code Issues**: See [CODE_REVIEW.md](CODE_REVIEW.md)
- **Best Practices**: See [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
- **Issues & Questions**: Create an issue in the repository 