#!/usr/bin/env python3
"""
Setup MTProxy with correct 32-hex-digit secret and Fake TLS.
Using port 19196 instead of 443 to avoid conflicts.
"""
import paramiko
import re
import time

HOST = "91.108.237.229"
USERNAME = "root"
PASSWORD = "kYyA08DTsHxn1P"
PORT = "19196"

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
        
        print("=== Checking what's on port 443 ===")
        status, netstat, err = run_ssh_command(client, "ss -tulpn | grep -E ':(443|19196)'")
        print(f"Netstat:\n{netstat}")
        
        print("\n=== Stopping nginx and MTProxy ===")
        status, out, err = run_ssh_command(client, "pkill -f mtproto-proxy 2>/dev/null; systemctl stop nginx 2>/dev/null; sleep 1")
        
        print("\n=== Checking if MTProxy binary is executable ===")
        status, ls, err = run_ssh_command(client, "ls -la /root/mtproxy/objs/bin/mtproto-proxy")
        print(f"Permissions: {ls}")
        
        print("\n=== Generating 32-hex-digit secret ===")
        status, secret, err = run_ssh_command(client, "openssl rand -hex 16")
        print(f"Secret: {secret}")
        
        print(f"\n=== Starting MTProxy on port {PORT} ===")
        # Use nohup to keep it running
        cmd = f"cd /root/mtproxy && nohup ./objs/bin/mtproto-proxy -p {PORT} -H {PORT} -S {secret} -D google.com -d > /root/mtproxy.log 2>&1 &"
        status, out, err = run_ssh_command(client, cmd)
        print(f"Start status: {status}")
        if err:
            print(f"Error: {err}")
        
        print("\n=== Waiting for service to start ===")
        time.sleep(3)
        
        print("\n=== Checking if running ===")
        status, procs, err = run_ssh_command(client, "ps aux | grep mtproto-proxy | grep -v grep")
        print(f"Process status: {status}")
        print(f"Processes:\n{procs}")
        
        print("\n=== Checking logs ===")
        status, logs, err = run_ssh_command(client, "tail -30 /root/mtproxy.log")
        print(f"Logs:\n{logs}")
        
        print("\n=== Checking port ===")
        status, port_check, err = run_ssh_command(client, f"ss -tulpn | grep {PORT}")
        print(f"Port check:\n{port_check}")
        
        # Try to parse the actual command line to get the secret
        print("\n=== Getting MTProxy process details ===")
        status, cmdline, err = run_ssh_command(client, "ps aux | grep mtproto-proxy | grep -v grep")
        print(f"Command line: {cmdline}")
        
        # Extract secret from command
        match = re.search(r'-S\s+([a-f0-9]{32})', cmdline)
        if match:
            actual_secret = match.group(1)
            link = f"tg://proxy?server={HOST}&port={PORT}&secret={actual_secret}"
            print(f"\n✅ SUCCESS!")
            print(f"Secret: {actual_secret}")
            print(f"Link: {link}")
            
            # Also save the quick format
            quick_link = f"mtproxy://{actual_secret}@{HOST}:{PORT}"
            print(f"Quick format: {quick_link}")
            
            # Save to file
            with open("/content/mtproxy_link.txt", "w") as f:
                f.write(link)
            print("Link saved to /content/mtproxy_link.txt")
            return
        
        # Check if we can read the secret from the command differently
        print("\n=== Trying alternative secret extraction ===")
        status, cmdline2, err = run_ssh_command(client, "cat /proc/$(pgrep -f mtproto-proxy | head -1)/cmdline 2>/dev/null | tr '\\0' ' '")
        print(f"CMDLINE2: {cmdline2}")
        
        # Try to find secret in the cmdline
        if "mtproto-proxy" in cmdline2:
            parts = cmdline2.split()
            for i, part in enumerate(parts):
                if part == "-S" and i+1 < len(parts):
                    secret_candidate = parts[i+1]
                    if len(secret_candidate) == 32:
                        actual_secret = secret_candidate
                        link = f"tg://proxy?server={HOST}&port={PORT}&secret={actual_secret}"
                        print(f"\n✅ SUCCESS!")
                        print(f"Secret: {actual_secret}")
                        print(f"Link: {link}")
                        
                        with open("/content/mtproxy_link.txt", "w") as f:
                            f.write(link)
                        print("Link saved to /content/mtproxy_link.txt")
                        return
        
        print("\n❌ MTProxy not running. Checking errors...")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()