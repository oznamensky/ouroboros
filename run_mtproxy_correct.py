#!/usr/bin/env python3
"""
Правильный запуск MTProxy 0.02
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
        
        # Создаем конфиг с форматом secret:tag
        run_ssh_raw(f'echo "{secret}:00000000000000000000000000000000" > /root/mtproxy.conf', client)
        
        print(f"=== MTProxy 0.02 настройка ===\n")
        print(f"Secret: {secret}\n")
        
        # Правильная команда запуска для MTProxy 0.02
        # Формат: mtproto-proxy [опции] <конфиг>
        cmd = f"""
cd /root/mtproxy-tls && \
timeout 10 ./objs/bin/mtproto-proxy \
  -p443 \
  -H443 \
  -Dtelegram.org \
  -Dcdn.telegram.org \
  -Dtelegramcdn.org \
  -l/root/mtproxy_443.log \
  /root/mtproxy.conf
"""
        
        print("Запуск MTProxy...\n")
        status, out, err = run_ssh_raw(cmd, client)
        
        print(f"=== Exit code: {status} ===\n")
        print(f"=== STDOUT ===\n{out if out else '(пусто)'}\n")
        if err:
            print(f"=== STDERR ===\n{err}\n")
        
        # Проверяем лог
        status, log, err = run_ssh_raw("cat /root/mtproxy_443.log 2>&1", client)
        print(f"=== LOG ===\n{log if log else '(пусто)'}\n")
        
        # Проверяем порт
        status, port, err = run_ssh_raw("ss -tulpn | grep :443", client)
        print(f"=== Порт 443 ===\n{port if port else 'НЕ СЛУШАЕТ'}\n")
        
        client.close()
        
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
