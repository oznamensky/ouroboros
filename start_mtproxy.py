#!/usr/bin/env python3
"""Search for MTProxy binary on remote server and start it"""
import paramiko
import time

HOST = "91.108.237.229"
USER = "root"
PASSWORD = "kYyA08DTsHxn1P"

def run_ssh(ssh, command):
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode().strip()
    error = stderr.read().decode().strip()
    return exit_status, output, error

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"Connecting to {HOST}...")
        ssh.connect(HOST, username=USER, password=PASSWORD, timeout=30)
        print("Connected!")
        
        # Find MTProxy binary
        print("\n=== Searching for MTProxy binary ===")
        status, output, error = run_ssh(ssh, "find /root -name 'mtproto-proxy' -type f 2>/dev/null")
        if output:
            print(f"Found: {output}")
            binary_path = output.split('\n')[0]
        else:
            print("Not found in /root, checking common locations...")
            status, output, error = run_ssh(ssh, "which mtproto-proxy 2>/dev/null || find /usr -name 'mtproto-proxy' 2>/dev/null | head -1")
            if output:
                binary_path = output
                print(f"Found: {binary_path}")
            else:
                print("MTProxy binary not found. Need to install.")
                # Install MTProxy
                print("\n=== Installing MTProxy ===")
                commands = [
                    "apt-get update -y",
                    "apt-get install -y git make gcc libevent-dev libssl-dev zlib1g-dev",
                    "cd /root && git clone https://github.com/TelegramMessenger/MTProxy.git",
                    "cd /root/MTProxy && make",
                ]
                for cmd in commands:
                    status, out, err = run_ssh(ssh, cmd)
                    if status != 0:
                        print(f"Error running: {cmd}")
                        print(f"Error: {err}")
                        return
                binary_path = "/root/MTProxy/objs/bin/mtproto-proxy"
        
        print(f"\nUsing binary: {binary_path}")
        
        # Kill existing processes
        print("\n=== Stopping existing MTProxy processes ===")
        status, output, error = run_ssh(ssh, "pkill -f mtproto-proxy 2>/dev/null; sleep 1")
        print("Stopped.")
        
        # Generate new secret
        print("\n=== Generating new secret ===")
        status, secret, error = run_ssh(ssh, "openssl rand -hex 16")
        secret = secret.strip()
        print(f"Secret: {secret}")
        
        # Start MTProxy with Fake TLS on port 443
        print("\n=== Starting MTProxy on port 443 with Fake TLS ===")
        cmd = f"""
cd $(dirname {binary_path}) && \
nohup {binary_path} \
  -p443 \
  -H443 \
  -S{secret} \
  -f \
  -d \
  -l/root/mtproxy.log \
> /dev/null 2>&1 &
"""
        status, output, error = run_ssh(ssh, cmd)
        time.sleep(3)
        
        # Verify it's running
        print("\n=== Checking if MTProxy is running ===")
        status, output, error = run_ssh(ssh, "ps aux | grep mtproto-proxy | grep -v grep")
        if output:
            print(f"Process found: {output}")
        else:
            print("Process not found! Checking logs...")
            status, output, error = run_ssh(ssh, "tail -30 /root/mtproxy.log")
            print(f"Log output:\n{output}")
            return
        
        # Check listening port
        print("\n=== Checking listening port ===")
        status, output, error = run_ssh(ssh, "ss -tulpn | grep :443")
        if output:
            print(f"Port listening: {output}")
        else:
            print("Port 443 not listening!")
            status, output, error = run_ssh(ssh, "tail -30 /root/mtproxy.log")
            print(f"Log output:\n{output}")
            return
        
        # Generate links
        link_tg = f"tg://proxy?server={HOST}&port=443&secret={secret}"
        link_https = f"https://t.me/proxy?server={HOST}&port=443&secret={secret}"
        
        print("\n" + "="*60)
        print("✅ MTProxy is running!")
        print("="*60)
        print(f"\nTelegram link (tg://):")
        print(f"{link_tg}")
        print(f"\nTelegram link (https://):")
        print(f"{link_https}")
        
        # Save link
        with open("/content/mtproxy_link.txt", "w") as f:
            f.write(link_tg)
        print(f"\nLink saved to /content/mtproxy_link.txt")
        
        # Also save to server
        run_ssh(ssh, f"echo '{link_tg}' > /root/mtproxy_link.txt")
        
        ssh.close()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()