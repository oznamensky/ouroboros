#!/usr/bin/env python3
"""
Отладка запуска MTProxy - запуск вручную и просмотр вывода.
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
    print("=== Отладка запуска MTProxy ===\n")
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, username=USERNAME, password=PASSWORD, timeout=10)
        
        # Остановка всех процессов
        print("1. Остановка всех MTProxy процессов...")
        run_ssh_raw("pkill -f mtproto-proxy 2>/dev/null || true", client)
        time.sleep(1)
        
        # Генерируем secret
        print("2. Генерация secret...")
        status, secret, err = run_ssh_raw("openssl rand -hex 16", client)
        secret = secret.strip()
        print(f"   Secret: {secret}\n")
        
        # Проверяем существование бинарника
        print("3. Проверка бинарника MTProxy...")
        status, ls_out, err = run_ssh_raw("ls -la /root/mtproxy-tls/objs/bin/mtproto-proxy 2>&1", client)
        print(f"   {ls_out}\n")
        
        # Проверяем директорию
        print("4. Проверка директории MTProxy...")
        status, ls_out, err = run_ssh_raw("ls -la /root/mtproxy-tls/ 2>&1 | head -20", client)
        print(f"   {ls_out}\n")
        
        # Запуск вручную в интерактивном режиме (без -d)
        print("5. Попытка запуска (без демонизации)...")
        cmd = f"""
cd /root/mtproxy-tls && \
./objs/bin/mtproto-proxy \
  -p443 \
  -H443 \
  -S{secret} \
  -f \
  -l/root/mtproxy_test.log \
  /root/mtproxy_443.conf \
  2>&1 &
PID=$!
sleep 3
kill $PID 2>/dev/null || true
echo "Process started with PID: $PID"
"""
        status, out, err = run_ssh_raw(cmd, client)
        print(f"   Exit code: {status}")
        print(f"   Output: {out[:500] if out else '(пусто)'}")
        print(f"   Error: {err[:500] if err else '(пусто)'}\n")
        
        # Проверяем лог
        print("6. Проверка логов...")
        status, logs, err = run_ssh_raw("cat /root/mtproxy_test.log 2>&1", client)
        print(f"   Логи:\n{logs if logs else '(пусто)'}\n")
        
        # Пробуем другой подход - запуск без конфига
        print("7. Попытка запуска без конфига (просто порт 443)...")
        cmd = f"""
cd /root/mtproxy-tls && \
timeout 5 ./objs/bin/mtproto-proxy \
  -p443 \
  -H443 \
  -S{secret} \
  -f \
  2>&1 || echo "Command finished"
"""
        status, out, err = run_ssh_raw(cmd, client)
        print(f"   Exit code: {status}")
        print(f"   Output: {out[:1000] if out else '(пусто)'}")
        print(f"   Error: {err[:500] if err else '(пусто)'}\n")
        
        # Проверяем, есть ли слушающие порты
        print("8. Проверка всех слушающих портов...")
        status, ports, err = run_ssh_raw("ss -tulpn | grep LISTEN", client)
        print(f"   {ports}\n")
        
        client.close()
        
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
