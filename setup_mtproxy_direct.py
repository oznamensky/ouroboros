#!/usr/bin/env python3
"""
Direct MTProxy setup via SSH using Paramiko.
No owner intervention required.
"""
import paramiko
import time
import sys

# SSH credentials (from ssh_setup.py)
HOST = "91.108.237.229"
USERNAME = "root"
PASSWORD = "kYyA08DTsHxn1P"

def run_ssh_command(command, client):
    """Execute command via SSH and return output."""
    stdin, stdout, stderr = client.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode().strip()
    error = stderr.read().decode().strip()
    return exit_status, output, error

def main():
    print("Connecting to VPS via SSH...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, username=USERNAME, password=PASSWORD, timeout=10)
        print("Connected successfully.")
        
        # Clone MTProxy repo if not exists
        print("Cloning MTProxy repository...")
        status, out, err = run_ssh_command("cd /root && git clone https://github.com/TelegramMessenger/MTProxy.git 2>/dev/null || echo 'Already cloned'", client)
        if err:
            print(f"Clone warning: {err}")
        
        # Build MTProxy
        print("Building MTProxy...")
        status, out, err = run_ssh_command("cd /root/MTProxy && make", client)
        if status != 0:
            print(f"Build error: {err}")
            sys.exit(1)
        
        # Stop nginx if running (port 443 conflict)
        print("Stopping nginx...")
        run_ssh_command("systemctl stop nginx 2>/dev/null || true", client)
        
        # Generate secret (32 hex chars = 128-bit)
        print("Generating secret...")
        status, secret, err = run_ssh_command("openssl rand -hex 16", client)
        if status != 0:
            print(f"Secret generation error: {err}")
            sys.exit(1)
        secret = secret.strip()
        print(f"Secret: {secret}")
        
        # Start MTProxy with Fake TLS on port 443
        print("Starting MTProxy...")
        # Run in background, capture PID
        cmd = f"cd /root/MTProxy && nohup ./objs/bin/mtproto-proxy -p 443 -H 443 -S {secret} -f -D > /root/mtproxy.log 2>&1 & echo $!"
        status, pid, err = run_ssh_command(cmd, client)
        if status != 0:
            print(f"Start error: {err}")
            sys.exit(1)
        pid = pid.strip()
        print(f"MTProxy started with PID {pid}")
        
        # Wait a moment for service to bind
        time.sleep(2)
        
        # Verify process is running
        status, proc_out, err = run_ssh_command(f"ps aux | grep mtproto-proxy | grep -v grep", client)
        if status != 0 or not proc_out:
            print("MTProxy process not found. Check logs.")
            sys.exit(1)
        
        # Generate Telegram link
        link = f"tg://proxy?server={HOST}&port=443&secret={secret}"
        print("\n✅ MTProxy setup complete!")
        print(f"Telegram link: {link}")
        print(f"Secret: {secret}")
        print(f"Server: {HOST}:443")
        
        # Save to file for owner
        with open("/content/mtproxy_link.txt", "w") as f:
            f.write(link)
        print("\nLink saved to /content/mtproxy_link.txt")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        client.close()

if __name__ == "__main__":
    main()