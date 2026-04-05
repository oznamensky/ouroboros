#!/usr/bin/env python3
"""Check MTProxy status on remote server via SSH"""
import paramiko
import sys

# Remote server details
HOST = "91.108.237.229"
USER = "root"
PASS = "kYyA08DTsHxn1P"

def run_command(ssh, command):
    print(f"Executing: {command}")
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode()
    error = stderr.read().decode()
    return output, error, exit_status

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"Connecting to {HOST}...")
        ssh.connect(HOST, username=USER, password=PASS, timeout=30)
        print("Connected!")
        
        # 1. Check if MTProxy process is running
        print("\n=== Checking MTProxy process ===")
        output, error, status = run_command(ssh, "ps aux | grep mtproto-proxy | grep -v grep")
        print(f"Process check output: {output}")
        
        # 2. Check listening ports
        print("\n=== Checking listening ports ===")
        output, error, status = run_command(ssh, "netstat -tulpn | grep LISTEN | grep -E ':(19196|443)'")
        print(f"Port check output: {output}")
        
        # 3. Check MTProxy log
        print("\n=== Checking MTProxy log ===")
        output, error, status = run_command(ssh, "cat /root/mtproxy.log 2>/dev/null | tail -20")
        print(f"Log output: {output}")
        
        # 4. Check if link file exists
        print("\n=== Checking saved link ===")
        output, error, status = run_command(ssh, "cat /root/mtproxy_link.txt 2>/dev/null")
        print(f"Saved link: {output}")
        
        # 5. Test connection to port
        print("\n=== Testing port connection ===")
        output, error, status = run_command(ssh, "timeout 5 bash -c 'cat < /dev/null > /dev/tcp/127.0.0.1/19196' && echo 'Port 19196 open' || echo 'Port 19196 closed'")
        print(f"Port 19196 test: {output}")
        
        output, error, status = run_command(ssh, "timeout 5 bash -c 'cat < /dev/null > /dev/tcp/127.0.0.1/443' && echo 'Port 443 open' || echo 'Port 443 closed'")
        print(f"Port 443 test: {output}")
        
        # 6. Check firewall/ufw
        print("\n=== Checking firewall ===")
        output, error, status = run_command(ssh, "ufw status 2>/dev/null || iptables -L -n | grep -E ':(19196|443)' || echo 'No firewall rules found'")
        print(f"Firewall check: {output}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        ssh.close()

if __name__ == "__main__":
    main()