#!/usr/bin/env python3
"""
Setup MTProxy with correct 32-hex-digit secret and Fake TLS.
"""
import paramiko
import re

HOST = "91.108.237.229"
USERNAME = "root"
PASSWORD = "kYyA08DTsHxn1P"

def run_ssh_command(client, command):
    stdin, stdout, stderr = client.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode().strip()
    error = stderr.read().decode().strip()
    return exit_status, output, error

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HOST, username=USERNAME, password=PASSWORD, timeout=10)
        
        print("=== Generating 32-hex-digit secret ===")
        # Generate 32 hex digits (128 bits)
        status, secret, err = run_ssh_command(client, "openssl rand -hex 16")
        print(f"Secret: {secret}")
        
        print("\n=== Stopping any existing MTProxy ===")
        status, out, err = run_ssh_command(client, "pkill -f mtproto-proxy 2>/dev/null || true")
        
        print("\n=== Starting MTProxy with correct parameters ===")
        # Key: use 32 hex digits, correct flags
        cmd = f"cd /root/mtproxy && nohup ./objs/bin/mtproto-proxy -p 443 -H 443 -S {secret} -D google.com -d > /root/mtproxy.log 2>&1 &"
        status, out, err = run_ssh_command(client, cmd)
        print(f"Start status: {status}")
        
        print("\n=== Waiting for service to start ===")
        import time
        time.sleep(3)
        
        print("\n=== Checking if running ===")
        status, procs, err = run_ssh_command(client, "ps aux | grep mtproto-proxy | grep -v grep")
        print(f"Process status: {status}")
        print(f"Processes:\n{procs}")
        
        print("\n=== Checking port 443 ===")
        status, netstat, err = run_ssh_command(client, "ss -tulpn | grep 443")
        print(f"Netstat status: {status}")
        print(f"Port info:\n{netstat}")
        
        print("\n=== Checking logs ===")
        status, logs, err = run_ssh_command(client, "tail -20 /root/mtproxy.log")
        print(f"Logs:\n{logs}")
        
        if "secret=" in logs or "Secret" in logs or len(procs) > 10:
            print("\n=== Trying to extract secret from process ===")
            # Try to read from command line
            status, cmdline, err = run_ssh_command(client, "ps aux | grep mtproto-proxy | grep -v grep | head -1")
            print(f"Process command line:\n{cmdline}")
            
            # Extract the secret from the command
            match = re.search(r'-S\s+([a-f0-9]{32})', cmdline)
            if match:
                actual_secret = match.group(1)
                link = f"tg://proxy?server={HOST}&port=443&secret={actual_secret}"
                print(f"\n✅ SUCCESS!")
                print(f"Secret: {actual_secret}")
                print(f"Link: {link}")
                
                # Save to file
                with open("/content/mtproxy_link.txt", "w") as f:
                    f.write(link)
                print("Link saved to /content/mtproxy_link.txt")
                return
                
        print("\n❌ MTProxy failed to start or get secret")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()