#!/usr/bin/env python3
"""Install MTProxy on remote server via SSH"""
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
        
        # 1. Install dependencies
        print("Installing dependencies...")
        run_command(ssh, "apt-get update && apt-get install -y libssl-dev zlib1g-dev git make")
        
        # 2. Clone MTProxy
        print("Cloning MTProxy...")
        run_command(ssh, "rm -rf /root/mtproxy")
        run_command(ssh, "git clone https://github.com/TelegramMessenger/MTProxy.git /root/mtproxy")
        
        # 3. Build
        print("Building MTProxy...")
        run_command(ssh, "cd /root/mtproxy && make")
        
        # 4. Generate secret (32 hex digits)
        print("Generating secret...")
        stdin, stdout, stderr = ssh.exec_command("openssl rand -hex 16")
        secret = stdout.read().decode().strip()
        print(f"Secret: {secret}")
        
        # 5. Stop existing instances
        print("Stopping existing MTProxy...")
        run_command(ssh, "pkill -f mtproto-proxy")
        
        # 6. Start MTProxy
        print("Starting MTProxy...")
        # Using nohup to keep it running
        cmd = f"nohup /root/mtproxy/objs/bin/mtproto-proxy -p 19196 -H 19196 -S {secret} -f -D > /root/mtproxy.log 2>&1 &"
        run_command(ssh, cmd)
        
        # Wait a bit
        time.sleep(3)
        
        # 7. Check status
        print("Checking status...")
        run_command(ssh, "ps aux | grep mtproto-proxy")
        
        # 8. Generate Telegram link
        link = f"tg://proxy?server=91.108.237.229&port=19196&secret={secret}"
        print(f"Generated link: {link}")
        
        # 9. Save link to file
        run_command(ssh, f"echo '{link}' > /root/mtproxy_link.txt")
        
        # 10. Read back the link via SFTP to verify
        sftp = ssh.open_sftp()
        remote_file = sftp.open('/root/mtproxy_link.txt', 'r')
        saved_link = remote_file.read().decode().strip()
        remote_file.close()
        sftp.close()
        
        print(f"Link saved on server: {saved_link}")
        
        if saved_link == link:
            print("SUCCESS! MTProxy is running.")
            print(f"Your Telegram proxy link: {link}")
            # Save link locally for reference
            with open("/content/mtproxy_link.txt", "w") as f:
                f.write(link)
        else:
            print("WARNING: Link mismatch or file not saved correctly.")
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        ssh.close()

if __name__ == "__main__":
    main()