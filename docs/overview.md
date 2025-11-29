# Full-Stack Garlic and Chives - Project Overview

## Project Summary

**Garlic and Chives** is a redesigned application that processes financial data from multiple sources and organizes output by source, year, and month. The system provides automated data processing with structured file organization, enhanced data aggregation capabilities, and a sophisticated source mapping system with persistent metadata management.

## System Architecture

### High-Level Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │   File System   │
│   (FastAPI +    │◄──►│   (FastAPI)     │◄──►│   Storage       │
│   Jinja2)       │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Technology Stack Overview

#### Frontend
- **Framework**: Server-side rendered with Jinja2 templates
- **UI Framework**: Bootstrap 5.3.6 for styling and components
- **Icons**: Bootstrap Icons
- **Charts**: Chart.js for data visualization
- **JavaScript**: Vanilla JavaScript for client-side interactions
- **Real-time**: WebSocket for live updates

#### Backend
- **Framework**: FastAPI for backend API and server-side rendering
- **Language**: Python 3.10+
- **File Processing**: Python csv module, pandas for data manipulation
- **Validation**: Pydantic for data validation and serialization
- **Logging**: Python logging module with structured logging
- **Testing**: pytest, httpx for API testing
- **Server**: Uvicorn ASGI server
- **Rate Limiting**: slowapi for API rate limiting

#### Database (Administrative Only)
- **Database**: SQLite for administrative metadata storage
- **Purpose**: Administrative data only (processing history, job tracking, system logs)
- **User Data**: All user data (financial transactions, processed files) stored in file system only

## Core Features

### 1. Multi-Source Data Processing
- **Bank of America**: CSV statement processing with transaction grouping and status filtering
- **Chase**: Credit card statement processing with flexible header detection
- **Restaurant Depot**: Invoice receipt processing
- **Sysco**: Invoice processing
- **GG (Garlic & Chives)**: Merchant statement PDF processing
- **AR**: Additional merchant statement processing

### 2. Enhanced Source Mapping System
- **Persistent Configuration**: Source mappings stored as JSON files in `config/` directory with full metadata
- **Metadata Management**: Processed sample data metadata stored in `data/source_metadata/`
- **Auto-Loading**: Existing metadata automatically loads when source ID is entered
- **Settings Restore**: Full configuration backup and restore including sample data
- **Validation**: Multi-level validation system with robust CSV parsing (see `docs/VALIDATION_SYSTEM.md`)
- **Flexible Header Matching**: Supports multiple header patterns per source for variant file formats

### 3. Robust CSV Processing
- **Enterprise-Grade Parsing**: Handles malformed rows, encoding detection, and variable header locations
- **Metadata-Driven Validation**: Uses source-specific rules for comprehensive validation
- **Automatic Error Recovery**: Filters invalid rows while preserving good data
- **Multiple Encoding Support**: Auto-detects UTF-8, UTF-8-BOM, and other encodings
- **CLI Validation Tool**: Command-line interface for batch validation and automation

### 4. Automated File Organization
- **Year/Month Collation**: Automatic organization by year and month
- **Source Separation**: Dedicated directories for each data source (`data/{source}/input/` and `data/{source}/output/`)
- **Structured Output**: Consistent CSV format with source file tracking

### 5. Real-Time Processing
- **WebSocket Updates**: Live processing status and progress (via `/ws` endpoint)
- **Drag & Drop Upload**: Source-specific upload zones with file validation
- **Progress Tracking**: Real-time feedback during file processing
- **Background Processing**: Asynchronous processing with status polling

### 6. Data Visualization & Analytics
- **Chart.js Integration**: Spending patterns and analytics visualization
- **Responsive Tables**: Bootstrap-styled data tables with sorting and filtering
- **Interactive Dashboard**: Real-time data overview with file statistics
- **Source Analytics**: Per-source analytics and processing history

