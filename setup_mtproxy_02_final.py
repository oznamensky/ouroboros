#!/usr/bin/env python3
"""
Финальный запуск MTProxy 0.02 с domain fronting
"""
import paramiko
import time

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
    print("=== MTProxy 0.02 Final Setup ===\n")
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, username=USERNAME, password=PASSWORD, timeout=10)
        
        # Остановка всех процессов
        print("1. Остановка процессов...")
        run_ssh_raw("pkill -f mtproto-proxy 2>/dev/null || true", client)
        time.sleep(1)
        
        # Генерируем secret
        print("2. Генерация секрета...")
        status, secret, err = run_ssh_raw("openssl rand -hex 16", client)
        secret = secret.strip()
        print(f"   Secret: {secret}\n")
        
        # Создаем конфиг для MTProxy 0.02
        # Формат: https://core.telegram.org/mtproto/mtproxy#configuration
        # Каждая строка: <secret>[:<tag>]
        print("3. Создание конфигурации...")
        config_content = f"{secret}:00000000000000000000000000000000"
        run_ssh_raw(f'echo "{config_content}" > /root/mtproxy_443.conf', client)
        run_ssh_raw(f'echo "{secret}" > /root/mtproxy_secret.txt', client)
        
        # Проверяем конфиг
        status, cat, err = run_ssh_raw("cat /root/mtproxy_443.conf", client)
        print(f"   Конфиг: {cat.strip()}\n")
        
        # Создаем директорию для логов
        run_ssh_raw("mkdir -p /root/mtproxy_logs", client)
        
        # Запуск MTProxy 0.02 с domain fronting
        # Синтаксис: mtproto-proxy -p443 -H443 -D<domain> -S<secret> -d1 -l<log> <config>
        print("4. Запуск MTProxy 0.02...")
        
        # Команда с domain fronting для Telegram domains
        cmd = f"""
cd /root/mtproxy-tls && \
nohup ./objs/bin/mtproto-proxy \
  -p443 \
  -H443 \
  -Dtelegram.org \
  -Dcdn.telegram.org \
  -Dtelegramcdn.org \
  -Dcore.telegram.org \
  -d1 \
  -l/root/mtproxy_logs/mtproxy_443.log \
  /root/mtproxy_443.conf \
> /dev/null 2>&1 &
echo $!
"""
        status, pid_out, err = run_ssh_raw(cmd, client)
        pid = pid_out.strip()
        print(f"   PID: {pid}\n")
        
        # Ждем
        time.sleep(3)
        
        # Проверяем процесс
        print("5. Проверка процесса...")
        status, proc, err = run_ssh_raw("ps aux | grep mtproto-proxy | grep -v grep", client)
        print(f"   Процесс: {proc if proc else 'НЕ НАЙДЕН'}\n")
        
        # Проверяем порт
        print("6. Проверка порта 443...")
        status, port, err = run_ssh_raw("ss -tulpn | grep :443", client)
        print(f"   Порт 443: {port if port else 'НЕ СЛУШАЕТ'}\n")
        
        # Проверяем логи
        print("7. Проверка логов...")
        status, logs, err = run_ssh_raw("cat /root/mtproxy_logs/mtproxy_443.log 2>&1 | tail -30", client)
        print(f"   Логи:\n{logs if logs else '(пусто)'}\n")
        
        # Если не работает, попробуем без domain fronting
        if not port:
            print("8. Попытка без domain fronting...")
            run_ssh_raw("pkill -f mtproto-proxy 2>/dev/null || true", client)
            time.sleep(1)
            
            cmd = f"""
cd /root/mtproxy-tls && \
nohup ./objs/bin/mtproto-proxy \
  -p443 \
  -H443 \
  -d1 \
  -l/root/mtproxy_logs/mtproxy_443_nodomain.log \
  /root/mtproxy_443.conf \
> /dev/null 2>&1 &
echo $!
"""
            status, pid_out, err = run_ssh_raw(cmd, client)
            time.sleep(3)
            
            status, logs, err = run_ssh_raw("cat /root/mtproxy_logs/mtproxy_443_nodomain.log 2>&1 | tail -30", client)
            print(f"   Новые логи:\n{logs if logs else '(пусто)'}\n")
            
            status, port, err = run_ssh_raw("ss -tulpn | grep :443", client)
            print(f"   Порт 443: {port if port else 'НЕ СЛУШАЕТ'}\n")
        
        # Генерируем ссылки
        print("="*60)
        if port:
            print("✅ MTProxy 0.02 УСПЕШНО ЗАПУЩЕН!")
            print("="*60)
            
            link_tg = f"tg://proxy?server={HOST}&port=443&secret={secret}"
            link_https = f"https://t.me/proxy?server={HOST}&port=443&secret={secret}"
            
            print(f"\n📱 Telegram ссылка (tg://):")
            print(f"{link_tg}")
            print(f"\n🌐 Telegram ссылка (https://):")
            print(f"{link_https}")
            
            # Сохраняем ссылки
            with open("/content/mtproxy_443_link.txt", "w") as f:
                f.write(f"Telegram link (tg://): {link_tg}\n")
                f.write(f"Telegram link (https://): {link_https}\n")
                f.write(f"\nSecret: {secret}\n")
                f.write(f"\nPort: 443\n")
                f.write(f"Domain fronting enabled for: telegram.org, cdn.telegram.org, telegramcdn.org, core.telegram.org\n")
            
            print(f"\n✅ Ссылка сохранена в /content/mtproxy_443_link.txt")
        else:
            print("❌ ОШИБКА: MTProxy не удалось запустить")
            print("="*60)
            print(f"\nПроверьте логи в /root/mtproxy_logs/")
        
        client.close()
        
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
