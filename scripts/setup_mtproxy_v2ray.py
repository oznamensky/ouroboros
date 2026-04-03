#!/usr/bin/env python3
"""
MTProxy + V2Ray/VLESS совместная установка
MTProxy: порт 443 (для Telegram)
VLESS: порт 4443 (WebSocket + TLS для V2Ray клиентов)
"""

import paramiko
import sys

# SSH Credentials
HOST = "91.108.237.229"
USER = "root"
PASSWORD = "kYyA08DTsHxn1P"  # TODO: Remove after password change

def execute_command(ssh, command):
    """Execute command on remote server"""
    stdin, stdout, stderr = ssh.exec_command(command, get_pty=True)
    exit_code = stdout.channel.recv_exit_status()
    output = stdout.read().decode()
    errors = stderr.read().decode()
    return exit_code, output + errors

def main():
    print(f"Connecting to {HOST}...")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(HOST, username=USER, password=PASSWORD)
        print("✓ Connected successfully\n")
        
        # 1. Install dependencies
        print("Installing dependencies...")
        commands = [
            "apt-get update",
            "apt-get install -y wget curl git build-essential libssl-dev libevent-dev libjansson-dev libreadline-dev",
        ]
        
        for cmd in commands:
            print(f"  Running: {cmd}")
            code, out = execute_command(ssh, cmd)
            if code != 0:
                print(f"  Warning: {out}")
        
        # 2. Install MTProxy
        print("\nInstalling MTProxy...")
        commands = [
            "cd /root && git clone https://github.com/TelegramMessenger/MTProxy.git",
            "cd /root/MTProxy && make",
        ]
        
        for cmd in commands:
            print(f"  Running: {cmd}")
            code, out = execute_command(ssh, cmd)
            print(f"  Output: {out}")
        
        # 3. Generate MTProxy secret
        print("\nGenerating MTProxy secret...")
        code, secret = execute_command(ssh, "openssl rand -hex 16")
        secret = secret.strip()
        print(f"  Secret: {secret}")
        
        # 4. Create MTProxy systemd service
        print("\nCreating MTProxy service...")
        mtproxy_service = """[Unit]
Description=MTProxy Telegram Proxy
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/MTProxy
ExecStart=/root/MTProxy/objs/bin/mtproto-proxy -p 19196 -H 443 -S {secret} -D github.com -l /var/log/mtproxy.log
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
""".format(secret=secret)
        
        # Write service file
        execute_command(ssh, f"cat > /etc/systemd/system/mtproxy.service << 'EOF'\n{mtproxy_service}\nEOF")
        
        # 5. Install V2Ray
        print("\nInstalling V2Ray...")
        commands = [
            "bash <(curl -L https://raw.githubusercontent.com/v2fly/f2b-command-tracker/master/install-release.sh) 2>/dev/null",
        ]
        
        for cmd in commands:
            print(f"  Running: {cmd}")
            code, out = execute_command(ssh, cmd)
            print(f"  Output: {out}")
        
        # 6. Generate UUID for VLESS
        print("\nGenerating VLESS UUID...")
        code, uuid = execute_command(ssh, "cat /proc/sys/kernel/random/uuid")
        uuid = uuid.strip()
        print(f"  UUID: {uuid}")
        
        # 7. Create V2Ray config (VLESS on port 4443 with WebSocket + TLS)
        print("\nCreating V2Ray config...")
        v2ray_config = """{
  "inbounds": [
    {
      "port": 4443,
      "protocol": "vless",
      "settings": {
        "clients": [
          {
            "id": "UUID_PLACEHOLDER",
            "level": 0,
            "email": "tg-proxy"
          }
        ],
        "decryption": "none"
      },
      "streamSettings": {
        "network": "ws",
        "wsSettings": {
          "path": "/ws"
        },
        "security": "tls",
        "tlsSettings": {
          "certificates": [
            {
              "certificateFile": "/etc/v2ray/v2ray.crt",
              "keyFile": "/etc/v2ray/v2ray.key"
            }
          ]
        }
      }
    }
  ],
  "outbounds": [
    {
      "protocol": "freedom",
      "settings": {}
    }
  ]
}""".replace("UUID_PLACEHOLDER", uuid)
        
        execute_command(ssh, f"cat > /usr/local/etc/v2ray/config.json << 'EOF'\n{v2ray_config}\nEOF")
        
        # 8. Generate self-signed TLS certificate
        print("\nGenerating TLS certificate...")
        commands = [
            "mkdir -p /etc/v2ray",
            "openssl req -x509 -newkey rsa:4096 -keyout /etc/v2ray/v2ray.key -out /etc/v2ray/v2ray.crt -days 365 -nodes -subj '/CN=91.108.237.229'",
        ]
        
        for cmd in commands:
            print(f"  Running: {cmd}")
            code, out = execute_command(ssh, cmd)
            print(f"  Output: {out}")
        
        # 9. Start services
        print("\nStarting services...")
        commands = [
            "systemctl daemon-reload",
            "systemctl enable mtproxy",
            "systemctl enable v2ray",
            "systemctl start mtproxy",
            "systemctl start v2ray",
        ]
        
        for cmd in commands:
            print(f"  Running: {cmd}")
            code, out = execute_command(ssh, cmd)
            print(f"  Output: {out}")
        
        # 10. Check status
        print("\nChecking status...")
        code, out = execute_command(ssh, "systemctl status mtproxy --no-pager")
        print(f"MTProxy status:\n{out}")
        
        code, out = execute_command(ssh, "systemctl status v2ray --no-pager")
        print(f"V2Ray status:\n{out}")
        
        # 11. Check ports
        print("\nChecking ports...")
        code, out = execute_command(ssh, "netstat -tulpn | grep -E '(:443|:4443|:19196)'")
        print(f"Ports:\n{out}")
        
        # 12. Display final links
        print("\n" + "="*60)
        print("✅ SETUP COMPLETE!")
        print("="*60)
        print()
        print("📱 TELEGRAM MTProxy (порт 443):")
        print(f"   tg://proxy?server={HOST}&port=443&secret={secret}")
        print(f"   https://t.me/proxy?server={HOST}&port=443&secret={secret}")
        print()
        print("🌐 VLESS + WebSocket + TLS (порт 4443):")
        print(f"   vless://{uuid}@{HOST}:4443?path=/ws&security=tls&type=ws#V2Ray-VLESS")
        print()
        print("📊 Проверка статуса:")
        print(f"   systemctl status mtproxy")
        print(f"   systemctl status v2ray")
        print(f"   netstat -tulpn | grep -E '(:443|:4443|:19196)'")
        print()
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    finally:
        ssh.close()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
