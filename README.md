# Garlic and Chives - Financial Data Processor

A full-stack web application for processing and validating financial data from multiple sources with intelligent mapping and validation capabilities.

## 🎯 Project Status

**Overall**: Core functionality complete — processing, validation, PDF extraction, mapping, monitoring, and testing infrastructure are all implemented.

### Quick Links
- **Getting Started**: [QUICK_START.md](QUICK_START.md) - How to run the system
- **Developer Reference**: [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Error handling & best practices
- **API Reference**: [docs/api_reference.md](docs/api_reference.md) - Full endpoint listing
- **Architecture**: [docs/overview.md](docs/overview.md) - System design
- **Bank Analytics & Patterns**: [docs/bank_analytics.md](docs/bank_analytics.md) - Adding merchant/payroll/custom patterns

### Implemented Features
- ✅ Multi-source CSV processing (6 sources: BoA, Chase, Restaurant Depot, Sysco, GG, AR)
- ✅ PDF merchant statement extraction (pdfplumber, PyMuPDF, tabula-py)
- ✅ Intelligent column mapping with JSON config per source
- ✅ Multi-level validation (structural, format, data quality, metadata-driven)
- ✅ Year/month-based output organization
- ✅ Bank statement analytics — Group by Description, Monthly Summary, Amount Analysis, Trends
- ✅ **Merchant Analysis** — pattern-based card-deposit extraction per bank source
- ✅ **Payroll Analysis** — pattern-based payroll transfer extraction per bank source
- ✅ **Deposit Verification** — match merchant batch totals against bank deposits with discrepancy reporting
- ✅ Location-centric UI — GG and AR contexts selectable via navbar dropdown
- ✅ Prometheus metrics (15+ counters/histograms/gauges)
- ✅ Grafana dashboard configs
- ✅ Enhanced JSON logging with correlation IDs
- ✅ 6 health check endpoints (liveness, readiness, Prometheus scrape)
- ✅ Rate limiting (slowapi)
- ✅ Custom exception hierarchy with HTTP error factories
- ✅ File locking and MIME-type validation
- ✅ Load testing framework (Locust)
- ✅ Security scanning (Bandit, Safety, Semgrep)
- ✅ Integration test suite

## Features

- **Multi-Source Data Processing**: Chase, Bank of America, Restaurant Depot, Sysco, GG, AR
- **Intelligent Column Mapping**: JSON-configured per-source mapping with automatic column detection
- **Advanced Validation**: Multi-level validation — structural, format, data quality, and metadata-driven
- **Metadata-Based Processing**: Validation cross-referenced against saved sample metadata
- **Real-time Processing**: WebSocket support for live status updates
- **Modern Web Interface**: Server-side Jinja2 templates + vanilla JS (Bootstrap 5, Chart.js)
- **PDF Merchant Statement Processing**: Extract and convert merchant PDFs to CSV (pdfplumber, PyMuPDF, tabula-py)
- **Multi-Level Table Sorting**: Advanced sorting with primary, secondary, and tertiary levels
- **Observability**: Prometheus metrics, Grafana dashboards, structured JSON logging

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

- **Backend**: FastAPI, Python 3.10+, uvicorn
- **Frontend**: Jinja2 templates, JavaScript (Bootstrap 5, Chart.js)
- **Data Processing**: Pandas, Pydantic v2
- **PDF Processing**: pdfplumber, PyMuPDF, tabula-py
- **Validation**: python-magic (MIME type), chardet (encoding detection)
- **Observability**: prometheus-client, structured JSON logging
- **Rate Limiting**: slowapi
- **Load Testing**: Locust
- **Security Scanning**: Bandit, Safety, Semgrep
- **Storage**: File system (no active database); SQLite/SQLAlchemy available

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
- **Web UI**: `http://localhost:8000`
- **Backend API**: `http://localhost:8000/api`
- **API Docs** (debug mode only): `http://localhost:8000/api/docs`

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

See **[docs/api_reference.md](docs/api_reference.md)** for the full endpoint listing. Key groups:

| Prefix | Description |
|---|---|
| `GET /` | Web UI pages (served by Jinja2 templates) |
| `GET /api` | API info |
| `/api/health` | Liveness, readiness, Prometheus scrape endpoints |
| `/api/files` | Upload, list, preview, validate, download, backup |
| `/api/processing` | Trigger processing, check status, browse outputs |
| `/api/mappings` | CRUD for source mapping configurations |
| `/api/files/analytics` | Group-by, monthly summaries, trends |
| `/api/sample-data` | Sample metadata management |

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

### Quick Links
- 📊 **[PROJECT_STATUS.md](PROJECT_STATUS.md)** - Current status & how to use this repo
- 🚀 **[QUICK_START.md](QUICK_START.md)** - How to run the system
- 📖 **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Error handling & best practices
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