## Project Structure
```
rest_finance/
├── app/                    # Main application code
│   ├── api/               # API routes
│   │   ├── main.py        # FastAPI application entry point
│   │   └── routes/        # API route modules
│   │       ├── file_routes.py      # File management API
│   │       ├── processing_routes.py # Processing API
│   │       ├── mapping_routes.py   # Source mapping API
│   │       ├── web_routes.py       # Web page routes
│   │       └── health_routes.py    # Health check endpoints
│   ├── models/            # Pydantic models
│   ├── services/          # Business logic
│   │   ├── file_service.py           # File operations
│   │   ├── processing_service.py     # Data processing
│   │   ├── validation_service.py     # Data validation
│   │   ├── sample_data_service.py    # Sample data management
│   │   └── mapping_validation_service.py # Mapping validation
│   ├── templates/         # Jinja2 HTML templates
│   │   ├── base.html      # Base template
│   │   ├── source.html    # Source-specific page template
│   │   ├── mapping.html   # Enhanced mapping modal
│   │   └── pages/         # Page-specific templates
│   ├── static/            # Static assets (CSS, JS)
│   │   ├── css/           # Stylesheets
│   │   └── js/            # JavaScript files
│   ├── middleware/        # Middleware components
│   ├── utils/             # Utility functions
│   └── config/            # Configuration management
├── config/                # Source mapping configurations
│   ├── {source_id}.json  # Source-specific mapping configs
│   └── settings_sample.py # Sample configuration template
├── data/                  # Data storage (excluded from git)
│   ├── source_metadata/   # Processed sample data metadata
│   ├── {source_id}/       # User uploaded files
│   └── backups/           # Configuration backups
├── docs/                  # Documentation
├── tests/                 # Test files
├── logs/                  # Application logs (excluded from git)
├── requirements.txt       # Python dependencies
├── pyproject.toml         # Project configuration
└── .gitignore            # Privacy protection configuration
```

## Data Processing Pipeline

### Processing Flow
```
Upload Sample File → Generate Metadata → Configure Mapping → Validate Configuration → Upload Data Files → Robust CSV Parsing → Data Validation → Year/Month Collation → CSV Output Generation → File Preview/Download
```

### Detailed Pipeline Steps
1. **Sample File Upload**: Upload representative CSV file for metadata extraction
2. **Metadata Generation**: Process sample file to detect columns, formats, and patterns
3. **Mapping Configuration**: Configure source-specific column mappings using auto-detected metadata
4. **Validation**: Multi-level validation (structural, format, data conversion, file testing)
5. **Data File Upload**: Upload actual financial data files for processing
6. **Robust CSV Parsing**: 
   - Automatic encoding detection (UTF-8, UTF-8-BOM, etc.)
   - Flexible header location detection using metadata patterns
   - Malformed row filtering with comprehensive error logging
   - Metadata-driven validation rules
7. **Data Transformation**: Apply mappings to normalize data structure
8. **Year/Month Organization**: Automatically group transactions by year and month
9. **CSV Generation**: Create standardized output files with source tracking
10. **Preview & Download**: View processed data and download monthly files

### Output Organization
Each data source follows the structure:
```
data/{source}/
├── input/                     # Uploaded raw files
│   └── *.csv
└── output/                    # Processed monthly files
    └── {Year}/
        └── {MM_YYYY}.csv
```

Example:
```
data/bankofamerica/output/2024/01_2024.csv
├── Date, Description, Amount, Source File
├── 01/15/2024, VERIZON WIRELESS, -421.50, boa_statement_2024.csv
├── 01/20/2024, VERIZON WIRELESS, -301.93, boa_statement_2024.csv
└── 01/25/2024, GROCERY STORE, -45.67, boa_statement_2024.csv

data/chase/output/2023/12_2023.csv
├── Date, Description, Amount, Type, Source File
├── 12/30/2022, ORIG CO NAME:BANKCARD..., 263.92, ACH_CREDIT, chase_activity.csv
└── 12/29/2022, Online Transfer to CHK..., -15000.00, ACCT_XFER, chase_activity.csv
```

