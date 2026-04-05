#!/usr/bin/env python3
"""Restart MTProxy on remote server via SSH"""
import paramiko
import time
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
    if output:
        print(f"Output: {output}")
    if error:
        print(f"Error: {error}")
    return output, error, exit_status

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"Connecting to {HOST}...")
        ssh.connect(HOST, username=USER, password=PASS, timeout=30)
        print("Connected!")
        
        # 1. Stop existing MTProxy instances
        print("\n=== Stopping existing MTProxy ===")
        run_command(ssh, "pkill -f mtproto-proxy")
        time.sleep(2)
        
        # 2. Generate new secret (32 hex digits = 128 bits)
        print("\n=== Generating secret ===")
        stdin, stdout, stderr = ssh.exec_command("openssl rand -hex 16")
        secret = stdout.read().decode().strip()
        print(f"Secret: {secret}")
        
        # 3. Start MTProxy with correct parameters
        # Note: -d (lowercase) = daemonize, -D (uppercase) = domain (for TLS transport)
        print("\n=== Starting MTProxy ===")
        cmd = f"nohup /root/mtproxy/objs/bin/mtproto-proxy -p 19196 -H 19196 -S {secret} -d > /root/mtproxy.log 2>&1 &"
        run_command(ssh, cmd)
        
        # Wait for process to start
        time.sleep(5)
        
        # 4. Check if process is running
        print("\n=== Checking if process started ===")
        output, error, status = run_command(ssh, "ps aux | grep mtproto-proxy | grep -v grep")
        
        if "mtproto-proxy" in output:
            print("✓ MTProxy process is running!")
        else:
            print("✗ MTProxy process failed to start!")
            print("Checking log for errors...")
            run_command(ssh, "cat /root/mtproxy.log")
            sys.exit(1)
        
        # 5. Check if port is listening
        print("\n=== Checking if port is listening ===")
        output, error, status = run_command(ssh, "netstat -tulpn | grep LISTEN | grep 19196")
        
        if "19196" in output:
            print("✓ Port 19196 is listening!")
        else:
            print("✗ Port 19196 is NOT listening!")
            sys.exit(1)
        
        # 6. Generate Telegram link
        link = f"tg://proxy?server=91.108.237.229&port=19196&secret={secret}"
        print(f"\n=== Generated Telegram link ===")
        print(link)
        
        # 7. Save link to file
        run_command(ssh, f"echo '{link}' > /root/mtproxy_link.txt")
        
        # 8. Verify link was saved
        output, error, status = run_command(ssh, "cat /root/mtproxy_link.txt")
        
        if link in output:
            print("\n✓ SUCCESS! MTProxy is running with Fake TLS obfuscation on port 19196")
            print(f"✓ Telegram proxy link: {link}")
            print("\nTo use: Copy the link above and paste into Telegram → Settings → Proxy → Add")
        else:
            print("\n✗ WARNING: Link may not have been saved correctly")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        ssh.close()

if __name__ == "__main__":
    main()