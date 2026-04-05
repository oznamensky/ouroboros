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
        
        # Create config file
        print("\n=== Creating config file ===")
        config_content = f"tg:{secret}:19196:0"
        config_cmd = f"echo '{config_content}' > /root/mtproxy.conf"
        status, out, err = run_ssh_command(client, config_cmd)
        print(f"Config created: {config_content}")
        
        print("\n=== Test with config file ===")
        cmd = f"cd /root/mtproxy && timeout 10 ./objs/bin/mtproto-proxy -p 19196 /root/mtproxy.conf 2>&1"
        status, out, err = run_ssh_command(client, cmd)
        print(f"Status: {status}")
        print(f"Output:\n{out[:1000]}")
        
        print("\n=== Test with -D flag ===")
        cmd = f"cd /root/mtproxy && timeout 10 ./objs/bin/mtproto-proxy -p 19196 -D google.com /root/mtproxy.conf 2>&1"
        status, out, err = run_ssh_command(client, cmd)
        print(f"Status: {status}")
        print(f"Output:\n{out[:1000]}")
        
        print("\n=== Test daemonize with config ===")
        cmd = f"cd /root/mtproxy && nohup ./objs/bin/mtproto-proxy -p 19196 -D google.com /root/mtproxy.conf > /root/mtproxy.log 2>&1 &"
        status, out, err = run_ssh_command(client, cmd)
        print(f"Status: {status}")
        
        time.sleep(2)
        
        print("\n=== Check if running ===")
        status, procs, err = run_ssh_command(client, "ps aux | grep mtproto-proxy | grep -v grep")
        print(f"Process list:\n{procs}")
        
        print("\n=== Check logs ===")
        status, logs, err = run_ssh_command(client, "cat /root/mtproxy.log 2>/dev/null || echo 'No log file'")
        print(f"Logs:\n{logs[:1000]}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()