### Source Metadata Organization
```
data/source_metadata/
├── bankofamerica/
│   └── metadata.json          # Column info, patterns, sample data
├── chase/
│   └── metadata.json
└── {source_id}/
    └── metadata.json
```

## Development Phases

### Phase 1: Core Infrastructure ✅
- [x] Set up project structure and development environment
- [x] Implement basic file system operations
- [x] Create data processing engine with source-specific parsing
- [x] Build basic API endpoints with FastAPI
- [x] Implement file upload and management
- [x] Add data processing capabilities with year/month organization
- [x] Create web interface with source-specific pages

### Phase 2: Frontend Development ✅
- [x] Create FastAPI application with Jinja2 templates
- [x] Implement file upload functionality with Bootstrap styling
- [x] Build processing status dashboard with real-time updates via WebSocket
- [x] Add data visualization components with Chart.js
- [x] Implement source-specific navigation and pages
- [x] Add file preview and download functionality
- [x] Create responsive design with mobile support
- [x] Implement drag-drop file upload zones

### Phase 3: Advanced Features ✅
- [x] Implement real-time processing updates via WebSocket
- [x] Add comprehensive file validation with multi-level checks
- [x] Create file backup and restoration system
- [x] Implement rate limiting and security measures (slowapi)
- [x] Add comprehensive logging and monitoring
- [x] Create health check endpoints with detailed metrics
- [x] Implement file preview functionality (first 50 rows and full file)
- [x] **Enhanced Source Mapping System** with JSON configuration (see `docs/mapping_technical_spec.md`)
- [x] **Persistent Metadata Management** with auto-loading (see `docs/mapping_design.md`)
- [x] **Multi-Level Validation System** with comprehensive testing (see `docs/VALIDATION_SYSTEM.md`)
- [x] **Robust CSV Decoder** with enterprise-grade parsing (see `docs/VALIDATION_SYSTEM.md`)
- [x] **Settings Restore Functionality** with full configuration backup
- [x] **Improved UI/UX** with balanced layouts and professional styling
- [x] **PDF Processing** for merchant statements (GG, AR sources)
- [x] **CLI Validation Tool** for batch processing and automation
- [x] **Flexible Header Matching** for variant file formats
- [x] **Automatic Encoding Detection** (UTF-8, UTF-8-BOM, etc.)

### Phase 4: Production Deployment 📋
- [ ] Set up production infrastructure (Docker, Kubernetes)
- [ ] Implement comprehensive monitoring and alerting
- [ ] Performance optimization and load testing
- [ ] Security hardening and penetration testing
- [ ] CI/CD pipeline setup
- [ ] Cloud storage integration (AWS S3, Google Cloud Storage)
- [ ] Automated backup and disaster recovery

## Deployment Architecture

### Development Environment
- **Application**: FastAPI with Jinja2 templates (localhost:8000)
- **Server**: Uvicorn ASGI server with auto-reload
- **File Storage**: Local file system in `data/` directory
- **Configuration**: Local environment variables via `scripts/backend.env`
- **Logging**: Console and file logging to `logs/` directory

### Staging Environment (Planned)
- **Application**: Containerized FastAPI (Docker)
- **Server**: Uvicorn with multiple workers
- **File Storage**: Persistent volumes or cloud storage
- **Configuration**: Environment-specific settings
- **Logging**: Centralized logging with log aggregation

### Production Environment (Planned)
- **Frontend**: FastAPI with Jinja2 templates (server-side rendered)
- **Backend**: Containerized FastAPI (Docker + Kubernetes)
- **Load Balancing**: Nginx or cloud load balancer
- **File Storage**: Cloud storage (AWS S3, Google Cloud Storage) with local caching
- **Database**: SQLite for admin data (or PostgreSQL for multi-user)
- **Configuration**: Kubernetes ConfigMaps and Secrets
- **Monitoring**: Prometheus + Grafana
- **Logging**: ELK Stack or cloud logging service
- **Backup**: Automated backups to cloud storage
- **CDN**: CloudFlare or AWS CloudFront for static assets

