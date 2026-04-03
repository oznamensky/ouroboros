#!/usr/bin/env python3
"""Direct SSH setup for V2Ray + WebSocket + TLS"""

import paramiko
import time

def execute_ssh_commands():
    # SSH connection
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect('91.108.237.229', username='root', password='kYyA08DTsHxn1P', timeout=30)
        print("Connected to server!")
        
        # Commands to run
        commands = [
            # Stop conflicting services
            "systemctl stop nginx 2>/dev/null || true",
            "systemctl stop mtproxy 2>/dev/null || true",
            "pkill mtproto-proxy 2>/dev/null || true",
            
            # Install V2Ray
            "bash <(curl -L https://raw.githubusercontent.com/v2fly/installer/master/install-release.sh) 2>&1",
            
            # Generate UUID
            "UUID=$(cat /proc/sys/kernel/random/uuid) && echo $UUID > /root/v2ray_uuid.txt && cat /root/v2ray_uuid.txt",
        ]
        
        for cmd in commands:
            print(f"\n>>> Executing: {cmd[:100]}...")
            stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
            exit_code = stdout.channel.recv_exit_status()
            out = stdout.read().decode()
            err = stderr.read().decode()
            if out:
                print(f"Output: {out[:500]}")
            if err:
                print(f"Error: {err[:500]}")
            if exit_code != 0:
                print(f"Exit code: {exit_code}")
        
        # Get UUID
        stdin, stdout, stderr = ssh.exec_command("cat /root/v2ray_uuid.txt 2>/dev/null || echo 'NOT_FOUND'")
        uuid = stdout.read().decode().strip()
        print(f"\nUUID: {uuid}")
        
        # Create V2Ray config
        config = f'''{{
  "inbounds": [{{
    "port": 443,
    "protocol": "vless",
    "settings": {{
      "clients": [{{
        "id": "{uuid}",
        "level": 0
      }}],
      "decryption": "none"
    }},
    "streamSettings": {{
      "network": "ws",
      "security": "tls",
      "tlsSettings": {{
        "certificates": [{{
          "certificateFile": "/etc/v2ray/v2ray.crt",
          "keyFile": "/etc/v2ray/v2ray.key"
        }}]
      }},
      "wsSettings": {{
        "path": "/ws"
      }}
    }}
  }}],
  "outbounds": [{{
    "protocol": "freedom",
    "settings": {{}}
  }}]
}}'''
        
        # Write config
        ssh.exec_command(f'echo \'{config}\' > /usr/local/etc/v2ray/config.json')
        
        # Generate self-signed cert
        ssh.exec_command('mkdir -p /etc/v2ray')
        ssh.exec_command('openssl req -x509 -newkey rsa:4096 -keyout /etc/v2ray/v2ray.key -out /etc/v2ray/v2ray.crt -days 365 -nodes -subj "/CN=telegram.org" 2>/dev/null')
        
        # Start V2Ray
        ssh.exec_command('systemctl enable v2ray && systemctl start v2ray')
        time.sleep(3)
        
        # Check status
        stdin, stdout, stderr = ssh.exec_command('systemctl status v2ray --no-pager')
        print(f"\nV2Ray Status:\n{stdout.read().decode()[:1000]}")
        
        # Get the proxy link
        link = f"vless://{uuid}@91.108.237.229:443?encryption=none&security=tls&sni=telegram.org&type=ws&path=%2Fws#V2Ray-Telegram"
        print(f"\n{'='*60}")
        print(f"PROXY LINK (copy to Telegram):")
        print(f"{'='*60}")
        print(link)
        print(f"{'='*60}")
        
        return link
        
    except Exception as e:
        print(f"Error: {e}")
        return None
    finally:
        ssh.close()

if __name__ == "__main__":
    execute_ssh_commands()
