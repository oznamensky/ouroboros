#!/usr/bin/env python3
import paramiko
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('91.108.237.229', username='root', password='kYyA08DTsHxn1P', timeout=10)

# Check if binary exists
stdin, stdout, stderr = client.exec_command('ls -la /root/mtproxy/objs/bin/ 2>/dev/null || echo "Directory not found"')
print("Binary dir:", stdout.read().decode())

stdin, stdout, stderr = client.exec_command('find /root -name mtproto-proxy 2>/dev/null')
print("Binary found:", stdout.read().decode())

# Check MTProxy process
stdin, stdout, stderr = client.exec_command('ps aux | grep mtproto-proxy | grep -v grep')
print("Running:", stdout.read().decode())

# Check ports
stdin, stdout, stderr = client.exec_command('ss -tulpn | grep LISTEN | grep -E ":(19196|443)"')
print("Listening ports:", stdout.read().decode())

client.close()