## Security & Performance

### Security Features
- File type validation (CSV only)
- File size limits and malicious file detection
- Data sanitization and XSS protection
- Path traversal prevention
- API rate limiting with slowapi
- Virus scanning for uploaded files
- Strict MIME type checking
- HTTPS enforcement (TLS 1.3)
- Input validation and sanitization
- CORS configuration with restricted origins
- **Privacy Protection**: Comprehensive `.gitignore` excludes all user data, logs, and sensitive files

### Performance Optimizations
- Parallel file processing
- Streaming for large files
- Caching for repeated operations
- Lazy loading and virtual scrolling
- Debounced search operations
- Response compression (gzip)
- Connection pooling
- Database query optimization

### Performance Targets
- **Small Files (<1MB)**: <5 seconds processing time
- **Medium Files (1-10MB)**: <30 seconds processing time
- **Large Files (10-50MB)**: <2 minutes processing time
- **Concurrent Processing**: Support for 5 simultaneous jobs
- **Page Load Time**: <2 seconds for dashboard
- **File Upload**: Progress indication for files >1MB
- **Real-time Updates**: <500ms WebSocket latency

## Testing Strategy

### Testing Coverage
- **Unit Testing**: pytest for services, utilities, and business logic
  - File service tests
  - CSV loader tests (20+ comprehensive tests)
  - Validation service tests
  - Processing service tests
- **Integration Testing**: httpx for API endpoint testing
  - Health check endpoints
  - File upload/download endpoints
  - Processing endpoints
  - Mapping configuration endpoints
- **Manual Testing**: Browser testing for UI/UX validation
- **CLI Testing**: Command-line validation tools for automation

### Running Tests
```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_csv_loader.py -v

# Run specific test
pytest tests/test_csv_loader.py::TestRobustCSVLoader::test_csv_with_metadata_validation -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run only fast tests (exclude slow integration tests)
pytest tests/ -m "not slow" -v
```

### Test Categories
1. **Basic Functionality Tests** (`test_basic.py`)
   - Health check endpoints
   - API info endpoints
   - Source listing
   - Basic CRUD operations

2. **CSV Loader Tests** (`test_csv_loader.py`)
   - Standard CSV parsing
   - Quoted fields handling
   - Trailing empty columns
   - Variable header locations
   - Mixed line endings
   - Malformed rows
   - Encoding detection
   - Metadata-driven validation
   - Chase-like complex structures
   - 20 comprehensive test cases

3. **Grouping and Processing Tests** (`test_grouping_removal.py`)
   - Transaction grouping logic
   - Month-based organization
   - Source file tracking

4. **Mapping Tests** (`test_mapping_file_selection.py`)
   - Column mapping validation
   - Sample data processing
   - Configuration persistence

### Testing Best Practices
- **Isolation**: Each test is independent and can run in any order
- **Mock Data**: Use temporary files and mock loggers for testing
- **Comprehensive Coverage**: Tests cover edge cases and error conditions
- **Real-World Scenarios**: Tests based on actual Chase and BoA file formats
- **Cleanup**: Automatic cleanup of temporary test files

## Error Handling & Recovery

### File Processing Errors
- **Validation Failures**: Clear error messages with specific field issues
- **Processing Failures**: Automatic retry with exponential backoff
- **File Corruption**: Graceful degradation with partial data recovery
- **System Errors**: Comprehensive logging with admin notifications

### User Experience
- **Upload Failures**: Real-time feedback with retry options
- **Processing Timeouts**: Progress indicators with estimated completion
- **Data Validation**: Inline validation with helpful suggestions

## Data Management

### Backup Strategy
- **File System**: Manual and automated backups of processed data
- **Configuration**: JSON configuration files with version control support
- **Recovery**: Point-in-time recovery capabilities via file system
- **Source Mappings**: JSON configuration files in `config/` directory with sample templates
- **Sample Data Metadata**: Persistent storage in `data/source_metadata/` with automatic backups

