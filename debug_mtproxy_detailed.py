#!/usr/bin/env python3
"""
Детальная отладка запуска MTProxy
"""
import paramiko
import time

HOST = "91.108.237.229"
USERNAME = "root"
PASSWORD = "kYyA08DTsHxn1P"

def run_ssh_raw(command, client):
    """Выполнить команду и вернуть полный вывод."""
    stdin, stdout, stderr = client.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    out = stdout.read().decode()
    err = stderr.read().decode()
    return exit_status, out, err

def main():
    print("=== Детальная отладка MTProxy ===\n")
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, username=USERNAME, password=PASSWORD, timeout=10)
        
        # Остановка всех процессов
        print("1. Остановка всех процессов...")
        run_ssh_raw("pkill -f mtproto-proxy 2>/dev/null || true", client)
        run_ssh_raw("pkill -f mtproxy 2>/dev/null || true", client)
        time.sleep(2)
        
        # Проверяем порт 443
        print("2. Проверка порта 443...")
        status, port, err = run_ssh_raw("netstat -tulpn 2>/dev/null | grep :443 || ss -tulpn 2>/dev/null | grep :443 || echo 'Port 443 is free'", client)
        print(f"   {port}\n")
        
        # Проверяем права на бинарник
        print("3. Проверка прав бинарника...")
        status, ls, err = run_ssh_raw("ls -la /root/mtproxy-tls/objs/bin/mtproto-proxy", client)
        print(f"   {ls}\n")
        
        # Генерируем secret
        print("4. Генерация secret...")
        status, secret, err = run_ssh_raw("openssl rand -hex 16", client)
        secret = secret.strip()
        print(f"   Secret: {secret}\n")
        
        # Запуск с полным выводом (без демонизации)
        print("5. Запуск с полным выводом (интерактивный режим)...")
        cmd = f"""
cd /root/mtproxy-tls && \
timeout 10 ./objs/bin/mtproto-proxy \
  -p443 \
  -H443 \
  -S{secret} \
  -Dtelegram.org \
  -Dcdn.telegram.org \
  -v3 \
  -l/root/mtproxy_test.log \
  2>&1 || echo "Process ended"
"""
        status, out, err = run_ssh_raw(cmd, client)
        print(f"   Exit code: {status}")
        print(f"   Output:\n{out if out else '(пусто)'}\n")
        if err:
            print(f"   Error:\n{err}\n")
        
        # Проверяем лог
        print("6. Проверка лога...")
        status, logs, err = run_ssh_raw("cat /root/mtproxy_test.log 2>&1", client)
        print(f"   Log:\n{logs if logs else '(пусто)'}\n")
        
        # Проверяем общий лог системы
        print("7. Проверка system log...")
        status, syslog, err = run_ssh_raw("dmesg | tail -20", client)
        print(f"   Dmesg:\n{syslog if syslog else '(пусто)'}\n")
        
        # Пробуем запустить на другом порту (8443)
        print("8. Попытка на порту 8443...")
        cmd = f"""
cd /root/mtproxy-tls && \
timeout 10 ./objs/bin/mtproto-proxy \
  -p8443 \
  -H8443 \
  -S{secret} \
  -v3 \
  -l/root/mtproxy_8443.log \
  2>&1 || echo "Process ended"
"""
        status, out, err = run_ssh_raw(cmd, client)
        print(f"   Exit code: {status}")
        print(f"   Output:\n{out[:500] if out else '(пусто)'}\n")
        
        # Проверяем лог
        status, logs, err = run_ssh_raw("cat /root/mtproxy_8443.log 2>&1", client)
        print(f"   Лог порта 8443:\n{logs if logs else '(пусто)'}\n")
        
        # Проверяем системный лог
        print("9. Проверка journalctl...")
        status, journal, err = run_ssh_raw("journalctl -xe | tail -50", client)
        print(f"   Journal:\n{journal if journal else '(пусто)'}\n")
        
        client.close()
        
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
