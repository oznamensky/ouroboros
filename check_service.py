#!/usr/bin/env python3
import paramiko
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('91.108.237.229', username='root', password='kYyA08DTsHxn1P', timeout=10)

# Check systemd service
stdin, stdout, stderr = client.exec_command('systemctl status mtproxy 2>&1')
print("Service status:", stdout.read().decode())

# Check service file
stdin, stdout, stderr = client.exec_command('cat /etc/systemd/system/mtproxy.service 2>/dev/null || echo "Service file not found"')
print("Service file:", stdout.read().decode())

# Check if any mtproto-proxy process is running
stdin, stdout, stderr = client.exec_command('ps aux | grep mtproto-proxy')
print("All mtproto-proxy processes:", stdout.read().decode())

# Try to run the binary directly with correct parameters
stdin, stdout, stderr = client.exec_command('cd /root/mtproxy && ./objs/bin/mtproto-proxy --help 2>&1 | head -30')
print("Binary help:", stdout.read().decode())

client.close()