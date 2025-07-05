# Garlic and Chives

A comprehensive financial data processing system for multiple sources.

## Features

- **Multi-Source Support**: Process data from Bank of America, Chase, Restaurant Depot, and Sysco
- **Automated Organization**: Output files organized by source, year, and month
- **Modern Web Interface**: Responsive design with dark/light theme support
- **Real-time Processing**: WebSocket support for live processing updates
- **File Validation**: Comprehensive validation for uploaded files
- **Progress Tracking**: Real-time progress monitoring for processing jobs
- **Download Management**: Easy access to processed files
- **PWA Support**: Progressive Web App capabilities for mobile use

## Technology Stack

### Backend
- **FastAPI**: Modern, fast web framework for building APIs
- **SQLite**: Lightweight database for administrative data
- **Pandas**: Data processing and manipulation
- **Pydantic**: Data validation and settings management
- **Uvicorn**: ASGI server for production deployment

### Frontend
- **HTML5/CSS3**: Modern web standards with CSS Grid and Flexbox
- **Vanilla JavaScript**: No framework dependencies
- **Chart.js**: Data visualization
- **Font Awesome**: Icon library
- **PWA**: Progressive Web App features

## Installation

### Prerequisites
- Python 3.10 or higher
- pip (Python package installer)

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd financial-processor
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create environment file**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize data directories**
   ```bash
   mkdir -p data/{BankOfAmerica,Chase,RestaurantDepot,Sysco}/{input,output}
   mkdir -p logs backups
   ```

## Usage

### Starting the Application

1. **Development mode**
   ```bash
   python main.py
   ```

2. **Production mode**
   ```bash
   uvicorn app.api.main:app --host 0.0.0.0 --port 8000
   ```

3. **Access the application**
   - Web Interface: http://localhost:8000
   - API Documentation: http://localhost:8000/api/docs
   - Health Check: http://localhost:8000/api/health

### File Upload and Processing

1. **Upload Files**
   - Navigate to the Upload page
   - Select your data source (Bank of America, Chase, etc.)
   - Choose CSV files to upload
   - Files are automatically validated and stored

2. **Process Data**
   - Go to the Process page
   - Select source and year for processing
   - Click "Process Data" to start
   - Monitor progress in real-time

3. **Download Results**
   - Visit the Download page
   - Browse available processed files
   - Download monthly CSV files organized by source and year

## API Endpoints

### Health & Monitoring
- `GET /api/health` - Basic health check
- `GET /api/health/detailed` - Detailed system metrics
- `GET /api/health/ready` - Readiness check
- `GET /api/health/live` - Liveness check
- `GET /api/health/metrics` - Application metrics

### File Management
- `POST /api/files/upload/{source}` - Upload files
- `GET /api/files/list/{source}` - List files for a source
- `DELETE /api/files/{source}/{filename}` - Delete a file
- `GET /api/files/validate/{source}/{filename}` - Validate a file
- `GET /api/files/info/{source}/{filename}` - Get file information
- `POST /api/files/backup/{source}/{filename}` - Create file backup

### Data Processing
- `POST /api/processing/process/{source}/{year}` - Process data
- `GET /api/processing/status/{source}/{year}` - Get processing status
- `GET /api/processing/summary/{source}/{year}` - Get processing summary
- `GET /api/processing/download/{source}/{year}/{month}` - Download processed file
- `GET /api/processing/sources` - Get available sources
- `GET /api/processing/years/{source}` - Get available years
- `GET /api/processing/months/{source}/{year}` - Get available months

### WebSocket
- `WS /api/processing/ws/{source}/{year}` - Real-time processing updates

## Configuration

The application uses environment variables for configuration. Create a `.env` file with the following settings:

```env
# Application settings
DEBUG=false
HOST=0.0.0.0
PORT=8000

# Database
DATABASE_URL=sqlite:///app.db

# File processing
MAX_FILE_SIZE_MB=50
PROCESSING_TIMEOUT_SECONDS=300

# Security
SECRET_KEY=your-secret-key-here-change-in-production
CORS_ORIGINS=["*"]

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/processing.log

# Rate limiting
RATE_LIMIT_UPLOAD=10/minute
RATE_LIMIT_PROCESS=5/minute
RATE_LIMIT_DOWNLOAD=30/minute
RATE_LIMIT_API=100/minute
```

## Project Structure

```
financial-processor/
├── app/
│   ├── api/
│   │   ├── main.py              # FastAPI application
│   │   └── routes/              # API route modules
│   ├── middleware/              # Custom middleware
│   ├── models/                  # Pydantic models
│   ├── services/                # Business logic services
│   ├── static/                  # Static assets (CSS, JS, images)
│   ├── templates/               # HTML templates
│   └── utils/                   # Utility functions
├── data/                        # Data storage
│   ├── BankOfAmerica/
│   ├── Chase/
│   ├── RestaurantDepot/
│   └── Sysco/
├── docs/                        # Documentation
├── logs/                        # Application logs
├── tests/                       # Test files
├── main.py                      # Application entry point
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## Development

### Running Tests
```bash
pytest tests/
```

### Code Formatting
```bash
black app/
flake8 app/
mypy app/
```

### Adding New Data Sources

1. **Update SourceType enum** in `app/models/file_models.py`
2. **Add parsing logic** in `app/services/processing_service.py`
3. **Update validation** in `app/services/validation_service.py`
4. **Add frontend support** in templates and JavaScript

## Deployment

### Docker Deployment
```bash
# Build image
docker build -t financial-processor .

# Run container
docker run -p 8000:8000 financial-processor
```

### Production Considerations
- Use a production ASGI server (Gunicorn + Uvicorn)
- Set up reverse proxy (Nginx)
- Configure SSL/TLS certificates
- Set up monitoring and logging
- Use environment-specific configuration
- Implement proper backup strategies

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Check the documentation in the `/docs` folder
- Review the API documentation at `/api/docs`
- Open an issue on the project repository

## Changelog

### Version 1.0.0
- Initial release
- Multi-source data processing
- Modern web interface
- Real-time processing updates
- File validation and management
- PWA support 