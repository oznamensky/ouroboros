#!/bin/bash
# MTProxy Final Fix Script
# Diagnoses and fixes MTProxy issues on the server

echo "=== MTProxy Diagnostic & Fix ==="
echo "Server: 91.108.237.229"
echo "Time: $(date)"
echo ""

# 1. Check disk space (critical issue)
echo "--- 1. Disk Space Check ---"
df -h / | grep -v Filesystem
echo ""

# 2. Check what's using port 443
echo "--- 2. Port 443 Status ---"
ss -tulpn | grep :443 || echo "Port 443 is free"
echo ""

# 3. Check existing MTProxy processes
echo "--- 3. Existing MTProxy Processes ---"
ps aux | grep mtproto-proxy | grep -v grep || echo "No MTProxy processes running"
echo ""

# 4. Check log file
echo "--- 4. Log File Content ---"
if [ -f /root/mtproxy.log ]; then
    tail -30 /root/mtproxy.log
else
    echo "No log file found"
fi
echo ""

# 5. Test MTProxy binary directly
echo "--- 5. Testing MTProxy Binary ---"
cd /root/MTProxy 2>/dev/null || cd /root/mtproxy 2>/dev/null
if [ -f ./objs/bin/mtproto-proxy ]; then
    echo "Binary exists, testing with minimal parameters..."
    ./objs/bin/mtproto-proxy --help 2>&1 | head -20
else
    echo "Binary not found, need to compile"
fi
echo ""

# 6. Generate proper secret and test
echo "--- 6. Generating Test Secret ---"
SECRET=$(openssl rand -hex 16)
echo "Secret: $SECRET"
echo "Length: ${#SECRET} characters (should be 32)"
echo ""

# 7. Test run without daemon mode
echo "--- 7. Test Run (non-daemon, will timeout after 10 seconds) ---"
timeout 10 ./objs/bin/mtproto-proxy -p443 -H443 -S$SECRET -Dgoogle.com 2>&1 &
TEST_PID=$!
sleep 2
if ps -p $TEST_PID > /dev/null; then
    echo "✓ MTProxy started successfully (PID: $TEST_PID)"
    kill $TEST_PID 2>/dev/null
else
    echo "✗ MTProxy failed to start"
    echo "Last 10 lines of log:"
    tail -10 /root/mtproxy.log 2>/dev/null || echo "No log available"
fi
echo ""

# 8. Try alternative port (19196)
echo "--- 8. Testing Alternative Port (19196) ---"
timeout 10 ./objs/bin/mtproto-proxy -p19196 -H19196 -S$SECRET -Dgoogle.com 2>&1 &
TEST_PID=$!
sleep 2
if ps -p $TEST_PID > /dev/null; then
    echo "✓ MTProxy started on port 19196 (PID: $TEST_PID)"
    kill $TEST_PID 2>/dev/null
    echo "tg://proxy?server=91.108.237.229&port=19196&secret=$SECRET"
else
    echo "✗ MTProxy failed on port 19196"
fi
echo ""

# 9. Check if proxy-secret and proxy-multi.conf exist
echo "--- 9. Configuration Files ---"
ls -la proxy-secret proxy-multi.conf 2>/dev/null || echo "Config files missing"
echo ""

echo "=== Diagnosis Complete ==="
echo "Check output above for errors. If MTProxy starts successfully,"
echo "the Telegram proxy link will be shown."