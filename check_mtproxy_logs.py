#!/usr/bin/env python3
"""
Check MTProxy logs for debugging.
"""
import paramiko

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
        
        print("=== Checking processes ===")
        status, procs, err = run_ssh_command(client, "ps aux | grep -E 'mtproto|mtproxy'")
        print(f"Status: {status}")
        print(f"Output:\n{procs}")
        print(f"Error:\n{err}")
        
        print("\n=== Checking logs ===")
        status, logs, err = run_ssh_command(client, "cat /root/mtproxy.log 2>/dev/null || echo 'No log file'")
        print(f"Status: {status}")
        print(f"Logs:\n{logs}")
        
        print("\n=== Checking port 443 ===")
        status, netstat, err = run_ssh_command(client, "ss -tulpn | grep 443")
        print(f"Status: {status}")
        print(f"Output:\n{netstat}")
        
        print("\n=== Checking if mtproxy directory exists ===")
        status, ls, err = run_ssh_command(client, "ls -la /root/mtproxy 2>/dev/null || echo 'Directory not found'")
        print(f"Status: {status}")
        print(f"Output:\n{ls}")
        
        print("\n=== Checking if binary exists ===")
        status, ls, err = run_ssh_command(client, "ls -la /root/mtproxy/objs/bin/mtproto-proxy 2>/dev/null || echo 'Binary not found'")
        print(f"Status: {status}")
        print(f"Output:\n{ls}")
        
        print("\n=== Trying to start MTProxy again ===")
        cmd = "cd /root/mtproxy && SECRET=$(openssl rand -hex 32) && echo \"Secret: $SECRET\" && ./objs/bin/mtproto-proxy -p443 -H443 -S$SECRET -Dgoogle.com -d"
        status, out, err = run_ssh_command(client, cmd)
        print(f"Status: {status}")
        print(f"Output:\n{out}")
        print(f"Error:\n{err}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()