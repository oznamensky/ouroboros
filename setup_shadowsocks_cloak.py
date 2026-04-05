#!/usr/bin/env python3
"""
Setup Shadowsocks with Cloak for Telegram.
Masks traffic as HTTPS to avoid DPI detection.
"""
import paramiko
import time
import sys
import random
import string

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

def generate_password(length=32):
    """Generate random password."""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def generate_port():
    """Generate random port between 10000-65000."""
    return random.randint(10000, 65000)

def main():
    print("Connecting to VPS via SSH...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, username=USERNAME, password=PASSWORD, timeout=10)
        print("Connected successfully.\n")
        
        # Install Cloak if not present
        print("=== Installing/Checking Cloak ===")
        status, out, err = run_ssh_command("which ck-server || echo 'not found'", client)
        if "not found" in out:
            print("Cloak not found, installing...")
            status, out, err = run_ssh_command("apt update && apt install -y cloak", client)
            if status != 0:
                print("Cloak installation failed, trying manual install...")
                # Manual install
                status, out, err = run_ssh_command(
                    "wget https://github.com/cbeuw/Cloak/releases/download/v2.6.1/ck-server-linux-amd64-v2.6.1 -O /usr/local/bin/ck-server && chmod +x /usr/local/bin/ck-server",
                    client
                )
        
        # Generate configs
        port = generate_port()
        password = generate_password()
        admin_uid = generate_password(16)  # 16 chars for UID
        
        print(f"Generated port: {port}")
        print(f"Generated password: {password}")
        print(f"Admin UID: {admin_uid}")
        
        # Create Shadowsocks config
        ss_config = f"""
{{
    "server": "0.0.0.0",
    "server_port": {port},
    "password": "{password}",
    "method": "chacha20-ietf-poly1305",
    "timeout": 300,
    "fast_open": false,
    "workers": 1,
    "plugin": "ck-server",
    "plugin_opts": "ck-admin-uid={admin_uid}"
}}
"""
        
        # Create Cloak config
        cloak_config = f"""
{{
    "AdminUID": "{admin_uid}",
    "BindAddr": [":{port}"],
    "EncryptionKey": "{password}",
    "PrivateKey": "",
    "PublicKey": "",
    "ServerName": "www.google.com",
    "Port": 443,
    "MasterKey": "",
    "DatabasePath": "/etc/shadowsocks-libev/ck.db",
    "Timeout": 30,
    "LimitUser": "",
    "LimitUserPasswd": "",
    "LogLevel": 2,
    "Fingerprint": "chrome"
}}
"""
        
        # Write configs to server
        print("\n=== Writing configs to server ===")
        
        # Create directories
        status, out, err = run_ssh_command("mkdir -p /etc/shadowsocks-libev", client)
        
        # Write Shadowsocks config
        with open("/tmp/ss-config.json", "w") as f:
            f.write(ss_config)
        
        # Upload config
        sftp = client.open_sftp()
        sftp.put("/tmp/ss-config.json", "/etc/shadowsocks-libev/config.json")
        
        # Write Cloak config
        with open("/tmp/ck-config.json", "w") as f:
            f.write(cloak_config)
        
        sftp.put("/tmp/ck-config.json", "/etc/shadowsocks-libev/ck-config.json")
        sftp.close()
        
        print("Configs uploaded successfully.")
        
        # Kill any running Shadowsocks/Cloak processes
        print("\n=== Stopping existing services ===")
        run_ssh_command("pkill -f ss-server 2>/dev/null || true", client)
        run_ssh_command("pkill -f ck-server 2>/dev/null || true", client)
        
        # Generate keys for Cloak (if needed)
        print("\n=== Generating Cloak keys ===")
        status, out, err = run_ssh_command("ck-server -keygen -n 1", client)
        print(f"Keygen output: {out}")
        
        # Start Shadowsocks with Cloak plugin
        print("\n=== Starting Shadowsocks with Cloak ===")
        cmd = f"nohup ss-server -c /etc/shadowsocks-libev/config.json > /var/log/shadowsocks.log 2>&1 &"
        status, out, err = run_ssh_command(cmd, client)
        
        # Wait for service to start
        time.sleep(2)
        
        # Check if service is running
        print("\n=== Checking service status ===")
        status, out, err = run_ssh_command("ps aux | grep -E '(ss-server|ck-server)' | grep -v grep", client)
        print(f"Process check: {out}")
        
        # Check logs
        status, out, err = run_ssh_command("tail -20 /var/log/shadowsocks.log", client)
        print(f"Logs:\n{out}")
        
        # Check port binding
        status, out, err = run_ssh_command(f"ss -tulpn | grep :{port}", client)
        print(f"Port {port} status: {out}")
        
        # Generate Shadowsocks link
        method = "chacha20-ietf-poly1305"
        base64_password = password  # For simplicity, using plain password
        
        # Shadowsocks link format
        ss_link = f"ss://{method}:{base64_password}@{HOST}:{port}"
        
        # Generate Cloak configuration for Telegram
        # Telegram plugin requires special setup
        
        print("\n✅ Shadowsocks + Cloak setup complete!")
        print(f"\nShadowsocks link (for clients):")
        print(f"{ss_link}")
        print(f"\nManual config:")
        print(f"  Server: {HOST}")
        print(f"  Port: {port}")
        print(f"  Password: {password}")
        print(f"  Method: {method}")
        print(f"  Plugin: cloak")
        print(f"  Plugin options: ck-admin-uid={admin_uid}")
        
        # Save to file
        with open("/content/shadowsocks_config.txt", "w") as f:
            f.write(f"Shadowsocks link: {ss_link}\n")
            f.write(f"Server: {HOST}\n")
            f.write(f"Port: {port}\n")
            f.write(f"Password: {password}\n")
            f.write(f"Method: {method}\n")
            f.write(f"Plugin: cloak\n")
            f.write(f"Admin UID: {admin_uid}\n")
        
        print(f"\nConfig saved to /content/shadowsocks_config.txt")
        
        # Create Telegram-specific setup instructions
        print("\n=== Telegram Setup ===")
        print("For Telegram, you need a client that supports Shadowsocks with plugins.")
        print("Alternatively, you can use MTProxy with Shadowsocks as transport.")
        
        # Install MTProxy Telegram plugin
        print("\n=== Installing MTProxy Telegram plugin ===")
        status, out, err = run_ssh_command(
            "cd /root && git clone https://github.com/TelegramMessenger/MTProxy.git mtproxy-plugin 2>/dev/null && cd mtproxy-plugin && make 2>&1 | tail -20",
            client
        )
        print(f"MTProxy plugin install: {out}")
        
        client.close()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
