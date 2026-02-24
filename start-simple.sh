#!/bin/bash
#
# Simple startup script - works without Redis/Celery
# For development and testing
#

set -e

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Resume Template Engine - Simple Mode${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

cd "$APP_DIR"

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo -e "${RED}✗ uv is not installed${NC}"
    echo ""
    echo "Install it with:"
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo ""
    exit 1
fi

echo -e "${GREEN}✓${NC} uv found"

# Load environment variables
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | grep -v '^$' | xargs)
    echo -e "${GREEN}✓${NC} Environment loaded from .env"
else
    echo -e "${YELLOW}⚠${NC} No .env file found, using defaults"
    # Set defaults for running without Redis
    export CACHE_ENABLED=false
    export RATE_LIMIT_ENABLED=false
fi

# Disable cache and rate limiting if Redis not available
export CACHE_ENABLED=false
export RATE_LIMIT_ENABLED=false

echo -e "${YELLOW}⚠${NC} Running in simple mode (no Redis/Celery)"
echo ""

# Check port
PORT=${1:-8501}

echo -e "${BLUE}Starting API server on port $PORT...${NC}"
echo ""
echo "Access points:"
echo "  API:  http://localhost:$PORT"
echo "  Docs: http://localhost:$PORT/docs"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
echo ""

# Start with uvicorn (simpler than gunicorn for development)
uv run uvicorn src.resume_agent_template_engine.api.app:app \
    --host 0.0.0.0 \
    --port "$PORT" \
    --workers 4 \
    --log-level info

# If uvicorn fails, try with python directly
if [ $? -ne 0 ]; then
    echo ""
    echo -e "${YELLOW}Trying alternative startup method...${NC}"
    uv run python -c "
import uvicorn
from src.resume_agent_template_engine.api.app import app

uvicorn.run(app, host='0.0.0.0', port=$PORT, workers=4)
"
fi
