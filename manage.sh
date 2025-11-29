#!/bin/bash

# Financial Data Processor Unified Management Script
# Controls both backend (FastAPI) and frontend (static server)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
BACKEND_SCRIPT="$PROJECT_ROOT/scripts/manage_backend.sh"
FRONTEND_SCRIPT="$PROJECT_ROOT/scripts/manage_frontend.sh"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

print_header() { echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"; }
print_status() { echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"; }
print_success() { echo -e "${GREEN}✓${NC} $1"; }
print_warning() { echo -e "${YELLOW}⚠${NC} $1"; }
print_error() { echo -e "${RED}✗${NC} $1"; }
print_service() { echo -e "${MAGENTA}►${NC} $1"; }

# Check if required scripts exist
check_dependencies() {
    local missing=0
    if [ ! -f "$BACKEND_SCRIPT" ]; then
        print_error "Backend script not found: $BACKEND_SCRIPT"
        missing=1
    fi
    if [ ! -f "$FRONTEND_SCRIPT" ]; then
        print_error "Frontend script not found: $FRONTEND_SCRIPT"
        missing=1
    fi
    if [ $missing -eq 1 ]; then
        exit 1
    fi
    chmod +x "$BACKEND_SCRIPT" "$FRONTEND_SCRIPT" 2>/dev/null || true
}

start_all() {
    local background=${1:-true}
    print_header
    echo -e "${CYAN}Starting Financial Data Processor${NC}"
    print_header
    
    print_service "Starting Backend (FastAPI)..."
    if [ "$background" = true ]; then
        bash "$BACKEND_SCRIPT" start -b
    else
        bash "$BACKEND_SCRIPT" start -f &
        BACKEND_PID=$!
    fi
    
    echo ""
    print_service "Starting Frontend (Static Server)..."
    if [ "$background" = true ]; then
        bash "$FRONTEND_SCRIPT" start -b
    else
        bash "$FRONTEND_SCRIPT" start -f &
        FRONTEND_PID=$!
    fi
    
    if [ "$background" = true ]; then
        echo ""
        print_header
        print_success "System started successfully!"
        print_status "Backend API:  http://localhost:8000"
        print_status "Frontend App: http://localhost:3000"
        print_status "API Docs:     http://localhost:8000/docs"
        print_header
        echo ""
        echo -e "Use ${CYAN}./manage.sh status${NC} to check status"
        echo -e "Use ${CYAN}./manage.sh logs${NC} to view logs"
        echo -e "Use ${CYAN}./manage.sh stop${NC} to stop all services"
    else
        echo ""
        print_header
        print_success "System started in foreground mode"
        print_status "Press Ctrl+C to stop all services"
        print_header
        # Wait for both processes
        wait
    fi
}

stop_all() {
    print_header
    echo -e "${CYAN}Stopping Financial Data Processor${NC}"
    print_header
    
    print_service "Stopping Frontend..."
    bash "$FRONTEND_SCRIPT" stop || true
    
    echo ""
    print_service "Stopping Backend..."
    bash "$BACKEND_SCRIPT" stop || true
    
    echo ""
    print_header
    print_success "System stopped successfully!"
    print_header
}

restart_all() {
    local background=${1:-true}
    print_header
    echo -e "${CYAN}Restarting Financial Data Processor${NC}"
    print_header
    
    stop_all
    sleep 2
    start_all "$background"
}

status_all() {
    print_header
    echo -e "${CYAN}Financial Data Processor Status${NC}"
    print_header
    
    print_service "Backend Status:"
    bash "$BACKEND_SCRIPT" status 2>/dev/null || print_warning "Backend script error"
    
    echo ""
    print_service "Frontend Status:"
    bash "$FRONTEND_SCRIPT" status 2>/dev/null || print_warning "Frontend script error"
    
    print_header
}

show_logs() {
    local service=${1:-all}
    
    print_header
    echo -e "${CYAN}Financial Data Processor Logs${NC}"
    print_header
    
    case "$service" in
        backend)
            print_service "Backend Logs:"
            bash "$BACKEND_SCRIPT" logs
            ;;
        frontend)
            print_service "Frontend Logs:"
            bash "$FRONTEND_SCRIPT" logs
            ;;
        all|*)
            print_status "Showing combined logs (Press Ctrl+C to exit)"
            print_status "Backend log: logs/finance-backend.log"
            print_status "Frontend log: logs/finance-frontend.log"
            echo ""
            
            # Show both logs simultaneously if they exist
            BACKEND_LOG="$PROJECT_ROOT/logs/finance-backend.log"
            FRONTEND_LOG="$PROJECT_ROOT/logs/finance-frontend.log"
            
            if [ -f "$BACKEND_LOG" ] && [ -f "$FRONTEND_LOG" ]; then
                tail -f -n 25 "$BACKEND_LOG" "$FRONTEND_LOG"
            elif [ -f "$BACKEND_LOG" ]; then
                tail -f -n 50 "$BACKEND_LOG"
            elif [ -f "$FRONTEND_LOG" ]; then
                tail -f -n 50 "$FRONTEND_LOG"
            else
                print_warning "No log files found"
            fi
            ;;
    esac
}

