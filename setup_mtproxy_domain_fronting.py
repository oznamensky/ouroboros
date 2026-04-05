#!/usr/bin/env python3
"""
Setup MTProxy with Domain Fronting to hide Telegram traffic.
Маскирует трафик как обычный HTTPS к google.com.
"""
import paramiko
import time

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
    print("=== MTProxy with Domain Fronting Setup ===")
    print("Маскирует трафик Telegram под обычный HTTPS к google.com")
    print()
    
    print("Connecting to VPS via SSH...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, username=USERNAME, password=PASSWORD, timeout=10)
        print("Connected successfully.\n")
        
        # Kill existing MTProxy
        print("=== Stopping existing MTProxy ===")
        run_ssh_command("pkill -f mtproto-proxy 2>/dev/null || true", client)
        time.sleep(1)
        
        # Generate secret
        print("=== Generating secret ===")
        status, secret, err = run_ssh_command("openssl rand -hex 16", client)
        secret = secret.strip()
        print(f"Secret: {secret}")
        
        # Build MTProxy with domain fronting support
        print("\n=== Building MTProxy with Domain Fronting ===")
        status, out, err = run_ssh_command(
            "cd /root/mtproxy-tls && make clean && make 2>&1 | tail -5",
            client
        )
        
        # Start MTProxy with domain fronting (masquerading as google.com)
        # Domain fronting parameters:
        # -H 443: Listen on port 443 (HTTPS)
        # -S <secret>: Secret key
        # --domain <domain>: Domain to masquerade as
        # -d: Daemon mode
        print("\n=== Starting MTProxy with Domain Fronting ===")
        
        # Use Fake TLS with domain fronting on port 443
        cmd = f"""
cd /root/mtproxy-tls && \
nohup ./objs/bin/mtproto-proxy \
  -p 443 \
  -H 443 \
  -S {secret} \
  --domain google.com \
  -f \
  -d \
  -l /root/mtproxy_fronting.log \
> /root/mtproxy_fronting_start.log 2>&1 &
"""
        status, out, err = run_ssh_command(cmd, client)
        
        # Wait for startup
        time.sleep(3)
        
        # Check process
        print("\n=== Checking MTProxy process ===")
        status, proc, err = run_ssh_command("ps aux | grep mtproto-proxy | grep -v grep", client)
        print(f"Process: {proc}")
        
        # Check logs
        print("\n=== Checking logs ===")
        status, logs, err = run_ssh_command("tail -30 /root/mtproxy_fronting.log", client)
        print(f"Logs:\n{logs}")
        
        # Check port 443
        print("\n=== Checking port 443 ===")
        status, port_info, err = run_ssh_command("ss -tulpn | grep :443", client)
        print(f"Port 443: {port_info}")
        
        # Generate Telegram links
        link_tg = f"tg://proxy?server={HOST}&port=443&secret={secret}"
        link_https = f"https://t.me/proxy?server={HOST}&port=443&secret={secret}"
        
        print("\n" + "="*60)
        print("✅ MTProxy with Domain Fronting setup complete!")
        print("="*60)
        print()
        print("Telegram links (copied to files):")
        print()
        print("1. tg:// link (for mobile Telegram):")
        print(f"   {link_tg}")
        print()
        print("2. https:// link (for desktop/web Telegram):")
        print(f"   {link_https}")
        print()
        print(f"   Secret: {secret}")
        print(f"   Server: {HOST}:443")
        print()
        print("How it works:")
        print("  - Traffic is masked as HTTPS to google.com")
        print("  - DPI sees: normal HTTPS traffic to google.com")
        print("  - Actually: Telegram traffic through MTProxy")
        print()
        print("To add to Telegram:")
        print("  Settings → Privacy & Security → Data Settings →")
        print("  Use Proxy → Add Proxy → MTProto")
        print()
        
        # Save links to files
        with open("/content/mtproxy_fronting_link.txt", "w") as f:
            f.write("MTProxy with Domain Fronting\n")
            f.write("="*40 + "\n\n")
            f.write(f"TG Link (mobile):\n{link_tg}\n\n")
            f.write(f"HTTPS Link (desktop):\n{link_https}\n\n")
            f.write(f"Secret: {secret}\n")
            f.write(f"Server: {HOST}:443\n")
            f.write(f"Domain masking: google.com\n")
        
        with open("/content/mtproxy_fronting_tg.txt", "w") as f:
            f.write(link_tg)
        
        with open("/content/mtproxy_fronting_https.txt", "w") as f:
            f.write(link_https)
        
        print("Links saved to:")
        print("  - /content/mtproxy_fronting_link.txt (full info)")
        print("  - /content/mtproxy_fronting_tg.txt (tg:// link only)")
        print("  - /content/mtproxy_fronting_https.txt (https:// link only)")
        
        client.close()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
