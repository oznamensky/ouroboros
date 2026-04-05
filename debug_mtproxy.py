#!/usr/bin/env python3
import paramiko
import time

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
        
        print("=== Running MTProxy with --help ===")
        status, out, err = run_ssh_command(client, "/root/mtproxy/objs/bin/mtproto-proxy --help 2>&1 | head -30")
        print(f"Status: {status}")
        print(f"Output:\n{out}")
        print(f"Error:\n{err}")
        
        print("\n=== Trying to run with minimal arguments ===")
        # Generate secret
        status, secret, err = run_ssh_command(client, "openssl rand -hex 16")
        print(f"Secret: {secret}")
        
        # Run with just port and secret
        cmd = f"cd /root/mtproxy && timeout 5 ./objs/bin/mtproto-proxy -p 19196 -S {secret} -d 2>&1"
        status, out, err = run_ssh_command(client, cmd)
        print(f"Status: {status}")
        print(f"Output:\n{out}")
        print(f"Error:\n{err}")
        
        # Check if any process is running after that
        status, procs, err = run_ssh_command(client, "ps aux | grep mtproto-proxy | grep -v grep")
        print(f"\nProcess list:\n{procs}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()