open_browser() {
    print_header
    echo -e "${CYAN}Opening Financial Data Processor${NC}"
    print_header
    
    local frontend_url="http://localhost:3000"
    local backend_url="http://localhost:8000/docs"
    
    print_status "Frontend: $frontend_url"
    print_status "API Docs: $backend_url"
    
    # Try to open in browser (works on most systems)
    if command -v xdg-open > /dev/null; then
        xdg-open "$frontend_url" 2>/dev/null &
        print_success "Opened in default browser"
    elif command -v open > /dev/null; then
        open "$frontend_url" 2>/dev/null &
        print_success "Opened in default browser"
    else
        print_warning "Could not detect browser command"
        print_status "Please open: $frontend_url"
    fi
}

start_backend_only() {
    print_header
    echo -e "${CYAN}Starting Backend Only${NC}"
    print_header
    bash "$BACKEND_SCRIPT" start "${@}"
}

start_frontend_only() {
    print_header
    echo -e "${CYAN}Starting Frontend Only${NC}"
    print_header
    bash "$FRONTEND_SCRIPT" start "${@}"
}

stop_backend_only() {
    print_header
    echo -e "${CYAN}Stopping Backend Only${NC}"
    print_header
    bash "$BACKEND_SCRIPT" stop
}

stop_frontend_only() {
    print_header
    echo -e "${CYAN}Stopping Frontend Only${NC}"
    print_header
    bash "$FRONTEND_SCRIPT" stop
}

restart_backend_only() {
    print_header
    echo -e "${CYAN}Restarting Backend Only${NC}"
    print_header
    bash "$BACKEND_SCRIPT" restart "${@}"
}

restart_frontend_only() {
    print_header
    echo -e "${CYAN}Restarting Frontend Only${NC}"
    print_header
    bash "$FRONTEND_SCRIPT" restart "${@}"
}

show_help() {
    cat << EOF
${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}
${CYAN}Financial Data Processor - Unified Management Script${NC}
${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}

${YELLOW}Usage:${NC} $0 [COMMAND] [OPTIONS]

${YELLOW}Main Commands:${NC}
  ${GREEN}start${NC}               Start both backend and frontend
  ${GREEN}stop${NC}                Stop both backend and frontend
  ${GREEN}restart${NC}             Restart both backend and frontend
  ${GREEN}status${NC}              Show status of all services
  ${GREEN}logs${NC}                Show logs from all services

${YELLOW}Individual Service Commands:${NC}
  ${GREEN}start-backend${NC}       Start backend only
  ${GREEN}start-frontend${NC}      Start frontend only
  ${GREEN}stop-backend${NC}        Stop backend only
  ${GREEN}stop-frontend${NC}       Stop frontend only
  ${GREEN}restart-backend${NC}     Restart backend only
  ${GREEN}restart-frontend${NC}    Restart frontend only

${YELLOW}Utility Commands:${NC}
  ${GREEN}open${NC}                Open application in browser
  ${GREEN}logs-backend${NC}        Show backend logs only
  ${GREEN}logs-frontend${NC}       Show frontend logs only
  ${GREEN}help${NC}                Show this help message

${YELLOW}Options:${NC}
  ${CYAN}-b, --background${NC}    Start in background mode (default)
  ${CYAN}-f, --foreground${NC}    Start in foreground mode

${YELLOW}Examples:${NC}
  $0 start              ${BLUE}# Start both services in background${NC}
  $0 start -f           ${BLUE}# Start both services in foreground${NC}
  $0 stop               ${BLUE}# Stop all services${NC}
  $0 restart            ${BLUE}# Restart all services${NC}
  $0 status             ${BLUE}# Check service status${NC}
  $0 logs               ${BLUE}# View combined logs${NC}
  $0 start-backend -f   ${BLUE}# Start only backend in foreground${NC}
  $0 open               ${BLUE}# Open application in browser${NC}

${YELLOW}Service URLs:${NC}
  Frontend:  ${CYAN}http://localhost:3000${NC}
  Backend:   ${CYAN}http://localhost:8000${NC}
  API Docs:  ${CYAN}http://localhost:8000/docs${NC}

${YELLOW}Log Files:${NC}
  Backend:   ${CYAN}logs/finance-backend.log${NC}
  Frontend:  ${CYAN}logs/finance-frontend.log${NC}

${YELLOW}Configuration:${NC}
  Backend:   ${CYAN}scripts/backend.env${NC}
  Frontend:  ${CYAN}scripts/frontend.env${NC}

${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}
EOF
}

# Check dependencies before running any command
check_dependencies

# Parse command
case "${1:-help}" in
    start)
        background=true
        if [ "$2" = "-f" ] || [ "$2" = "--foreground" ]; then
            background=false
        fi
        start_all "$background"
        ;;
    stop)
        stop_all
        ;;
    restart)
        background=true
        if [ "$2" = "-f" ] || [ "$2" = "--foreground" ]; then
            background=false
        fi
        restart_all "$background"
        ;;
    status)
        status_all
        ;;
    logs)
        show_logs all
        ;;
    logs-backend)
        show_logs backend
        ;;
    logs-frontend)
        show_logs frontend
        ;;
    start-backend)
        shift
        start_backend_only "$@"
        ;;
    start-frontend)
        shift
        start_frontend_only "$@"
        ;;
    stop-backend)
        stop_backend_only
        ;;
    stop-frontend)
        stop_frontend_only
        ;;
    restart-backend)
        shift
        restart_backend_only "$@"
        ;;
    restart-frontend)
        shift
        restart_frontend_only "$@"
        ;;
    open)
        open_browser
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
