# Financial Data Processor - Management Scripts

This directory contains management scripts for starting, stopping, and monitoring the Financial Data Processor backend and frontend services.

## Scripts Overview

### Backend Management
- **`manage_backend.sh`** - Manages the FastAPI backend service
- **`backend.env`** - Backend configuration file

### Frontend Management  
- **`manage_frontend.sh`** - Manages the static frontend server
- **`frontend.env`** - Frontend configuration file

## Quick Start

1. **Start Backend:**
   ```bash
   ./scripts/manage_backend.sh start -b
   ```

2. **Start Frontend:**
   ```bash
   ./scripts/manage_frontend.sh start -b
   ```

3. **Check Status:**
   ```bash
   ./scripts/manage_backend.sh status
   ./scripts/manage_frontend.sh status
   ```

4. **View Logs:**
   ```bash
   ./scripts/manage_backend.sh logs
   ./scripts/manage_frontend.sh logs
   ```

5. **Stop Services:**
   ```bash
   ./scripts/manage_backend.sh stop
   ./scripts/manage_frontend.sh stop
   ```

## Configuration

Both scripts use environment configuration files to avoid hardcoded values:

### Backend Configuration (`backend.env`)
```bash
# Service Configuration
SERVICE_NAME=finance-backend
APP_MODULE=app.api.main:app

# Server Configuration  
HOST=0.0.0.0
PORT=8000
RELOAD=true
LOG_LEVEL=info

# Python Configuration
PYTHON_PATH=python3
# PYTHON_PATH=venv/bin/python  # Uncomment to use virtual environment

# File Paths
PID_FILE=logs/finance-backend.pid
LOG_FILE=logs/finance-backend.log
```

### Frontend Configuration (`frontend.env`)
```bash
# Service Configuration
SERVICE_NAME=finance-frontend
FRONTEND_DIR=app/static

# Server Configuration
HOST=0.0.0.0
PORT=3000

# File Paths
PID_FILE=logs/finance-frontend.pid
LOG_FILE=logs/finance-frontend.log
```

## Commands

Both scripts support the same commands:

- `start` - Start the service
- `stop` - Stop the service  
- `restart` - Restart the service
- `status` - Show service status
- `logs` - Show service logs
- `help` - Show help message

### Options

- `-b, --background` - Start in background mode
- `-f, --foreground` - Start in foreground mode (default)

## Examples

```bash
# Start backend in background
./scripts/manage_backend.sh start -b

# Start frontend in foreground
./scripts/manage_frontend.sh start

# Restart both services in background
./scripts/manage_backend.sh restart -b
./scripts/manage_frontend.sh restart -b

# Check status of both services
./scripts/manage_backend.sh status
./scripts/manage_frontend.sh status

# View logs
./scripts/manage_backend.sh logs
./scripts/manage_frontend.sh logs

# Stop both services
./scripts/manage_backend.sh stop
./scripts/manage_frontend.sh stop
```

## Log Files

Log files are stored in the `logs/` directory:
- `logs/finance-backend.log` - Backend service logs
- `logs/finance-frontend.log` - Frontend service logs

## PID Files

PID files track running processes:
- `logs/finance-backend.pid` - Backend process ID
- `logs/finance-frontend.pid` - Frontend process ID

## Troubleshooting

### Service Won't Start
1. Check if required packages are installed
2. Verify configuration files exist and are readable
3. Check log files for error messages
4. Ensure ports are not already in use

### Service Won't Stop
1. Check if PID file exists and contains valid process ID
2. Manually kill process if needed: `kill -9 <PID>`
3. Remove stale PID file: `rm logs/finance-*.pid`

### Configuration Issues
1. Ensure environment files are properly formatted (no spaces around `=`)
2. Check that all required variables are set
3. Verify file paths are correct for your system

## Development Workflow

1. **Start Development Environment:**
   ```bash
   # Start backend
   ./scripts/manage_backend.sh start -b
   
   # Start frontend  
   ./scripts/manage_frontend.sh start -b
   ```

2. **Monitor During Development:**
   ```bash
   # Watch backend logs
   ./scripts/manage_backend.sh logs
   
   # Watch frontend logs
   ./scripts/manage_frontend.sh logs
   ```

3. **Restart After Changes:**
   ```bash
   # Restart backend after code changes
   ./scripts/manage_backend.sh restart -b
   
   # Restart frontend after static file changes
   ./scripts/manage_frontend.sh restart -b
   ```

4. **Stop Development Environment:**
   ```bash
   ./scripts/manage_backend.sh stop
   ./scripts/manage_frontend.sh stop
   ``` 