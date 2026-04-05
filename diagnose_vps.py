#!/usr/bin/env python3
"""
Diagnose VPS for anti-blocking measures.
"""
import paramiko
import time
import sys

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
        
        # Check OS
        print("=== OS Information ===")
        status, out, err = run_ssh_command("cat /etc/os-release", client)
        print(out)
        
        # Check open ports
        print("\n=== Open Ports ===")
        status, out, err = run_ssh_command("ss -tulpn | grep LISTEN", client)
        print(out)
        
        # Check if MTProxy is running
        print("\n=== MTProxy Status ===")
        status, out, err = run_ssh_command("ps aux | grep mtproto-proxy | grep -v grep", client)
        print(f"MTProxy processes: {out}")
        
        # Check if port 443 is in use
        print("\n=== Port 443 Status ===")
        status, out, err = run_ssh_command("ss -tulpn | grep :443", client)
        print(out)
        
        # Check if nginx is running
        print("\n=== Nginx Status ===")
        status, out, err = run_ssh_command("systemctl status nginx 2>&1 | head -5", client)
        print(out)
        
        # Check if we can install packages
        print("\n=== Package Manager ===")
        status, out, err = run_ssh_command("which apt || which yum || which apk", client)
        print(f"Package manager: {out}")
        
        # Check available tools
        print("\n=== Available Tools ===")
        tools = ["git", "curl", "wget", "openssl", "python3", "gcc", "make"]
        for tool in tools:
            status, out, err = run_ssh_command(f"which {tool} || echo 'not found'", client)
            print(f"{tool}: {out}")
        
        # Check if we can install V2Ray or Shadowsocks
        print("\n=== Install V2Ray? ===")
        status, out, err = run_ssh_command("curl -s https://raw.githubusercontent.com/v2fly/f2b/master/install.sh | bash", client)
        if status == 0:
            print("V2Ray installation script downloaded successfully.")
        else:
            print("V2Ray installation script failed.")
        
        print("\n=== Install Shadowsocks? ===")
        status, out, err = run_ssh_command("apt update && apt install -y shadowsocks-libev", client)
        if status == 0:
            print("Shadowsocks-libev installed successfully.")
        else:
            print("Shadowsocks-libev installation failed.")
        
        print("\n=== Check Firewall ===")
        status, out, err = run_ssh_command("ufw status", client)
        print(out)
        
        print("\n=== Check SSL Certificates ===")
        status, out, err = run_ssh_command("ls -la /etc/ssl/certs/ | head -5", client)
        print(out)
        
        print("\n=== Check Domain Fronting ===")
        # Test domain fronting by checking if we can connect to google.com via port 443
        status, out, err = run_ssh_command("timeout 5 bash -c 'echo Q | openssl s_client -connect google.com:443 -servername google.com 2>/dev/null | head -10'", client)
        print(out)
        
        print("\n=== Check if we can use Let's Encrypt ===")
        status, out, err = run_ssh_command("which certbot", client)
        print(f"Certbot: {out}")
        
        print("\n=== Summary ===")
        print("Based on the diagnosis, we can try:")
        print("1. V2Ray with WebSocket + TLS on port 443 (requires domain or self-signed cert)")
        print("2. Shadowsocks with Cloak (masks as HTTPS)")
        print("3. Another MTProxy configuration with different obfuscation")
        
        client.close()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
