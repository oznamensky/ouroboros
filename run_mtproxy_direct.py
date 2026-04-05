#!/usr/bin/env python3
"""
Запуск MTProxy с прямым выводом ошибок
"""
import paramiko

HOST = "91.108.237.229"
USERNAME = "root"
PASSWORD = "kYyA08DTsHxn1P"

def run_ssh_raw(command, client):
    stdin, stdout, stderr = client.exec_command(command, timeout=10)
    exit_status = stdout.channel.recv_exit_status()
    out = stdout.read().decode()
    err = stderr.read().decode()
    return exit_status, out, err

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, username=USERNAME, password=PASSWORD, timeout=10)
        
        # Остановка
        run_ssh_raw("pkill -f mtproto-proxy 2>/dev/null || true", client)
        
        # Генерация secret
        status, secret, err = run_ssh_raw("openssl rand -hex 16", client)
        secret = secret.strip()
        
        # Создаем простой конфиг
        # MTProxy 0.02 требует: secret:proxy_tag
        run_ssh_raw(f'echo "{secret}:00000000000000000000000000000000" > /root/mtproxy.conf', client)
        
        print(f"Запускаю MTProxy с secret: {secret}\n")
        
        # Запуск с прямым выводом (не в фоне)
        cmd = f"""
cd /root/mtproxy-tls && \
./objs/bin/mtproto-proxy \
  -p443 \
  -H443 \
  -Dtelegram.org \
  -Dcdn.telegram.org \
  -d0 \
  /root/mtproxy.conf 2>&1
"""
        print("Запуск MTProxy (ожидание 5 секунд)...")
        status, out, err = run_ssh_raw("timeout 5 " + cmd, client)
        
        print(f"\n=== Exit code: {status} ===")
        print(f"\n=== STDOUT ===\n{out if out else '(пусто)'}")
        print(f"\n=== STDERR ===\n{err if err else '(пусто)'}")
        
        client.close()
        
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
