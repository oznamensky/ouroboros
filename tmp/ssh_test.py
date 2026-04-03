#!/usr/bin/env python3
import paramiko
import sys

# SSH connection details
hostname = '91.108.237.229'
username = 'root'
password = 'kYyA08DTsHxn1P'

print(f"Connecting to {hostname}...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect(hostname, username=username, password=password, timeout=10)
    print("SSH connection successful!")
    
    # Try to get V2Ray config or status
    commands = [
        "systemctl status v2ray --no-pager 2>&1 || echo 'V2Ray not installed'",
        "ls -la /usr/local/etc/v2ray/ 2>&1 || echo 'No V2Ray config dir'",
        "netstat -tulpn | grep -E '443|10000' 2>&1 || echo 'No ports found'",
        "cat /usr/local/etc/v2ray/config.json 2>&1 || echo 'No config file'",
    ]
    
    for cmd in commands:
        print(f"\n> {cmd}")
        stdin, stdout, stderr = ssh.exec_command(cmd)
        exit_code = stdout.channel.recv_exit_status()
        output = stdout.read().decode()
        errors = stderr.read().decode()
        if output:
            print(f"Output: {output}")
        if errors and not output:
            print(f"Errors: {errors}")
            
    ssh.close()
    print("\nSSH session closed.")
    
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)