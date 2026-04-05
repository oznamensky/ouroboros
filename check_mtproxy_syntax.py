#!/usr/bin/env python3
"""
Проверка синтаксиса MTProxy 0.02
"""
import paramiko

HOST = "91.108.237.229"
USERNAME = "root"
PASSWORD = "kYyA08DTsHxn1P"

def run_ssh_raw(command, client):
    stdin, stdout, stderr = client.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    out = stdout.read().decode()
    err = stderr.read().decode()
    return exit_status, out, err

def main():
    print("=== Проверка синтаксиса MTProxy 0.02 ===\n")
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, username=USERNAME, password=PASSWORD, timeout=10)
        
        # Get full help
        print("Получение полного help...")
        status, out, err = run_ssh_raw("/root/mtproxy-tls/objs/bin/mtproto-proxy 2>&1", client)
        print(out)
        
        client.close()
        
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
