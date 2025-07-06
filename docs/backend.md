# Backend Specification - Garlic and Chives

## Overview

The backend of Garlic and Chives is built using FastAPI, providing a robust API for file upload, management, processing, preview, and real-time updates. The system handles multiple data sources (Bank of America, Chase, Restaurant Depot, Sysco) with source-specific processing rules and organizes output by source, year, and month. All user data is stored in the file system; SQLite is used for administrative metadata only.

## Technology Stack

### Core Technologies
- **Framework**: FastAPI for API and server-side rendering
- **Language**: Python 3.10+
- **File Processing**: Python csv module, pandas for data manipulation
- **Validation**: Pydantic for data validation and serialization
- **Logging**: Python logging module with structured logging
- **Testing**: pytest, httpx for API testing
- **Server**: Uvicorn ASGI server
- **Real-time**: WebSocket support for live updates
- **Rate Limiting**: slowapi for API rate limiting

### Database (Administrative Only)
- **Database**: SQLite for administrative metadata storage
- **Purpose**: Administrative data only (processing history, job tracking, system logs)
- **User Data**: All user data (financial transactions, processed files) stored in file system only

## Configuration Management

- All configuration is managed via `app/config/settings.py` using Pydantic settings.
- Environment variables and `.env` file supported.
- Key settings: data directory, backup directory, allowed file types, rate limits, CORS, logging.
- Source mapping configurations stored as JSON files in `config/` directory (see `config/README.md`).

## Project Structure
```
rest_finance/
├── app/
│   ├── api/
│   │   ├── main.py            # FastAPI application entry point
│   │   ├── sample_data.py     # Sample data and metadata API
│   │   └── routes/
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
│   ├── static/            # Static assets (CSS, JS)
│   ├── middleware/        # Middleware components
│   ├── utils/             # Utility functions
│   └── config/            # Configuration management
├── config/                # Source mapping configurations
├── data/                  # Data storage (excluded from git)
├── docs/                  # Documentation
├── tests/                 # Test files
├── logs/                  # Application logs (excluded from git)
├── backups/               # File backups (excluded from git)
├── requirements.txt       # Python dependencies
├── pyproject.toml         # Project configuration
└── README.md              # Project documentation
```

## Data Models

- Pydantic models for sources, file upload, processing options, results, and status.
- Enum for source types: BankOfAmerica, Chase, RestaurantDepot, Sysco.
- Processing options: group by description, include source file, etc.
- Source mapping models (see `docs/mapping_technical_spec.md` for detailed specifications).

## API Design

### RESTful Endpoints (actual implementation)

#### File Management
- `POST   /api/files/upload/{source}` — Upload files for a specific source
- `GET    /api/files/list/{source}` — List uploaded files for a source
- `DELETE /api/files/{source}/{filename}` — Delete a file from a source
- `GET    /api/files/validate/{source}/{filename}` — Validate a file for processing
- `GET    /api/files/info/{source}/{filename}` — Get file info
- `POST   /api/files/backup/{source}/{filename}` — Backup a file
- `GET    /api/files/output/{source}` — List output files for a source
- `GET    /api/files/download/{source}/{year}/{month}` — Download an output file
- `GET    /api/files/preview/{source}` — Preview a processed file (first 50 rows)
- `GET    /api/files/preview-uploaded/{source}` — Preview an uploaded file (first 50 rows)
- `GET    /api/files/preview-uploaded-full/{source}` — Preview full uploaded file
- `GET    /api/files/preview-full/{source}` — Preview full processed file
- `DELETE /api/files/processed/{source}/{year}/{month}` — Delete a processed output file

#### Data Processing
- `POST   /api/files/process/{source}/{filename}` — Process a single uploaded file
- `POST   /api/processing/process/{source}/{year}` — Process all files for a source and year
- `GET    /api/processing/status/{source}/{year}` — Get processing status for a source and year
- `GET    /api/processing/summary/{source}/{year}` — Get processing summary for a source and year
- `GET    /api/processing/download/{source}/{year}/{month}` — Download a processed file
- `GET    /api/processing/sources` — List available sources
- `GET    /api/processing/years/{source}` — List available years for a source
- `GET    /api/processing/months/{source}/{year}` — List available months for a source and year

