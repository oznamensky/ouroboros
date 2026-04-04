import sys
sys.path.append('/content/ouroboros_repo')
from ouroboros.tools.ssh_executor import _ssh_execute

# Setup V2Ray
uuid_cmd = """UUID=$(cat /proc/sys/kernel/random/uuid)
cat > /usr/local/etc/v2ray/config.json << EOF
{
  "inbounds": [
    {
      "port": 443,
      "protocol": "vless",
      "settings": {
        "clients": [
          {
            "id": "$UUID",
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
              "certificateFile": "/etc/ssl/certs/ssl-cert-snakeoil.pem",
              "keyFile": "/etc/ssl/private/ssl-cert-snakeoil.key"
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
}
EOF
echo "UUID=$UUID" """

result = _ssh_execute(None, '91.108.237.229', 'root', 'kYyA08DTsHxn1P', uuid_cmd)
print(result)