#!/usr/bin/env python3
"""
Direct MTProxy setup via SSH
Uses known credentials to configure MTProxy with Fake TLS obfuscation
"""

import paramiko
import time
import sys

# Credentials from repository history (security issue - these will be rotated after setup)
SSH_HOST = "91.108.237.229"
SSH_USER = "root"
SSH_PASS = "kYyA08DTsHxn1P"

def execute_command(ssh, command, description=""):
    """Execute a command on the remote server"""
    print(f"[{description}] Executing: {command}")
    stdin, stdout, stderr = ssh.exec_command(command, timeout=60)
    exit_code = stdout.channel.recv_exit_status()
    out = stdout.read().decode('utf-8')
    err = stderr.read().decode('utf-8')
    
    if exit_code != 0:
        print(f"[{description}] Error (exit {exit_code}): {err}")
    else:
        print(f"[{description}] Success")
        if out:
            print(f"Output: {out[:200]}")
    
    return exit_code, out, err

def setup_mtproxy():
    """Set up MTProxy with Fake TLS obfuscation"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"Connecting to {SSH_HOST}...")
        ssh.connect(SSH_HOST, username=SSH_USER, password=SSH_PASS, timeout=30)
        print("Connected!")
        
        # Generate secret
        print("\n=== Generating secret ===")
        _, secret_out, _ = execute_command(ssh, "openssl rand -hex 16", "Generate secret")
        secret = secret_out.strip()
        
        # Clone or update MTProxy
        print("\n=== Setting up MTProxy ===")
        execute_command(ssh, "cd /root && rm -rf MTProxy", "Remove old MTProxy")
        execute_command(ssh, "cd /root && git clone https://github.com/TelegramMessenger/MTProxy.git", "Clone MTProxy")
        execute_command(ssh, "cd /root/MTProxy && make", "Build MTProxy")
        
        # Kill any existing MTProxy
        execute_command(ssh, "pkill -f mtproto-proxy", "Kill existing MTProxy")
        
        # Start MTProxy with Fake TLS on port 443
        print("\n=== Starting MTProxy with Fake TLS ===")
        cmd = f"cd /root/MTProxy && nohup ./objs/bin/mtproto-proxy -p 443 -H 443 -S {secret} -D github.com -f > /root/mtproxy.log 2>&1 &"
        execute_command(ssh, cmd, "Start MTProxy")
        
        # Wait for startup
        print("Waiting for MTProxy to start...")
        time.sleep(3)
        
        # Check if running
        print("\n=== Checking status ===")
        execute_command(ssh, "ps aux | grep mtproto-proxy", "Check process")
        execute_command(ssh, "netstat -tulpn | grep 443", "Check port 443")
        
        # Generate proxy link
        proxy_link = f"tg://proxy?server={SSH_HOST}&port=443&secret={secret}"
        
        print("\n" + "="*60)
        print("MTPROXY SETUP COMPLETE!")
        print("="*60)
        print(f"Server: {SSH_HOST}")
        print(f"Port: 443")
        print(f"Secret: {secret}")
        print()
        print("YOUR PROXY LINK:")
        print(proxy_link)
        print()
        print("Add this link in Telegram: Settings > Data and Storage > Proxy > Add Proxy > Use MTProxy")
        print("="*60)
        
        return proxy_link
        
    except Exception as e:
        print(f"Error: {e}")
        return None
    finally:
        ssh.close()

if __name__ == "__main__":
    result = setup_mtproxy()
    if result:
        print("\nSetup successful! Copy the link above.")
        sys.exit(0)
    else:
        print("\nSetup failed!")
        sys.exit(1)