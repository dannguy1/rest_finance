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
- **Bank of America**: CSV statement processing with transaction grouping
- **Chase**: Credit card statement processing
- **Restaurant Depot**: Invoice receipt processing
- **Sysco**: Invoice processing

### 2. Enhanced Source Mapping System
- **Persistent Configuration**: Source mappings stored as JSON files in `config/` directory
- **Metadata Management**: Processed sample data metadata stored in `data/source_metadata/`
- **Auto-Loading**: Existing metadata automatically loads when source ID is entered
- **Settings Restore**: Full configuration backup and restore including sample data
- **Validation**: Multi-level validation system (see `docs/VALIDATION_SYSTEM.md`)

### 3. Automated File Organization
- **Year/Month Collation**: Automatic organization by year and month
- **Source Separation**: Dedicated directories for each data source
- **Structured Output**: Consistent CSV format with grouped aggregations

### 4. Real-Time Processing
- **WebSocket Updates**: Live processing status and progress
- **Drag & Drop Upload**: Source-specific upload zones
- **Progress Tracking**: Real-time feedback during file processing

### 5. Data Visualization
- **Chart.js Integration**: Spending patterns and analytics
- **Responsive Tables**: Bootstrap-styled data tables with sorting
- **Interactive Dashboard**: Real-time data overview

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
Upload Sample File → Generate Metadata → Configure Mapping → Process Files → Year/Month Collation → Grouped Aggregation → CSV Output Generation
```

### Output Organization
Each data source follows the structure:
```
{Source}/output/{Year}/{MM_YYYY}.csv
```

Example:
```
BankOfAmerica/output/2024/01_2024.csv
├── Date, Description, Amount, Source File
├── 01/15/2024, VERIZON WIRELESS, -421.50, boa_statement_2024.csv
├── 01/20/2024, VERIZON WIRELESS, -301.93, boa_statement_2024.csv
└── 01/25/2024, GROCERY STORE, -45.67, boa_statement_2024.csv
```

## Development Phases

### Phase 1: Core Infrastructure ✅
- [x] Set up project structure and development environment
- [x] Implement basic file system operations
- [x] Create data processing engine
- [x] Build basic API endpoints
- [x] Implement file upload and management
- [x] Add data processing capabilities
- [x] Create web interface with source-specific pages

### Phase 2: Frontend Development ✅
- [x] Create FastAPI application with Jinja2 templates
- [x] Implement file upload functionality with Bootstrap styling
- [x] Build processing status dashboard with real-time updates
- [x] Add data visualization components with Chart.js
- [x] Implement source-specific navigation and pages
- [x] Add file preview and download functionality
- [x] Create responsive design with mobile support

### Phase 3: Advanced Features ✅
- [x] Implement real-time processing updates via WebSocket
- [x] Add file validation and error handling
- [x] Create file backup and restoration system
- [x] Implement rate limiting and security measures
- [x] Add comprehensive logging and monitoring
- [x] Create health check endpoints
- [x] Implement file preview functionality
- [x] **Enhanced Source Mapping System** (see `docs/mapping_technical_spec.md`)
- [x] **Persistent Metadata Management** (see `docs/mapping_design.md`)
- [x] **Multi-Level Validation System** (see `docs/VALIDATION_SYSTEM.md`)
- [x] **Settings Restore Functionality** with full configuration backup
- [x] **Improved UI/UX** with balanced layouts and professional styling

### Phase 4: Production Deployment 📋
- [ ] Set up production infrastructure
- [ ] Implement monitoring and logging
- [ ] Performance optimization
- [ ] Security hardening

## Deployment Architecture

### Development Environment
- **Frontend**: FastAPI with Jinja2 templates (localhost:8000)
- **Backend**: FastAPI with Uvicorn (localhost:8000)
- **File Storage**: Local file system
- **Database**: SQLite (development)

### Production Environment
- **Frontend**: FastAPI with Jinja2 templates (server-side rendered)
- **Backend**: Containerized FastAPI (Docker, Kubernetes)
- **File Storage**: Cloud storage (AWS S3, Google Cloud Storage)
- **Database**: SQLite (administrative data only, stored with application)

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
- **Unit Testing**: pytest for API endpoints and business logic
- **Integration Testing**: httpx for endpoint testing
- **Frontend Testing**: Manual testing with browser automation
- **Performance Testing**: Load testing with Artillery or k6
- **Security Testing**: Vulnerability scanning and penetration testing
- **Accessibility Testing**: WCAG compliance validation
- **Cross-browser Testing**: Multiple browser compatibility

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
- **File System**: Automated daily backups of processed data
- **Database**: SQLite database backup with versioning
- **Configuration**: Environment-specific configuration backups
- **Recovery**: Point-in-time recovery capabilities
- **Source Mappings**: JSON configuration files with version control
- **Sample Data Metadata**: Persistent storage in `data/source_metadata/`

### Data Retention
- **Input Files**: Configurable retention period (default: 1 year)
- **Output Files**: Permanent retention with versioning
- **Processing Logs**: 90-day retention for administrative logs
- **Sample Data**: Retained for mapping configuration and validation

### Data Protection
- **Encryption at Rest**: Encrypt sensitive files
- **Access Logging**: Log all file access
- **Audit Trail**: Track all operations
- **Data Retention**: Configurable retention policies
- **Privacy**: All user data excluded from version control

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
1. **Machine Learning**: Automated transaction categorization
2. **Advanced Analytics**: Enhanced reporting and insights
3. **Multi-tenant Support**: Multiple organization support
4. **API Integration**: Banking API connections for automatic imports
5. **Mobile Application**: React Native mobile app
6. **Cloud Synchronization**: Real-time cross-device sync

### Technical Improvements
1. **Microservices Architecture**: Service decomposition
2. **Event Sourcing**: Event-driven architecture with Celery
3. **CQRS Pattern**: Separate read/write operations
4. **GraphQL API**: Flexible data querying with Strawberry
5. **Real-time Collaboration**: Multi-user capabilities

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
- Node.js (for development tools)
- Git

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd rest_finance

# Install Python dependencies
pip install -r requirements.txt

# Run the development server
uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Access the Application
- **Main Application**: http://localhost:8000
- **API Documentation**: http://localhost:8000/api/docs
- **Alternative API Docs**: http://localhost:8000/api/redoc

## Contributing

Please refer to the individual documentation files for detailed implementation guidelines:
- **[frontend.md](frontend.md)** for UI/UX development
- **[backend.md](backend.md)** for API and data processing development
- **[mapping_technical_spec.md](mapping_technical_spec.md)** for source mapping system development
- **[modal_guidelines.md](modal_guidelines.md)** for modal dialog development

## Support

For technical questions or implementation details, please refer to the specific documentation files or create an issue in the project repository. 