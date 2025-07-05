#!/bin/bash

# Financial Data Processor Frontend Management Script
# Serves static frontend assets for development

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$SCRIPT_DIR/frontend.env"

# Load environment configuration
load_config() {
    if [ -f "$ENV_FILE" ]; then
        print_status "Loading configuration from $ENV_FILE"
        export $(grep -v '^#' "$ENV_FILE" | xargs)
    else
        print_error "Configuration file not found: $ENV_FILE"
        print_error "Please create $ENV_FILE from frontend.env.example"
        exit 1
    fi
}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() { echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"; }
print_success() { echo -e "${GREEN}✓${NC} $1"; }
print_warning() { echo -e "${YELLOW}⚠${NC} $1"; }
print_error() { echo -e "${RED}✗${NC} $1"; }

# Load configuration at script start
load_config

# Set default values if not in env file
SERVICE_NAME=${SERVICE_NAME:-finance-frontend}
FRONTEND_DIR=${FRONTEND_DIR:-$PROJECT_ROOT/app/static}
PID_FILE=${PID_FILE:-$PROJECT_ROOT/logs/$SERVICE_NAME.pid}
LOG_FILE=${LOG_FILE:-$PROJECT_ROOT/logs/$SERVICE_NAME.log}
PORT=${PORT:-3000}
HTTP_SERVER_PORT=${HTTP_SERVER_PORT:-3000}
HTTP_SERVER_DIRECTORY=${HTTP_SERVER_DIRECTORY:-app/static}

is_running() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        else
            rm -f "$PID_FILE"
        fi
    fi
    return 1
}

get_status() {
    if is_running; then
        local pid=$(cat "$PID_FILE")
        echo "running (PID: $pid)"
    else
        echo "stopped"
    fi
}

stop_service() {
    print_status "Stopping $SERVICE_NAME..."
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            print_status "Sending SIGTERM to process $pid..."
            kill -TERM "$pid"
            local count=0
            while ps -p "$pid" > /dev/null 2>&1 && [ $count -lt 10 ]; do
                sleep 1
                count=$((count + 1))
            done
            if ps -p "$pid" > /dev/null 2>&1; then
                print_warning "Process still running, sending SIGKILL..."
                kill -KILL "$pid"
                sleep 1
            fi
            rm -f "$PID_FILE"
            print_success "Service stopped"
        else
            print_warning "PID file exists but process is not running"
            rm -f "$PID_FILE"
        fi
    else
        print_warning "No PID file found, service may not be running"
    fi
}

start_service() {
    local background=${1:-false}
    print_status "Starting $SERVICE_NAME on port $HTTP_SERVER_PORT..."
    if is_running; then
        print_warning "Service is already running (PID: $(cat "$PID_FILE"))"
        return 1
    fi
    mkdir -p "$(dirname "$LOG_FILE")"
    mkdir -p "$(dirname "$PID_FILE")"
    if [ "$background" = true ]; then
        print_status "Starting service in background..."
        nohup python3 -m http.server $HTTP_SERVER_PORT --directory "$HTTP_SERVER_DIRECTORY" > "$LOG_FILE" 2>&1 &
        local pid=$!
        echo "$pid" > "$PID_FILE"
        sleep 2
        if ps -p "$pid" > /dev/null 2>&1; then
            print_success "Frontend started in background (PID: $pid)"
            print_status "Logs: $LOG_FILE"
            print_status "Frontend: http://localhost:$HTTP_SERVER_PORT"
        else
            print_error "Failed to start frontend"
            rm -f "$PID_FILE"
            return 1
        fi
    else
        print_status "Starting service in foreground..."
        print_status "Press Ctrl+C to stop"
        python3 -m http.server $HTTP_SERVER_PORT --directory "$HTTP_SERVER_DIRECTORY"
    fi
}

restart_service() {
    print_status "Restarting $SERVICE_NAME..."
    stop_service
    sleep 2
    start_service "$1"
}

show_logs() {
    if [ -f "$LOG_FILE" ]; then
        if command -v tail > /dev/null 2>&1; then
            print_status "Showing last 50 lines of logs (Press Ctrl+C to exit):"
            tail -f -n 50 "$LOG_FILE"
        else
            print_status "Log file: $LOG_FILE"
            cat "$LOG_FILE"
        fi
    else
        print_warning "No log file found"
    fi
}

show_help() {
    echo "Financial Data Processor Frontend Management Script"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  start     Start the frontend service"
    echo "  stop      Stop the frontend service"
    echo "  restart   Restart the frontend service"
    echo "  status    Show service status"
    echo "  logs      Show service logs"
    echo "  help      Show this help message"
    echo ""
    echo "Options:"
    echo "  -b, --background  Start in background mode"
    echo "  -f, --foreground  Start in foreground mode (default)"
    echo ""
    echo "Configuration:"
    echo "  Uses: $ENV_FILE"
    echo ""
    echo "Examples:"
    echo "  $0 start              # Start in foreground"
    echo "  $0 start -b           # Start in background"
    echo "  $0 stop               # Stop the service"
    echo "  $0 restart -b         # Restart in background"
    echo "  $0 status             # Show status"
    echo "  $0 logs               # Show logs"
}

case "${1:-help}" in
    start)
        background=false
        if [ "$2" = "-b" ] || [ "$2" = "--background" ]; then
            background=true
        fi
        start_service "$background"
        ;;
    stop)
        stop_service
        ;;
    restart)
        background=false
        if [ "$2" = "-b" ] || [ "$2" = "--background" ]; then
            background=true
        fi
        restart_service "$background"
        ;;
    status)
        print_status "Service status: $(get_status)"
        if is_running; then
            local pid=$(cat "$PID_FILE")
            print_status "Process info:"
            ps -p "$pid" -o pid,ppid,cmd,etime
        fi
        ;;
    logs)
        show_logs
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac 