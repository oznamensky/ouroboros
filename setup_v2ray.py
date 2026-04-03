#!/usr/bin/env python3
import paramiko
import time

# SSH credentials
HOST = '91.108.237.229'
USER = 'root'
PASS = 'kYyA08DTsHxn1P'

def run_command(ssh, cmd):
    """Execute command and return output"""
    stdin, stdout, stderr = ssh.exec_command(cmd, get_pty=True)
    time.sleep(0.5)
    return stdout.read().decode() + stderr.read().decode()

def main():
    print("Connecting to server...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USER, password=PASS)
    
    print("Connected! Setting up V2Ray...")
    
    # Stop nginx to free port 443
    print(run_command(ssh, "systemctl stop nginx"))
    
    # Stop any existing MTProxy
    print(run_command(ssh, "systemctl stop mtproxy 2>/dev/null; pkill -9 mtproto-proxy 2>/dev/null"))
    
    # Install V2Ray
    print("Installing V2Ray...")
    print(run_command(ssh, "bash <(curl -L https://raw.githubusercontent.com/v2fly/f2b-command-tracker/master/install-release.sh) 2>/dev/null"))
    
    # Generate UUID
    uuid_output = run_command(ssh, "cat /proc/sys/kernel/random/uuid")
    UUID = uuid_output.strip()
    print(f"Generated UUID: {UUID}")
    
    # Create V2Ray config
    config = f'''{{
  "inbounds": [{{
    "port": 443,
    "protocol": "vless",
    "settings": {{
      "clients": [
        {{
          "id": "{UUID}",
          "level": 0,
          "email": "tg-proxy"
        }}
      ],
      "decryption": "none"
    }},
    "streamSettings": {{
      "network": "ws",
      "wsSettings": {{
        "path": "/ws"
      }},
      "security": "tls",
      "tlsSettings": {{
        "certificates": [
          {{
            "certificateFile": "/root/cert.pem",
            "keyFile": "/root/key.pem"
          }}
        ]
      }}
    }}
  }}],
  "outbounds": [
    {{
      "protocol": "freedom",
      "settings": {{}}
    }}
  ]
}}'''
    
    print("Creating V2Ray config...")
    run_command(ssh, f'cat > /usr/local/etc/v2ray/config.json << "EOF"\n{config}\nEOF')
    
    # Generate self-signed certificate
    print("Generating SSL certificate...")
    run_command(ssh, "openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /root/key.pem -out /root/cert.pem -subj '/CN=telegram-proxy'")
    
    # Start V2Ray
    print("Starting V2Ray...")
    print(run_command(ssh, "systemctl daemon-reload && systemctl enable v2ray && systemctl start v2ray"))
    
    # Wait and check status
    time.sleep(3)
    print("V2Ray status:")
    print(run_command(ssh, "systemctl status v2ray --no-pager"))
    
    # Generate proxy link
    proxy_link = f"vless://{UUID}@91.108.237.229:443?encryption=none&security=tls&sni=telegram-proxy&type=ws&path=/ws#Telegram-Proxy"
    
    print("\n" + "="*60)
    print("PROXY LINK READY!")
    print("="*60)
    print(f"\n{proxy_link}\n")
    print("Copy this link and add to Telegram:")
    print("Settings > Data and Storage > Use Proxy > Add Proxy > From Link")
    print("="*60)
    
    ssh.close()

if __name__ == "__main__":
    main()