#### Source Mapping Management
- `GET    /api/mappings` — List all source mappings
- `GET    /api/mappings/{source_id}` — Get specific source mapping
- `POST   /api/mappings` — Create new source mapping
- `PUT    /api/mappings/{source_id}` — Update source mapping
- `DELETE /api/mappings/{source_id}` — Delete source mapping
- `POST   /api/mappings/{source_id}/validate` — Validate source mapping
- `GET    /api/mappings/{source_id}/template` — Get template for new source

#### Sample Data and Metadata
- `POST   /api/sample-data/upload/{source_id}` — Upload sample file for metadata generation
- `POST   /api/sample-data/process/{source_id}` — Process sample file to generate metadata
- `GET    /api/sample-data/sources/{source_id}/metadata` — Get metadata for a source
- `GET    /api/sample-data/sources/{source_id}/list` — List available metadata files
- `DELETE /api/sample-data/sources/{source_id}/metadata` — Delete metadata for a source
- `POST   /api/sample-data/sources/{source_id}/validate` — Validate uploaded file against metadata

#### Web Pages
- `/` — Dashboard
- `/source/{source}` — Source-specific page (upload, process, preview)
- `/mapping` — Source mapping configuration page
- `/analytics` — Analytics page
- `/settings` — Settings page
- `/download` — Download page

#### Health Checks
- `GET /api/health` — Basic health check
- `GET /api/health/detailed` — Detailed health check with system metrics

#### WebSocket
- `/ws` — Real-time updates for processing status

## Data Processing Engine

- Source-specific parsing and validation (Bank of America, Chase, Restaurant Depot, Sysco)
- Grouping by month and description
- Output CSV generation by year/month
- Per-file and batch processing supported
- File validation and error handling
- Logging of all processing events

## File Service

- File upload, listing, deletion, backup, and info
- Output file management (list, download, delete)
- File preview (first 50 rows or full file)
- All user data stored in the file system under `data/{Source}/input/` and `data/{Source}/output/`

## Sample Data Service

- **Metadata Generation**: Processes sample files to extract column information and data patterns
- **Persistent Storage**: Stores metadata in `data/source_metadata/{source_id}/` as JSON files
- **Auto-Loading**: Automatically loads existing metadata when source ID is accessed
- **Validation**: Validates uploaded files against saved metadata
- **Restore Functionality**: Supports full configuration backup and restore including sample data

## Validation Service

- File extension and size validation
- Source-specific CSV structure validation
- General CSV checks (empty, duplicates, missing values)
- Filename sanitization
- **Multi-Level Validation**: Comprehensive validation system (see `docs/VALIDATION_SYSTEM.md`)
- **Mapping Validation**: Validates source mapping configurations against sample data

## Mapping Validation Service

- **Structural Validation**: Validates mapping configuration structure and required fields
- **Format Validation**: Tests date and amount format parsing with sample data
- **Data Conversion Testing**: Tests actual data processing with real sample data
- **File Validation**: Tests against actual uploaded files
- **Comprehensive Reporting**: Detailed validation results with success rates and error details

## Middleware

- Logging middleware for all requests
- Error handling middleware for consistent error responses
- Rate limiting middleware (slowapi)

## Security & Performance

- File type and size validation
- Path traversal prevention
- CORS configuration
- API rate limiting (slowapi)
- Structured logging
- HTTPS enforcement (production)
- Input sanitization
- **Privacy Protection**: Comprehensive data exclusion from version control

## Testing Strategy

- **Unit Testing**: pytest for services and endpoints
- **Integration Testing**: httpx for API
- **Manual Testing**: Browser and API client
- **Performance Testing**: Load testing tools (optional)

## Deployment

- Uvicorn for development and production
- Docker-ready (see Dockerfile)
- Static asset serving
- Logs and backups directories

## Configuration Management

### Source Mapping Configurations
- Stored as JSON files in `config/` directory
- Each source has its own configuration file (`{source_id}.json`)
- Automatic loading and saving of configurations
- Version controlled with sample configurations provided
- Actual configurations excluded from version control for privacy

### Sample Data Metadata
- Processed sample data metadata stored in `data/source_metadata/{source_id}/`
- Contains column information, data patterns, and detected mappings
- Used for auto-loading existing configurations
- Supports restore functionality for full configuration backup

## Future Enhancements

- Machine learning for transaction categorization
- Advanced analytics and reporting
- Multi-tenant support
- Banking API integration
- Real-time collaboration
- Cloud storage support

---

For detailed frontend and overall architecture, see `frontend.md` and `overview.md`. For source mapping system details, see `mapping_technical_spec.md` and `mapping_design.md`. 