#!/bin/bash
# Remote Executor Wrapper Script
# Automatically generates token and starts the remote executor server
# Usage: ./remote_executor_wrapper.sh [PORT]

# Generate secure token based on timestamp and random string
generate_token() {
    # Format: ourob_<timestamp>_<random>
    local timestamp=$(date +%s)
    local random=$(head -c 16 /dev/urandom | md5sum | cut -d' ' -f1)
    echo "ourob_${timestamp}_${random}"
}

# Set default port (can be overridden)
PORT=${1:-8080}

# Generate or use provided token
if [ -n "$2" ]; then
    TOKEN="$2"
    echo "Using provided token: $TOKEN"
else
    TOKEN=$(generate_token)
    echo "Generated new token: $TOKEN"
fi

# Set environment variables
export REMOTE_EXECUTOR_TOKEN="$TOKEN"
export REMOTE_EXECUTOR_PORT="$PORT"
export REMOTE_EXECUTOR_HOST="0.0.0.0"

# Print connection info
echo ""
echo "========================================="
echo "Remote Executor Server Starting"
echo "========================================="
echo "Port: $PORT"
echo "Token: $TOKEN"
echo "Host: 0.0.0.0 (accessible from any interface)"
echo ""
echo "To connect from Ouroboros:"
echo "  POST http://localhost:$PORT/?token=$TOKEN"
echo ""
echo "Health check:"
echo "  GET http://localhost:$PORT/health"
echo "========================================="
echo ""

# Start the remote executor server
cd "$(dirname "$0")"
exec python3 remote_executor.py