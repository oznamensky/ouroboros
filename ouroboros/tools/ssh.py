"""SSH tools for remote server execution."""

from __future__ import annotations

import logging
from typing import List, Optional

from ouroboros.tools.registry import ToolContext, ToolEntry

log = logging.getLogger(__name__)


def _ssh_connect(ctx: ToolContext, host: str, username: str, password: str, port: int = 22) -> str:
    """Test SSH connection to a server."""
    try:
        import paramiko
    except ImportError:
        return "⚠️ paramiko not installed. Run: pip install paramiko"

    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, port=port, username=username, password=password, timeout=10)
        
        # Test basic command
        stdin, stdout, stderr = client.exec_command("echo 'SSH connection successful'")
        output = stdout.read().decode().strip()
        
        client.close()
        return f"✅ SSH connection successful to {host}\nOutput: {output}"
    except Exception as e:
        return f"⚠️ SSH connection failed: {e}"


def _ssh_run_command(ctx: ToolContext, host: str, username: str, password: str, 
                     command: str, port: int = 22) -> str:
    """Run a command on a remote server via SSH."""
    try:
        import paramiko
    except ImportError:
        return "⚠️ paramiko not installed. Run: pip install paramiko"

    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, port=port, username=username, password=password, timeout=30)
        
        # Execute command
        stdin, stdout, stderr = client.exec_command(command, timeout=120)
        
        # Read output
        stdout_text = stdout.read().decode()
        stderr_text = stderr.read().decode()
        exit_code = stdout.channel.recv_exit_status()
        
        client.close()
        
        result = f"exit_code={exit_code}\n"
        if stdout_text:
            result += f"STDOUT:\n{stdout_text}\n"
        if stderr_text:
            result += f"STDERR:\n{stderr_text}\n"
        
        return result
    except Exception as e:
        return f"⚠️ SSH command failed: {e}"


def _ssh_fix_mtproxy(ctx: ToolContext, host: str, username: str, password: str, port: int = 22) -> str:
    """Fix MTProxy configuration on the remote server and return the working proxy link."""
    try:
        import paramiko
    except ImportError:
        return "⚠️ paramiko not installed. Run: pip install paramiko"

    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, port=port, username=username, password=password, timeout=30)
        
        # Commands to fix MTProxy
        commands = [
            # Stop nginx to free port 443
            "systemctl stop nginx",
            
            # Generate correct 32-char secret
            "SECRET=$(openssl rand -hex 16)",
            
            # Create correct systemd service file
            """cat > /etc/systemd/system/mtproxy.service << 'EOF'
[Unit]
Description=MTProxy Telegram Proxy
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/MTProxy
ExecStart=/root/MTProxy/objs/bin/mtproto-proxy -p 19196 -H 443 -S $SECRET -D github.com -l /var/log/mtproxy.log
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF""",
            
            # Reload and start
            "systemctl daemon-reload",
            "systemctl enable mtproxy",
            "systemctl start mtproxy",
            
            # Wait and check status
            "sleep 2",
            "systemctl status mtproxy --no-pager",
            
            # Get the secret for the link
            "echo $SECRET",
        ]
        
        full_command = " && ".join(commands)
        
        stdin, stdout, stderr = client.exec_command(full_command, timeout=120)
        
        stdout_text = stdout.read().decode()
        stderr_text = stderr.read().decode()
        exit_code = stdout.channel.recv_exit_status()
        
        client.close()
        
        # Extract the secret from output
        secret = None
        for line in stdout_text.split('\n'):
            if len(line) == 32 and all(c in '0123456789abcdef' for c in line):
                secret = line
                break
        
        # Generate proxy link
        if secret and exit_code == 0:
            proxy_link = f"tg://proxy?server={host}&port=19196&secret={secret}"
            https_link = f"https://t.me/proxy?server={host}&port=19196&secret={secret}"
            
            result = f"✅ MTProxy configured successfully!\n\n"
            result += f"Secret: {secret}\n\n"
            result += f"Proxy Link (tg://):\n{proxy_link}\n\n"
            result += f"Proxy Link (https://):\n{https_link}\n\n"
            result += f"--- Command Output ---\n"
            result += f"exit_code={exit_code}\n"
            if stdout_text:
                result += f"STDOUT:\n{stdout_text[-1000:]}\n"  # Last 1000 chars
            if stderr_text:
                result += f"STDERR:\n{stderr_text}\n"
            
            return result
        else:
            result = f"⚠️ MTProxy configuration may have failed\n"
            result += f"exit_code={exit_code}\n"
            result += f"STDOUT:\n{stdout_text}\n"
            result += f"STDERR:\n{stderr_text}\n"
            return result
            
    except Exception as e:
        return f"⚠️ SSH operation failed: {e}"


def get_tools() -> List[ToolEntry]:
    return [
        ToolEntry("ssh_connect", {
            "name": "ssh_connect",
            "description": "Test SSH connection to a remote server.",
            "parameters": {"type": "object", "properties": {
                "host": {"type": "string", "description": "Server IP or hostname"},
                "username": {"type": "string", "description": "SSH username"},
                "password": {"type": "string", "description": "SSH password"},
                "port": {"type": "integer", "description": "SSH port", "default": 22},
            }, "required": ["host", "username", "password"]},
        }, _ssh_connect),
        ToolEntry("ssh_run_command", {
            "name": "ssh_run_command",
            "description": "Run a command on a remote server via SSH.",
            "parameters": {"type": "object", "properties": {
                "host": {"type": "string", "description": "Server IP or hostname"},
                "username": {"type": "string", "description": "SSH username"},
                "password": {"type": "string", "description": "SSH password"},
                "command": {"type": "string", "description": "Command to execute"},
                "port": {"type": "integer", "description": "SSH port", "default": 22},
            }, "required": ["host", "username", "password", "command"]},
        }, _ssh_run_command),
        ToolEntry("ssh_fix_mtproxy", {
            "name": "ssh_fix_mtproxy",
            "description": "Fix MTProxy configuration on remote server and return working proxy link.",
            "parameters": {"type": "object", "properties": {
                "host": {"type": "string", "description": "Server IP or hostname"},
                "username": {"type": "string", "description": "SSH username"},
                "password": {"type": "string", "description": "SSH password"},
                "port": {"type": "integer", "description": "SSH port", "default": 22},
            }, "required": ["host", "username", "password"]},
        }, _ssh_fix_mtproxy),
    ]
