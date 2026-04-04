# Remote Executor Wrapper Script

## Overview
The `remote_executor_wrapper.sh` script automatically handles token generation and starts the remote executor server with minimal user effort.

## Usage

### One-Command Launch
```bash
./remote_executor_wrapper.sh
```

This automatically:
1. Generates a secure random token
2. Sets the `REMOTE_EXECUTOR_TOKEN` environment variable
3. Starts the server on port 8080

### Custom Port
```bash
./remote_executor_wrapper.sh 9090
```

### Custom Token (optional)
```bash
./remote_executor_wrapper.sh 8080 my-custom-token
```

## Generated Token Format
Tokens follow the pattern: `ourob_<timestamp>_<random>`
- Example: `ourob_1743752576_a3f8b2c1d4e5f6`

## Server Details
- **Host**: 0.0.0.0 (accessible from any interface)
- **Port**: 8080 (default, customizable)
- **Health Check**: `GET http://localhost:8080/health`
- **Command Execution**: `POST http://localhost:8080/?token=<your-token>`

## Security Notes
- Token is automatically generated with high entropy
- Server requires token authentication for all POST requests
- Commands are executed with server user permissions (root)