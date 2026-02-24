#!/bin/bash
#
# Production startup script for Resume Template Engine
# Handles 10,000+ concurrent users
#
# Usage: ./start-production.sh [start|stop|restart|status]

set -e

# Configuration
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$APP_DIR/.venv"
PID_DIR="/var/run/resume-api"
LOG_DIR="/var/log/resume-api"

# PIDs
GUNICORN_PID="$PID_DIR/gunicorn.pid"
CELERY_PID="$PID_DIR/celery-worker.pid"
FLOWER_PID="$PID_DIR/celery-flower.pid"

# Logs
GUNICORN_LOG="$LOG_DIR/gunicorn.log"
CELERY_LOG="$LOG_DIR/celery-worker.log"
FLOWER_LOG="$LOG_DIR/celery-flower.log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

# Create directories
setup_directories() {
    sudo mkdir -p "$PID_DIR" "$LOG_DIR"
    sudo chown -R $USER:$USER "$PID_DIR" "$LOG_DIR"
    print_success "Directories created"
}

# Check if service is running
is_running() {
    local pid_file=$1
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        fi
    fi
    return 1
}

# Start Gunicorn
start_gunicorn() {
    print_info "Starting Gunicorn (API server)..."

    if is_running "$GUNICORN_PID"; then
        print_error "Gunicorn is already running (PID: $(cat $GUNICORN_PID))"
        return 1
    fi

    cd "$APP_DIR"

    # Load environment
    if [ -f ".env" ]; then
        export $(cat .env | grep -v '^#' | xargs)
    fi

    # Start Gunicorn
    uv run gunicorn src.resume_agent_template_engine.api.app:app \
        --config gunicorn.conf.py \
        --daemon \
        --pid "$GUNICORN_PID" \
        --access-logfile "$GUNICORN_LOG" \
        --error-logfile "$GUNICORN_LOG"

    sleep 2

    if is_running "$GUNICORN_PID"; then
        print_success "Gunicorn started (PID: $(cat $GUNICORN_PID))"
        return 0
    else
        print_error "Failed to start Gunicorn"
        return 1
    fi
}

# Start Celery Workers
start_celery() {
    print_info "Starting Celery workers..."

    if is_running "$CELERY_PID"; then
        print_error "Celery is already running (PID: $(cat $CELERY_PID))"
        return 1
    fi

    cd "$APP_DIR"

    # Load environment
    if [ -f ".env" ]; then
        export $(cat .env | grep -v '^#' | xargs)
    fi

    # Start Celery
    uv run celery -A resume_agent_template_engine.workers.celery_app worker \
        --loglevel=info \
        --concurrency=${CELERY_WORKERS:-32} \
        --max-tasks-per-child=100 \
        --prefetch-multiplier=1 \
        --detach \
        --pidfile="$CELERY_PID" \
        --logfile="$CELERY_LOG"

    sleep 2

    if is_running "$CELERY_PID"; then
        print_success "Celery started (PID: $(cat $CELERY_PID))"
        return 0
    else
        print_error "Failed to start Celery"
        return 1
    fi
}

# Start Flower (Celery monitoring)
start_flower() {
    print_info "Starting Flower (monitoring)..."

    if is_running "$FLOWER_PID"; then
        print_error "Flower is already running (PID: $(cat $FLOWER_PID))"
        return 1
    fi

    cd "$APP_DIR"

    # Load environment
    if [ -f ".env" ]; then
        export $(cat .env | grep -v '^#' | xargs)
    fi

    # Start Flower
    uv run celery -A resume_agent_template_engine.workers.celery_app flower \
        --port=5555 \
        --detach \
        --pidfile="$FLOWER_PID" \
        --logfile="$FLOWER_LOG"

    sleep 2

    if is_running "$FLOWER_PID"; then
        print_success "Flower started (PID: $(cat $FLOWER_PID)) - http://localhost:5555"
        return 0
    else
        print_error "Failed to start Flower"
        return 1
    fi
}

# Stop services
stop_service() {
    local service_name=$1
    local pid_file=$2

    print_info "Stopping $service_name..."

    if ! is_running "$pid_file"; then
        print_error "$service_name is not running"
        return 1
    fi

    local pid=$(cat "$pid_file")
    kill "$pid" 2>/dev/null || true

    # Wait for graceful shutdown
    local count=0
    while is_running "$pid_file" && [ $count -lt 10 ]; do
        sleep 1
        count=$((count + 1))
    done

    # Force kill if still running
    if is_running "$pid_file"; then
        print_info "Force killing $service_name..."
        kill -9 "$pid" 2>/dev/null || true
        sleep 1
    fi

    rm -f "$pid_file"
    print_success "$service_name stopped"
}

# Check status
check_status() {
    echo ""
    echo "=== Resume Template Engine Status ==="
    echo ""

    # Gunicorn
    if is_running "$GUNICORN_PID"; then
        print_success "Gunicorn: Running (PID: $(cat $GUNICORN_PID))"
    else
        print_error "Gunicorn: Stopped"
    fi

    # Celery
    if is_running "$CELERY_PID"; then
        print_success "Celery: Running (PID: $(cat $CELERY_PID))"
    else
        print_error "Celery: Stopped"
    fi

    # Flower
    if is_running "$FLOWER_PID"; then
        print_success "Flower: Running (PID: $(cat $FLOWER_PID))"
    else
        print_error "Flower: Stopped"
    fi

    echo ""

    # Check API health
    if curl -s http://localhost:8501/health > /dev/null 2>&1; then
        print_success "API: Healthy"
    else
        print_error "API: Not responding"
    fi

    # Check Redis
    if redis-cli ping > /dev/null 2>&1; then
        print_success "Redis: Connected"
    else
        print_error "Redis: Not available"
    fi

    echo ""
}

# Main commands
cmd_start() {
    echo ""
    echo "Starting Resume Template Engine (Production Mode)"
    echo "=================================================="
    echo ""

    setup_directories

    start_gunicorn
    start_celery
    start_flower

    echo ""
    print_success "All services started!"
    echo ""
    echo "Access points:"
    echo "  API:     http://localhost:8501"
    echo "  Docs:    http://localhost:8501/docs"
    echo "  Metrics: http://localhost:8501/metrics"
    echo "  Flower:  http://localhost:5555"
    echo ""
    echo "View logs:"
    echo "  tail -f $GUNICORN_LOG"
    echo "  tail -f $CELERY_LOG"
    echo ""
}

cmd_stop() {
    echo ""
    echo "Stopping Resume Template Engine"
    echo "==============================="
    echo ""

    stop_service "Gunicorn" "$GUNICORN_PID"
    stop_service "Celery" "$CELERY_PID"
    stop_service "Flower" "$FLOWER_PID"

    echo ""
    print_success "All services stopped"
    echo ""
}

cmd_restart() {
    cmd_stop
    sleep 2
    cmd_start
}

cmd_status() {
    check_status
}

# Parse command
case "${1:-}" in
    start)
        cmd_start
        ;;
    stop)
        cmd_stop
        ;;
    restart)
        cmd_restart
        ;;
    status)
        cmd_status
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        echo ""
        echo "Commands:"
        echo "  start    - Start all services (Gunicorn, Celery, Flower)"
        echo "  stop     - Stop all services"
        echo "  restart  - Restart all services"
        echo "  status   - Check status of all services"
        echo ""
        exit 1
        ;;
esac

exit 0
