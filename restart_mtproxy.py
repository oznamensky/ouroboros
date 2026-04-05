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
        
        # 1. Clone MTProxy if not exists
        print("\n=== Cloning MTProxy repository ===")
        run_command(ssh, "cd /root && git clone https://github.com/TelegramMessenger/MTProxy.git")
        
        # 2. Build MTProxy
        print("\n=== Building MTProxy ===")
        run_command(ssh, "cd /root/MTProxy && make")
        
        # 3. Stop existing MTProxy instances
        print("\n=== Stopping existing MTProxy ===")
        run_command(ssh, "pkill -f mtproto-proxy")
        time.sleep(2)
        
        # 4. Generate new secret (16 bytes = 32 hex digits)
        print("\n=== Generating secret ===")
        stdin, stdout, stderr = ssh.exec_command("head -c 16 /dev/urandom | xxd -ps")
        secret = stdout.read().decode().strip()
        print(f"Secret: {secret}")
        
        # 5. Download Telegram proxy secret and config
        print("\n=== Downloading Telegram proxy files ===")
        run_command(ssh, "cd /root/MTProxy && curl -s https://core.telegram.org/getProxySecret -o proxy-secret")
        run_command(ssh, "cd /root/MTProxy && curl -s https://core.telegram.org/getProxyConfig -o proxy-multi.conf")
        
        # 6. Start MTProxy with correct parameters
        print("\n=== Starting MTProxy ===")
        cmd = f"cd /root/MTProxy && nohup ./objs/bin/mtproto-proxy -u nobody -p 19196 -H 19196 -S {secret} --aes-pwd proxy-secret proxy-multi.conf -M 1 > /root/mtproxy.log 2>&1 &"
        run_command(ssh, cmd)
        
        # Wait for process to start
        time.sleep(5)
        
        # 7. Check if process is running
        print("\n=== Checking if process started ===")
        output, error, status = run_command(ssh, "ps aux | grep mtproto-proxy | grep -v grep")
        
        if "mtproto-proxy" in output:
            print("✓ MTProxy process is running!")
        else:
            print("✗ MTProxy process failed to start!")
            print("Checking log for errors...")
            run_command(ssh, "cat /root/mtproxy.log")
        
        # 8. Check if port is listening
        print("\n=== Checking if port is listening ===")
        output, error, status = run_command(ssh, "netstat -tulpn | grep LISTEN | grep 19196")
        
        if "19196" in output:
            print("✓ Port 19196 is listening!")
        else:
            print("✗ Port 19196 is NOT listening!")
        
        # 9. Generate Telegram link (no Fake TLS, just direct MTProto)
        link = f"tg://proxy?server=91.108.237.229&port=19196&secret={secret}"
        print(f"\n=== Generated Telegram link ===")
        print(link)
        
        # 10. Save link to file
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