#!/bin/bash
# Remote Executor Wrapper Script
# Automatically generates token and starts the remote executor server
# Usage: ./remote_executor_wrapper.sh [PORT] [TOKEN]

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Generate secure token based on timestamp and random string
generate_token() {
    # Format: ourob_<timestamp>_<random>
    local timestamp=$(date +%s)
    local random=$(head -c 16 /dev/urandom | md5sum | cut -d' ' -f1)
    echo "ourob_${timestamp}_${random}"
}

# Parse arguments
PORT=${1:-8080}
CUSTOM_TOKEN=$2

# Validate port is a number
if ! [[ "$PORT" =~ ^[0-9]+$ ]]; then
    echo -e "${RED}Error: Port must be a number${NC}"
    echo "Usage: ./remote_executor_wrapper.sh [PORT] [TOKEN]"
    exit 1
fi

# Generate or use provided token
if [ -n "$CUSTOM_TOKEN" ]; then
    TOKEN="$CUSTOM_TOKEN"
    echo -e "${YELLOW}Using provided token: $TOKEN${NC}"
else
    TOKEN=$(generate_token)
    echo -e "${GREEN}Generated new token: $TOKEN${NC}"
fi

# Set environment variables
export REMOTE_EXECUTOR_TOKEN="$TOKEN"
export REMOTE_EXECUTOR_PORT="$PORT"
export REMOTE_EXECUTOR_HOST="0.0.0.0"

# Print connection info
echo ""
echo "========================================="
echo -e "${BLUE}Remote Executor Server Starting${NC}"
echo "========================================="
echo "Port: $PORT"
echo "Token: $TOKEN"
echo "Host: 0.0.0.0 (accessible from any interface)"
echo ""
echo -e "${YELLOW}To connect from Ouroboros:${NC}"
echo "  POST http://localhost:$PORT/?token=$TOKEN"
echo ""
echo -e "${YELLOW}Health check:${NC}"
echo "  GET http://localhost:$PORT/health"
echo "========================================="
echo ""

# Start the remote executor server
cd "$(dirname "$0")"
echo -e "${GREEN}Starting server...${NC}"
exec python3 remote_executor.py