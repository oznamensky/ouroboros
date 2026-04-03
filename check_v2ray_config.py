#!/usr/bin/env python3
"""Check actual V2Ray configuration on server"""

import paramiko

def check_config():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect('91.108.237.229', username='root', password='kYyA08DTsHxn1P', timeout=30)
        print("Connected to server!")
        
        # Check V2Ray config
        commands = [
            "cat /usr/local/etc/v2ray/config.json 2>/dev/null || echo 'Config not found'",
            "cat /etc/v2ray/v2ray.crt 2>/dev/null | head -5 || echo 'No cert found'",
            "cat /root/v2ray_uuid.txt 2>/dev/null || echo 'No UUID file'",
            "netstat -tulpn | grep -E '(:443|:10086)'",
            "curl -k https://localhost:443/ws 2>&1 | head -20",
        ]
        
        for cmd in commands:
            print(f"\n>>> {cmd}")
            stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
            exit_code = stdout.channel.recv_exit_status()
            out = stdout.read().decode()
            err = stderr.read().decode()
            print(f"Output:\n{out}")
            if err:
                print(f"Error: {err}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    check_config()