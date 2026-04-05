#!/usr/bin/env python3
"""
Check if MTProxy is running and get the link.
"""
import paramiko
import sys

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
        
        # Check process
        status, procs, err = run_ssh_command(client, "ps aux | grep mtproto-proxy | grep -v grep")
        if status == 0 and procs:
            print(f"MTProxy process found: {procs}")
            
            # Check port
            status, netstat, err = run_ssh_command(client, "ss -tulpn | grep 443")
            print(f"Port 443 status: {netstat}")
            
            # Read log to find secret
            status, logs, err = run_ssh_command(client, "cat /root/mtproxy.log")
            if "secret=" in logs:
                # Extract secret
                import re
                match = re.search(r'secret=([a-f0-9]{64})', logs)
                if match:
                    secret = match.group(1)
                    link = f"tg://proxy?server={HOST}&port=443&secret={secret}"
                    print(f"\n✅ MTProxy is running!")
                    print(f"Link: {link}")
                    
                    # Save to file
                    with open("/content/mtproxy_link.txt", "w") as f:
                        f.write(link)
                    print("Link saved to /content/mtproxy_link.txt")
                    sys.exit(0)
            
            # Try to get secret from process command line
            status, cmdline, err = run_ssh_command(client, "cat /proc/$(pgrep mtproto-proxy)/cmdline 2>/dev/null | tr '\\0' ' '")
            if cmdline:
                print(f"Command line: {cmdline}")
                match = re.search(r'-S([a-f0-9]{64})', cmdline)
                if match:
                    secret = match.group(1)
                    link = f"tg://proxy?server={HOST}&port=443&secret={secret}"
                    print(f"\n✅ MTProxy is running!")
                    print(f"Link: {link}")
                    
                    with open("/content/mtproxy_link.txt", "w") as f:
                        f.write(link)
                    print("Link saved to /content/mtproxy_link.txt")
                    sys.exit(0)
        
        print("MTProxy not running or secret not found")
        sys.exit(1)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        client.close()

if __name__ == "__main__":
    main()