### Data Retention
- **Input Files**: User-managed retention in `data/{source}/input/`
- **Output Files**: Permanent retention in `data/{source}/output/{year}/` until manually deleted
- **Processing Logs**: Configurable retention in `logs/` directory (default: 90 days)
- **Sample Metadata**: Retained indefinitely in `data/source_metadata/` for mapping configuration
- **Configuration Backups**: Stored in `backups/` directory with timestamp

### Data Protection
- **File System Isolation**: All user data stored separately from application code
- **Access Logging**: Comprehensive logging of all file operations
- **Audit Trail**: Processing history and job tracking
- **Privacy**: All user data, logs, and configurations excluded from version control via `.gitignore`
- **Configuration Templates**: Sample configurations provided, actual configs excluded
- **Secure File Handling**: Path traversal prevention and file type validation

### File Organization
```
rest_finance/
├── data/                           # User data (excluded from git)
│   ├── source_metadata/           # Persistent metadata storage
│   │   ├── bankofamerica/
│   │   │   └── metadata.json
│   │   ├── chase/
│   │   │   └── metadata.json
│   │   └── {source_id}/
│   │       └── metadata.json
│   ├── bankofamerica/
│   │   ├── input/                 # Uploaded raw files
│   │   └── output/                # Processed files by year/month
│   ├── chase/
│   │   ├── input/
│   │   └── output/
│   └── {source}/
│       ├── input/
│       └── output/
├── config/                         # Source mappings (tracked in git)
│   ├── bankofamerica.json
│   ├── chase.json
│   ├── settings_sample.py         # Sample configuration
│   └── settings.py                # Actual config (excluded from git)
├── backups/                        # Configuration backups (excluded from git)
├── logs/                           # Application logs (excluded from git)
└── scripts/                        # Utility scripts
    ├── manage_backend.sh
    ├── manage_frontend.sh
    ├── extract_pdf_table.py
    └── backend.env                # Actual env (excluded from git)
```

## Monitoring & Alerting

### Application Metrics
- **Processing Success Rate**: Target >95%
- **Average Processing Time**: Target <30 seconds
- **File Upload Success Rate**: Target >98%
- **API Response Time**: Target <500ms

### System Metrics
- **Disk Usage**: Alert when >80%
- **Memory Usage**: Alert when >85%
- **CPU Usage**: Alert when >90%
- **Database Size**: Alert when >1GB

### Alert Channels
- **Email**: Critical system alerts
- **Slack**: Processing status updates
- **Dashboard**: Real-time metrics display

## Version Control & Releases

### Git Workflow
- **Main Branch**: Production-ready code
- **Development Branch**: Active development
- **Feature Branches**: Individual features
- **Release Tags**: Semantic versioning (v1.0.0, v1.1.0, etc.)

### Release Process
1. Feature development in feature branches
2. Merge to development branch
3. Testing and validation
4. Merge to main branch
5. Tag release
6. Deploy to production

### Privacy Protection
- **Comprehensive .gitignore**: Excludes all user data, logs, and sensitive files
- **Configuration Templates**: Sample configs provided, actual configs excluded
- **Data Isolation**: User data stored separately from source code
- **Secure Handling**: Protected file processing and storage

## Future Enhancements

### Planned Features
1. **Machine Learning**: Automated transaction categorization and anomaly detection
2. **Advanced Analytics**: Enhanced reporting with trend analysis and forecasting
3. **Multi-tenant Support**: Multiple organization/user support with role-based access
4. **API Integration**: Banking API connections for automatic imports
5. **Mobile Application**: Native mobile apps (iOS/Android) or enhanced PWA
6. **Cloud Synchronization**: Real-time cross-device sync with cloud storage
7. **Scheduled Processing**: Automated processing on schedule (daily, weekly, monthly)
8. **Email Notifications**: Processing completion alerts and error notifications
9. **Advanced Filtering**: Complex query builder for data analysis
10. **Data Export**: Multiple export formats (Excel, PDF, JSON)

