"""SSH Execution Tool for Ouroboros

Allows direct command execution on remote servers via SSH.
"""

import paramiko
import time
from typing import Dict, List, Tuple, Optional

from ouroboros.tools.registry import ToolEntry, ToolContext


def _ssh_execute(ctx: ToolContext, host: str, username: str, password: str, command: str, timeout: int = 30) -> str:
    """Execute a single command on remote server via SSH."""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(host, username=username, password=password, timeout=timeout)
        stdin, stdout, stderr = ssh.exec_command(command, timeout=timeout)
        exit_code = stdout.channel.recv_exit_status()
        output = stdout.read().decode()
        error = stderr.read().decode()
        
        result = f"exit_code={exit_code}\n"
        if output:
            result += f"STDOUT:\n{output}\n"
        if error:
            result += f"STDERR:\n{error}\n"
        return result
    except Exception as e:
        return f"⚠️ SSH command failed: {e}"
    finally:
        ssh.close()


def _ssh_execute_batch(ctx: ToolContext, host: str, username: str, password: str, commands: List[str], timeout: int = 30) -> str:
    """Execute multiple commands on remote server via SSH."""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    results = []
    try:
        ssh.connect(host, username=username, password=password, timeout=timeout)
        
        for cmd in commands:
            try:
                stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
                exit_code = stdout.channel.recv_exit_status()
                output = stdout.read().decode()
                error = stderr.read().decode()
                
                results.append({
                    "command": cmd,
                    "success": exit_code == 0,
                    "exit_code": exit_code,
                    "output": output,
                    "error": error
                })
            except Exception as e:
                results.append({
                    "command": cmd,
                    "success": False,
                    "exit_code": -1,
                    "output": "",
                    "error": str(e)
                })
    except Exception as e:
        results.append({
            "command": "CONNECT",
            "success": False,
            "exit_code": -1,
            "output": "",
            "error": str(e)
        })
    finally:
        ssh.close()
    
    # Format results as text
    output_lines = []
    for r in results:
        output_lines.append(f"Command: {r['command']}")
        output_lines.append(f"  Exit code: {r['exit_code']}")
        if r['output']:
            output_lines.append(f"  STDOUT:\n{r['output']}")
        if r['error']:
            output_lines.append(f"  STDERR:\n{r['error']}")
        output_lines.append("")
    
    return "\n".join(output_lines)


def get_tools() -> List[ToolEntry]:
    return [
        ToolEntry("ssh_execute", {
            "name": "ssh_execute",
            "description": "Execute a command on a remote server via SSH",
            "parameters": {
                "type": "object",
                "properties": {
                    "host": {"type": "string", "description": "Remote host IP or hostname"},
                    "username": {"type": "string", "description": "SSH username"},
                    "password": {"type": "string", "description": "SSH password"},
                    "command": {"type": "string", "description": "Command to execute"},
                    "timeout": {"type": "integer", "description": "Timeout in seconds", "default": 30}
                },
                "required": ["host", "username", "password", "command"]
            }
        }, _ssh_execute),
        ToolEntry("ssh_execute_batch", {
            "name": "ssh_execute_batch",
            "description": "Execute multiple commands on a remote server via SSH",
            "parameters": {
                "type": "object",
                "properties": {
                    "host": {"type": "string", "description": "Remote host IP or hostname"},
                    "username": {"type": "string", "description": "SSH username"},
                    "password": {"type": "string", "description": "SSH password"},
                    "commands": {"type": "array", "items": {"type": "string"}, "description": "Commands to execute"},
                    "timeout": {"type": "integer", "description": "Timeout in seconds", "default": 30}
                },
                "required": ["host", "username", "password", "commands"]
            }
        }, _ssh_execute_batch),
    ]
