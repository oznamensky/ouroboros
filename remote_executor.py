#!/usr/bin/env python3
"""
Remote SSH Executor - HTTP Server
Accepts commands from Ouroboros and executes them on the server.
For installing V2Ray + WebSocket + TLS for Telegram proxy without VPN.

SECURITY: All credentials and tokens must be provided via environment variables.
"""

import http.server
import socketserver
import json
import subprocess
import sys
import threading
import time
import os
from urllib.parse import urlparse, parse_qs

# Configuration from environment variables (secure)
PORT = int(os.getenv('REMOTE_EXECUTOR_PORT', '8080'))
HOST = os.getenv('REMOTE_EXECUTOR_HOST', '0.0.0.0')
TOKEN = os.getenv('REMOTE_EXECUTOR_TOKEN')  # Must be set via environment
AUTH_KEY = 'token'

# Required: Set REMOTE_EXECUTOR_TOKEN environment variable
if not TOKEN:
    print("⚠️  SECURITY ERROR: REMOTE_EXECUTOR_TOKEN environment variable not set!")
    print("   Set it with: export REMOTE_EXECUTOR_TOKEN='your-secret-token'")
    sys.exit(1)

class RemoteExecutorHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        """Handle POST requests with commands to execute"""
        try:
            # Parse URL and check authentication
            parsed_path = urlparse(self.path)
            query_params = parse_qs(parsed_path.query)
            
            # Check token
            provided_token = query_params.get(AUTH_KEY, [None])[0]
            if provided_token != TOKEN:
                self.send_error(403, "Forbidden: Invalid token")
                return
            
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            
            # Parse JSON command
            try:
                data = json.loads(body)
                command = data.get('command')
                if not command:
                    self.send_error(400, "Bad Request: 'command' field required")
                    return
            except json.JSONDecodeError:
                self.send_error(400, "Bad Request: Invalid JSON")
                return
            
            # Execute command
            try:
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minute timeout
                )
                
                response = {
                    'exit_code': result.returncode,
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                    'success': result.returncode == 0
                }
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
                
            except subprocess.TimeoutExpired:
                self.send_error(408, "Request Timeout: Command took too long")
            except Exception as e:
                self.send_error(500, f"Internal Server Error: {str(e)}")
                
        except Exception as e:
            self.send_error(500, f"Internal Server Error: {str(e)}")
    
    def do_GET(self):
        """Handle GET requests for health check"""
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'ok', 'service': 'remote-executor'}).encode('utf-8'))
        else:
            self.send_error(404, "Not Found")
    
    def log_message(self, format, *args):
        """Custom log format"""
        print(f"[RemoteExecutor] {self.address_string()} - {format % args}")

def run_server():
    """Start the HTTP server"""
    with socketserver.TCPServer((HOST, PORT), RemoteExecutorHandler) as httpd:
        print(f"Remote Executor Server started on http://{HOST}:{PORT}")
        print(f"Authentication token: (from environment)")
        print(f"Use: POST http://localhost:{PORT}/?token=YOUR_TOKEN")
        print("Press Ctrl+C to stop")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")
            httpd.shutdown()

if __name__ == '__main__':
    print("Remote SSH Executor - Starting...")
    print(f"Listening on: http://{HOST}:{PORT}")
    print("-" * 50)
    run_server()