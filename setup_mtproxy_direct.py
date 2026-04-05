#!/usr/bin/env python3
"""
Direct MTProxy setup via SSH using Paramiko.
No owner intervention required.
"""
import paramiko
import time
import sys
import random

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
        
        # Clone MTProxy repo (telegramdesktop version)
        print("Cloning MTProxy repository...")
        status, out, err = run_ssh_command("cd /root && rm -rf mtproxy MTProxy && git clone https://github.com/telegramdesktop/mtproxy.git mtproxy", client)
        if status != 0:
            print(f"Clone error: {err}")
            sys.exit(1)
        print(f"Clone output: {out}")
        
        # Build MTProxy
        print("Building MTProxy...")
        status, out, err = run_ssh_command("cd /root/mtproxy && make", client)
        if status != 0:
            print(f"Build error: {err}")
            print(f"Build output: {out}")
            sys.exit(1)
        print(f"Build output: {out}")
        
        # Stop nginx if running (port 443 conflict)
        print("Stopping nginx...")
        run_ssh_command("systemctl stop nginx 2>/dev/null || true", client)
        
        # Kill any existing MTProxy processes
        print("Killing existing MTProxy processes...")
        run_ssh_command("pkill -f mtproto-proxy 2>/dev/null || true", client)
        time.sleep(1)
        
        # Generate secret (32 hex chars = 128-bit)
        print("Generating secret...")
        status, secret, err = run_ssh_command("openssl rand -hex 32", client)
        if status != 0:
            print(f"Secret generation error: {err}")
            sys.exit(1)
        secret = secret.strip()
        print(f"Secret: {secret}")
        
        # Get a random working domain (non-telegram)
        fake_domains = ["google.com", "cloudflare.com", "github.com", "yandex.ru", "ok.ru", "mail.ru", "vk.com", "mozilla.org"]
        random_domain = random.choice(fake_domains)
        print(f"Using fake domain: {random_domain}")
        
        # Start MTProxy with Fake TLS on port 443
        print("Starting MTProxy...")
        # Correct syntax: -p443 -H443 -S<secret> -D<domain> -d (daemonize)
        cmd = f"cd /root/mtproxy && nohup ./objs/bin/mtproto-proxy -p443 -H443 -S{secret} -D{random_domain} -d > /root/mtproxy.log 2>&1 &"
        status, out, err = run_ssh_command(cmd, client)
        if status != 0:
            print(f"Start error: {err}")
            print(f"Start output: {out}")
        
        # Wait for service to bind
        print("Waiting for MTProxy to start...")
        time.sleep(3)
        
        # Check logs
        status, logs, err = run_ssh_command("tail -30 /root/mtproxy.log", client)
        print(f"Logs:\n{logs}")
        
        # Check if process is running
        status, proc_out, err = run_ssh_command("ps aux | grep mtproto-proxy | grep -v grep", client)
        print(f"Process check: {proc_out}")
        
        if not proc_out.strip():
            print("Process not found, checking full log...")
            status, err_log, _ = run_ssh_command("cat /root/mtproxy.log", client)
            print(f"Full log:\n{err_log}")
            sys.exit(1)
        
        # Check port binding
        status, netstat, err = run_ssh_command("ss -tulpn | grep 443", client)
        print(f"Port 443 status: {netstat}")
        
        # Generate Telegram link
        link = f"tg://proxy?server={HOST}&port=443&secret={secret}"
        link_alt = f"https://t.me/proxy?server={HOST}&port=443&secret={secret}"
        
        print("\n✅ MTProxy setup complete!")
        print(f"\nTelegram link (tg://):")
        print(f"{link}")
        print(f"\nTelegram link (https://):")
        print(f"{link_alt}")
        print(f"\nSecret: {secret}")
        print(f"Server: {HOST}:443")
        print(f"Domain: {random_domain}")
        
        # Save to file for owner
        with open("/content/mtproxy_link.txt", "w") as f:
            f.write(f"MTProxy Link (tg://): {link}\n")
            f.write(f"MTProxy Link (https://): {link_alt}\n")
            f.write(f"Secret: {secret}\n")
            f.write(f"Server: {HOST}:443\n")
        print("\nLink saved to /content/mtproxy_link.txt")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        client.close()

if __name__ == "__main__":
    main()