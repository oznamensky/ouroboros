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
        
        # Generate secret
        status, secret, err = run_ssh_command(client, "openssl rand -hex 16")
        print(f"Secret: {secret}")
        
        print("\n=== Test 1: No -d flag ===")
        cmd = f"cd /root/mtproxy && timeout 5 ./objs/bin/mtproto-proxy -p 19196 -S {secret} 2>&1"
        status, out, err = run_ssh_command(client, cmd)
        print(f"Status: {status}")
        print(f"Output:\n{out[:500]}")
        
        print("\n=== Test 2: With -d 1 ===")
        cmd = f"cd /root/mtproxy && timeout 5 ./objs/bin/mtproto-proxy -p 19196 -S {secret} -d 1 2>&1"
        status, out, err = run_ssh_command(client, cmd)
        print(f"Status: {status}")
        print(f"Output:\n{out[:500]}")
        
        print("\n=== Test 3: With --daemonize ===")
        cmd = f"cd /root/mtproxy && timeout 5 ./objs/bin/mtproto-proxy -p 19196 -S {secret} --daemonize 2>&1"
        status, out, err = run_ssh_command(client, cmd)
        print(f"Status: {status}")
        print(f"Output:\n{out[:500]}")
        
        print("\n=== Test 4: Check if binary works at all ===")
        cmd = f"cd /root/mtproxy && ./objs/bin/mtproto-proxy 2>&1 | head -10"
        status, out, err = run_ssh_command(client, cmd)
        print(f"Status: {status}")
        print(f"Output:\n{out}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()