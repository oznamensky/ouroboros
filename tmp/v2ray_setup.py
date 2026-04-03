import paramiko
import time

host = "91.108.237.229"
username = "root"
password = "kYyA08DTsHxn1P"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=username, password=password, timeout=15)
print("Connected to server")

# Check if V2Ray is installed
cmd = "which v2ray || ls /usr/local/bin/v2ray 2>/dev/null"
stdin, stdout, stderr = ssh.exec_command(cmd)
result = stdout.read().decode().strip()
print(f"V2Ray check: {result}")

if not result:
    print("Installing V2Ray...")
    install_cmd = "curl -L https://raw.githubusercontent.com/v2fly/install/master/install-release.sh | bash"
    stdin, stdout, stderr = ssh.exec_command(install_cmd)
    print(stdout.read().decode())
    time.sleep(5)

# Generate UUID
stdin, stdout, stderr = ssh.exec_command("cat /proc/sys/kernel/random/uuid")
uuid = stdout.read().decode().strip()
print(f"Generated UUID: {uuid}")

# Get IP address
stdin, stdout, stderr = ssh.exec_command("curl -4 ifconfig.co")
ip = stdout.read().decode().strip()
print(f"Server IP: {ip}")

# Create V2Ray config
config = f'''{{
  "inbounds": [
    {{
      "port": 443,
      "protocol": "vless",
      "settings": {{
        "clients": [
          {{
            "id": "{uuid}",
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
              "certificateFile": "/etc/ssl/certs/ssl-cert-snakeoil.pem",
              "keyFile": "/etc/ssl/private/ssl-cert-snakeoil.key"
            }}
          ]
        }}
      }}
    }}
  ],
  "outbounds": [
    {{
      "protocol": "freedom",
      "settings": {{}}
    }}
  ]
}}'''

# Write config
config_cmd = f'cat > /usr/local/etc/v2ray/config.json << EOFCONFIG\n{config}\nEOFCONFIG'
stdin, stdout, stderr = ssh.exec_command(config_cmd)
print("Config written")

# Start V2Ray
stdin, stdout, stderr = ssh.exec_command("systemctl daemon-reload && systemctl enable v2ray && systemctl restart v2ray")
print("V2Ray restarted")
time.sleep(3)

# Check status
stdin, stdout, stderr = ssh.exec_command("systemctl status v2ray --no-pager")
print("V2Ray Status:")
print(stdout.read().decode())

# Generate proxy link
link = f"vless://{uuid}@{ip}:443?encryption=none&security=tls&type=ws&path=%2Fws#V2Ray-WebSocket-TLS"
print(f"\n\nPROXY LINK: {link}\n\n")

ssh.close()