### Technical Improvements
1. **Microservices Architecture**: Service decomposition for scalability
2. **Event Sourcing**: Event-driven architecture with Celery for background jobs
3. **CQRS Pattern**: Separate read/write operations for performance
4. **GraphQL API**: Flexible data querying alongside REST API
5. **Real-time Collaboration**: Multi-user capabilities with WebSocket
6. **Database Migration**: PostgreSQL for production with SQLAlchemy migrations
7. **Container Orchestration**: Kubernetes deployment with auto-scaling
8. **Caching Layer**: Redis for improved performance
9. **Search Engine**: Elasticsearch for advanced search capabilities
10. **Monitoring & Observability**: Prometheus + Grafana for metrics and alerting

### Performance Enhancements
1. **Parallel Processing**: Multi-threaded file processing for large datasets
2. **Streaming Processing**: Handle very large files without loading entirely into memory
3. **Incremental Processing**: Process only new/changed data
4. **CDN Integration**: Serve static assets from CDN in production
5. **Database Indexing**: Optimize queries for faster data retrieval

## Documentation Structure

This project documentation is organized into several documents:

1. **[overview.md](overview.md)** - This document: High-level project overview, architecture, and development phases
2. **[frontend.md](frontend.md)** - Detailed frontend specifications, UI components, and JavaScript architecture
3. **[backend.md](backend.md)** - Backend API design, data processing logic, and service architecture
4. **[mapping_technical_spec.md](mapping_technical_spec.md)** - Source mapping system technical specification
5. **[mapping_design.md](mapping_design.md)** - Source mapping configuration design and implementation
6. **[VALIDATION_SYSTEM.md](VALIDATION_SYSTEM.md)** - Multi-level validation system documentation
7. **[modal_guidelines.md](modal_guidelines.md)** - Modal dialog design guidelines and standards

## Quick Start

### Prerequisites
- Python 3.10+
- Git
- 10MB+ disk space for dependencies

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd rest_finance

# Install Python dependencies
pip install -r requirements.txt

# Optional: Set up configuration
cp scripts/backend.env.example scripts/backend.env
# Edit scripts/backend.env with your settings
```

### Running the Application

#### Option 1: Using the management script (recommended)
```bash
# Start backend in background
bash scripts/manage_backend.sh start -b

# Or start in foreground (for development)
bash scripts/manage_backend.sh start

# Check status
bash scripts/manage_backend.sh status

# View logs
bash scripts/manage_backend.sh logs

# Stop the service
bash scripts/manage_backend.sh stop
```

#### Option 2: Direct execution
```bash
# Run the application directly
python main.py

# Or use uvicorn directly
uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Access the Application
- **Main Application**: http://localhost:8000
- **API Documentation**: http://localhost:8000/api/docs (in debug mode)
- **Alternative API Docs**: http://localhost:8000/api/redoc (in debug mode)
- **Health Check**: http://localhost:8000/api/health

### First Steps
1. Navigate to http://localhost:8000
2. Select a data source from the sidebar (e.g., Bank of America, Chase)
3. Upload a sample CSV file to generate metadata
4. Configure column mappings (or use auto-detected settings)
5. Upload your data files
6. Process files and download monthly outputs

### CLI Tools
```bash
# Validate CSV files from command line
python3 tools/csv_validator.py data/chase/input/file.csv --source chase --verbose

# Extract PDF merchant statements
python3 scripts/extract_pdf_table.py --pdf data/gg/input/Jan2025.pdf --vendor gg --year 2025

# Run tests
pytest tests/ -v

# Run specific test file
pytest tests/test_csv_loader.py -v
```

## Contributing

Please refer to the individual documentation files for detailed implementation guidelines:
- **[frontend.md](frontend.md)** for UI/UX development
- **[backend.md](backend.md)** for API and data processing development
- **[mapping_technical_spec.md](mapping_technical_spec.md)** for source mapping system development
- **[modal_guidelines.md](modal_guidelines.md)** for modal dialog development

## Support

For technical questions or implementation details, please refer to the specific documentation files or create an issue in the project repository. 