#!/usr/bin/env python3
"""
Setup MTProxy with real TLS (not Fake TLS) to avoid DPI detection.
Uses self-signed SSL certificate on port 443.
"""
import paramiko
import time
import sys
import random

# SSH credentials
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
        print("Connected successfully.\n")
        
        # Generate SSL certificate (self-signed)
        print("=== Generating SSL certificate ===")
        status, out, err = run_ssh_command(
            "cd /root && openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes -subj '/CN=google.com'",
            client
        )
        if status != 0:
            print(f"Certificate generation error: {err}")
        else:
            print("Certificate generated.")
        
        # Clone MTProxy if not present
        print("\n=== Cloning MTProxy ===")
        status, out, err = run_ssh_command(
            "cd /root && rm -rf mtproxy-tls 2>/dev/null; git clone https://github.com/TelegramMessenger/MTProxy.git mtproxy-tls 2>&1",
            client
        )
        if status != 0:
            print(f"Clone error: {err}")
        
        # Build MTProxy
        print("\n=== Building MTProxy ===")
        status, out, err = run_ssh_command(
            "cd /root/mtproxy-tls && make 2>&1 | tail -10",
            client
        )
        if status != 0:
            print(f"Build error: {err}")
        
        # Kill existing MTProxy processes
        print("\n=== Stopping existing MTProxy ===")
        run_ssh_command("pkill -f mtproto-proxy 2>/dev/null || true", client)
        time.sleep(1)
        
        # Generate secret (32 hex chars)
        print("\n=== Generating secret ===")
        status, secret, err = run_ssh_command("openssl rand -hex 16", client)
        secret = secret.strip()
        print(f"Secret: {secret}")
        
        # Start MTProxy with TLS on port 443
        print("\n=== Starting MTProxy with TLS ===")
        cmd = f"cd /root/mtproxy-tls && nohup ./objs/bin/mtproto-proxy -p 443 -H 443 -S{secret} -C -D -d > /root/mtproxy_tls.log 2>&1 &"
        status, out, err = run_ssh_command(cmd, client)
        
        # Wait for service to start
        time.sleep(3)
        
        # Check logs
        status, logs, err = run_ssh_command("tail -30 /root/mtproxy_tls.log", client)
        print(f"Logs:\n{logs}")
        
        # Check process
        status, proc_out, err = run_ssh_command("ps aux | grep mtproto-proxy | grep -v grep", client)
        print(f"Process check: {proc_out}")
        
        # Check port
        status, netstat, err = run_ssh_command("ss -tulpn | grep :443", client)
        print(f"Port 443 status: {netstat}")
        
        # Generate Telegram link
        link = f"tg://proxy?server={HOST}&port=443&secret={secret}"
        link_alt = f"https://t.me/proxy?server={HOST}&port=443&secret={secret}"
        
        print("\n✅ MTProxy TLS setup complete!")
        print(f"\nTelegram link (tg://):")
        print(f"{link}")
        print(f"\nTelegram link (https://):")
        print(f"{link_alt}")
        print(f"\nSecret: {secret}")
        print(f"Server: {HOST}:443")
        
        # Save to file
        with open("/content/mtproxy_tls_link.txt", "w") as f:
            f.write(f"MTProxy TLS Link (tg://): {link}\n")
            f.write(f"MTProxy TLS Link (https://): {link_alt}\n")
            f.write(f"Secret: {secret}\n")
            f.write(f"Server: {HOST}:443\n")
        print("\nLink saved to /content/mtproxy_tls_link.txt")
        
        client.close()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
