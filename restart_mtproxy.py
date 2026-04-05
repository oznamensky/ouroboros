#!/usr/bin/env python3
"""Restart MTProxy on remote server via SSH with correct Telegram config"""
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
        
        # 2. Generate new secret (16 bytes = 32 hex digits)
        print("\n=== Generating secret ===")
        stdin, stdout, stderr = ssh.exec_command("head -c 16 /dev/urandom | xxd -ps")
        secret = stdout.read().decode().strip()
        print(f"Secret: {secret}")
        
        # 3. Download Telegram proxy secret and config
        print("\n=== Downloading Telegram proxy files ===")
        run_command(ssh, "curl -s https://core.telegram.org/getProxySecret -o /root/proxy-secret")
        run_command(ssh, "curl -s https://core.telegram.org/getProxyConfig -o /root/proxy-multi.conf")
        
        # 4. Start MTProxy with setsid to avoid PID assertion error
        print("\n=== Starting MTProxy ===")
        cmd = f"cd /root/MTProxy && setsid ./objs/bin/mtproto-proxy -u nobody -p 19196 -H 19196 -S {secret} --aes-pwd /root/proxy-secret /root/proxy-multi.conf > /root/mtproxy.log 2>&1 &"
        run_command(ssh, cmd)
        time.sleep(5)
        
        # 5. Check if process is running
        print("\n=== Checking if process started ===")
        output, error, status = run_command(ssh, "ps aux | grep mtproto-proxy | grep -v grep")
        
        if "mtproto-proxy" in output:
            print("✓ MTProxy process is running!")
            port = 19196
        else:
            print("✗ MTProxy process failed to start!")
            print("Checking log for errors...")
            run_command(ssh, "cat /root/mtproxy.log")
            
            # Try port 443
            print("\n=== Trying port 443 (standard HTTPS) ===")
            run_command(ssh, "pkill -f mtproto-proxy")
            time.sleep(2)
            
            cmd = f"cd /root/MTProxy && setsid ./objs/bin/mtproto-proxy -u nobody -p 443 -H 443 -S {secret} --aes-pwd /root/proxy-secret /root/proxy-multi.conf > /root/mtproxy.log 2>&1 &"
            run_command(ssh, cmd)
            time.sleep(5)
            
            output, error, status = run_command(ssh, "ps aux | grep mtproto-proxy | grep -v grep")
            if "mtproto-proxy" in output:
                print("✓ MTProxy process is running on port 443!")
                port = 443
            else:
                print("✗ Still failed")
                port = 19196
        
        # 6. Generate Telegram link
        link = f"tg://proxy?server=91.108.237.229&port={port}&secret={secret}"
        print(f"\n=== Generated Telegram link ===")
        print(link)
        
        # 7. Save link to file
        run_command(ssh, f"echo '{link}' > /root/mtproxy_link.txt")
        
        print(f"\n✓ Telegram proxy link: {link}")
        print("\nTo use: Copy the link above and paste into Telegram → Settings → Proxy → Add")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        ssh.close()

if __name__ == "__main__":
    main()