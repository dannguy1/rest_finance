# Quick Start Guide - Financial Data Processor

## System Management Made Easy

This guide shows you how to quickly start, stop, and manage the Financial Data Processor using the unified management script.

## Prerequisites

- Python 3.10 or higher
- All dependencies installed (`pip install -r requirements.txt`)
- Configuration files set up in `scripts/` directory

## Starting the System

### Method 1: Quick Start (Recommended)

Start both backend and frontend in background mode:

```bash
./manage.sh start
```

Expected output:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Starting Financial Data Processor
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
► Starting Backend (FastAPI)...
[HH:MM:SS] Loading configuration from scripts/backend.env
[HH:MM:SS] Starting finance-backend on 0.0.0.0:8000...
✓ Service started in background (PID: 12345)
[HH:MM:SS] Logs: logs/finance-backend.log
[HH:MM:SS] API: http://0.0.0.0:8000

► Starting Frontend (Static Server)...
[HH:MM:SS] Loading configuration from scripts/frontend.env
[HH:MM:SS] Starting finance-frontend on port 3000...
✓ Frontend started in background (PID: 12346)
[HH:MM:SS] Logs: logs/finance-frontend.log
[HH:MM:SS] Frontend: http://localhost:3000

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ System started successfully!
[HH:MM:SS] Backend API:  http://localhost:8000
[HH:MM:SS] Frontend App: http://localhost:3000
[HH:MM:SS] API Docs:     http://localhost:8000/docs
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Method 2: Start in Foreground (for Development)

If you want to see logs directly in the terminal:

```bash
./manage.sh start -f
```

**Note**: Press `Ctrl+C` to stop both services when running in foreground mode.

## Accessing the Application

Once started, open your browser:

- **Frontend Application**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

Or use the quick-open command:

```bash
./manage.sh open
```

## Checking Status

Check if services are running:

```bash
./manage.sh status
```

Output:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Financial Data Processor Status
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
► Backend Status:
[HH:MM:SS] Service status: running (PID: 12345)
[HH:MM:SS] Process info:
  PID  PPID CMD                                         ELAPSED
12345     1 /usr/bin/python3 -m uvicorn app.api.main    00:05:23

► Frontend Status:
[HH:MM:SS] Service status: running (PID: 12346)
[HH:MM:SS] Process info:
  PID  PPID CMD                                         ELAPSED
12346     1 python3 -m http.server 3000                 00:05:23
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Viewing Logs

### Combined Logs (Both Services)

```bash
./manage.sh logs
```

### Individual Service Logs

Backend only:
```bash
./manage.sh logs-backend
```

Frontend only:
```bash
./manage.sh logs-frontend
```

**Tip**: Press `Ctrl+C` to exit log viewing.

## Stopping the System

Stop both services:

```bash
./manage.sh stop
```

Output:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Stopping Financial Data Processor
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
► Stopping Frontend...
[HH:MM:SS] Stopping finance-frontend...
[HH:MM:SS] Sending SIGTERM to process 12346...
✓ Service stopped

► Stopping Backend...
[HH:MM:SS] Stopping finance-backend...
[HH:MM:SS] Sending SIGTERM to process 12345...
✓ Service stopped

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ System stopped successfully!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Restarting the System

Restart both services (useful after code changes):

```bash
./manage.sh restart
```

## Individual Service Control

### Backend Only

```bash
# Start backend
./manage.sh start-backend

# Stop backend
./manage.sh stop-backend

# Restart backend
./manage.sh restart-backend
```

### Frontend Only

```bash
# Start frontend
./manage.sh start-frontend

# Stop frontend
./manage.sh stop-frontend

# Restart frontend
./manage.sh restart-frontend
```

## Common Workflows

### Development Workflow

1. **Start the system**:
   ```bash
   ./manage.sh start
   ```

2. **Make code changes** in your editor

3. **Restart to apply changes**:
   ```bash
   ./manage.sh restart
   ```

4. **Check logs for errors**:
   ```bash
   ./manage.sh logs
   ```

5. **Stop when done**:
   ```bash
   ./manage.sh stop
   ```

### Quick Testing Workflow

1. **Start in foreground** to see logs directly:
   ```bash
   ./manage.sh start -f
   ```

2. **Test your changes** in the browser

3. **Press Ctrl+C** to stop when done

### Backend-Only Development

If you're only working on backend code:

```bash
# Start backend in foreground
./manage.sh start-backend -f

# In another terminal, start frontend in background
./manage.sh start-frontend -b
```

### Production-Like Testing

Run both services in background:

```bash
# Start
./manage.sh start

# Monitor
./manage.sh status

# Check logs if needed
./manage.sh logs

# Stop
./manage.sh stop
```

## Troubleshooting

### Services Won't Start

1. **Check if ports are already in use**:
   ```bash
   # Check port 8000 (backend)
   lsof -i :8000
   
   # Check port 3000 (frontend)
   lsof -i :3000
   ```

2. **Check configuration files**:
   ```bash
   # Verify backend config
   cat scripts/backend.env
   
   # Verify frontend config
   cat scripts/frontend.env
   ```

3. **Check logs for errors**:
   ```bash
   # Backend log
   tail -50 logs/finance-backend.log
   
   # Frontend log
   tail -50 logs/finance-frontend.log
   ```

### Services Won't Stop

1. **Force stop if needed**:
   ```bash
   # Find processes
   ps aux | grep uvicorn
   ps aux | grep http.server
   
   # Kill manually
   kill -9 <PID>
   
   # Remove stale PID files
   rm logs/finance-backend.pid
   rm logs/finance-frontend.pid
   ```

### "Configuration file not found" Error

Create the missing configuration files:

```bash
# Backend configuration
cp scripts/backend.env.example scripts/backend.env

# Frontend configuration
cp scripts/frontend.env.example scripts/frontend.env
```

### Port Already in Use

Change ports in configuration files:

**Backend** (`scripts/backend.env`):
```bash
UVICORN_PORT=8001  # Change from 8000 to 8001
```

**Frontend** (`scripts/frontend.env`):
```bash
HTTP_SERVER_PORT=3001  # Change from 3000 to 3001
```

## Getting Help

### View All Commands

```bash
./manage.sh help
```

### Script Documentation

- Main script: `manage.sh` in root directory
- Backend script: `scripts/manage_backend.sh`
- Frontend script: `scripts/manage_frontend.sh`
- Documentation: `scripts/README.md`

## Tips & Best Practices

1. **Always use background mode** (`-b`) for long-running sessions
2. **Use foreground mode** (`-f`) for quick testing and debugging
3. **Check status regularly** with `./manage.sh status`
4. **Monitor logs** when testing new features
5. **Restart after code changes** to apply updates
6. **Stop services** when not in use to free resources

## Summary of Commands

| Command | Description |
|---------|-------------|
| `./manage.sh start` | Start both services in background |
| `./manage.sh start -f` | Start both services in foreground |
| `./manage.sh stop` | Stop all services |
| `./manage.sh restart` | Restart all services |
| `./manage.sh status` | Check service status |
| `./manage.sh logs` | View combined logs |
| `./manage.sh open` | Open app in browser |
| `./manage.sh help` | Show all commands |

## Next Steps

- Read the [full documentation](scripts/README.md) for advanced usage
- Check out the [API documentation](http://localhost:8000/docs) after starting
- Explore the [frontend interface](http://localhost:3000)

---

**Need more help?** Run `./manage.sh help` for detailed command information.
