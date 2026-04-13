#!/bin/bash
echo "=== MTProxy Fix Script (Fixed) ==="
echo "Server: 91.108.237.229"
echo ""

# 1. Kill any existing MTProxy processes
pkill -f mtproto-proxy 2>/dev/null || echo "No running processes found"
sleep 2

# 2. Navigate to MTProxy directory
cd /root/MTProxy || { echo "MTProxy directory not found"; exit 1; }

# 3. Generate secret
SECRET=$(openssl rand -hex 32)
echo "Generated secret: $SECRET"

# 4. Create link file (FIXED ECHO COMMAND)
echo "tg://proxy?server=91.108.237.229&port=443&secret=$SECRET" > /root/mtproxy_link.txt

# 5. Download config files if missing
if [ ! -f proxy-secret ]; then
    curl -s https://core.telegram.org/getProxySecret -o proxy-secret
fi
if [ ! -f proxy-multi.conf ]; then
    curl -s https://core.telegram.org/getProxyConfig -o proxy-multi.conf
fi

# 6. Start MTProxy
# -p443: listen on port 443
# -H443: external port 443
# -S$SECRET: secret
# -Dgoogle.com: domain to use for fingerprint
# -d: daemon mode (detach)
echo "Starting MTProxy..."
./objs/bin/mtproto-proxy -p443 -H443 -S$SECRET -Dgoogle.com -d

# 7. Verify it's running
sleep 2
if pgrep -f mtproto-proxy > /dev/null; then
    echo "✓ MTProxy started successfully"
    echo "Link saved to /root/mtproxy_link.txt"
    cat /root/mtproxy_link.txt
    ss -tulpn | grep 443
else
    echo "✗ Failed to start MTProxy"
    # Try running without -d to see errors
    echo "Attempting to run in foreground to see errors:"
    ./objs/bin/mtproto-proxy -p443 -H443 -S$SECRET -Dgoogle.com
fi