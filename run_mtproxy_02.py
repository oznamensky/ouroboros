#!/usr/bin/env python3
"""
Правильный запуск MTProxy 0.02 с domain fronting для обхода блокировок.
"""
import paramiko
import time

HOST = "91.108.237.229"
USERNAME = "root"
PASSWORD = "kYyA08DTsHxn1P"

# Домены для domain fronting (будем использовать cloudfront CDN)
ALLOWED_DOMAINS = [
    "cdn.telegram.org",
    "telegram.org",
    "core.telegram.org",
    "telegramcdn.org",
    "telegramdownload.org",
    "t.me",
]

def run_ssh_raw(command, client):
    """Выполнить команду и вернуть полный вывод."""
    stdin, stdout, stderr = client.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    out = stdout.read().decode()
    err = stderr.read().decode()
    return exit_status, out, err

def main():
    print("=== Запуск MTProxy 0.02 с Domain Fronting ===\n")
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, username=USERNAME, password=PASSWORD, timeout=10)
        
        # Остановка всех MTProxy процессов
        print("1. Остановка всех MTProxy процессов...")
        run_ssh_raw("pkill -f mtproto-proxy 2>/dev/null || true", client)
        time.sleep(1)
        
        # Генерируем secret (16 байт = 32 hex chars)
        print("2. Генерация секретного ключа...")
        status, secret, err = run_ssh_raw("openssl rand -hex 16", client)
        secret = secret.strip()
        print(f"   Secret: {secret}\n")
        
        # Создаем директорию для логов если нужно
        run_ssh_raw("mkdir -p /root/mtproxy_logs", client)
        
        # Генерируем параметры domain fronting
        domain_args = ""
        for domain in ALLOWED_DOMAINS:
            domain_args += f" -D{domain}"
        
        # Запуск MTProxy с domain fronting
        # Синтаксис: mtproto-proxy -p443 -H443 -S<secret> -D<domain> -d -l<log> <config>
        print("3. Запуск MTProxy с domain fronting...")
        cmd = f"""
cd /root/mtproxy-tls && \
nohup ./objs/bin/mtproto-proxy \
  -p443 \
  -H443 \
  -S{secret} \
  {domain_args} \
  -d \
  -l/root/mtproxy_logs/mtproxy_443.log \
  -P$(openssl rand -hex 16) \
  /root/mtproxy_443.conf \
> /dev/null 2>&1 &
echo "PID: $!"
"""
        status, out, err = run_ssh_raw(cmd, client)
        print(f"   Запуск выполнен. Output: {out if out else '(пусто)'}\n")
        time.sleep(3)
        
        # Проверяем процесс
        print("4. Проверка запущенного процесса...")
        status, proc, err = run_ssh_raw("ps aux | grep mtproto-proxy | grep -v grep", client)
        print(f"   Процесс: {proc if proc else 'НЕ ЗАПУЩЕН'}\n")
        
        # Проверяем порт
        print("5. Проверка порта 443...")
        status, port, err = run_ssh_raw("ss -tulpn | grep :443", client)
        print(f"   Порт: {port if port else 'НЕ СЛУШАЕТ'}\n")
        
        # Проверяем логи
        print("6. Проверка логов...")
        status, logs, err = run_ssh_raw("cat /root/mtproxy_logs/mtproxy_443.log 2>&1 | tail -30", client)
        print(f"   Логи:\n{logs if logs else '(пусто)'}\n")
        
        # Если порт не слушает, пробуем альтернативный запуск
        if not port:
            print("7. Альтернативный запуск (без конфига)...")
            run_ssh_raw("pkill -f mtproto-proxy 2>/dev/null || true", client)
            time.sleep(1)
            
            # Запуск без конфига
            cmd = f"""
cd /root/mtproxy-tls && \
nohup ./objs/bin/mtproto-proxy \
  -p443 \
  -H443 \
  -S{secret} \
  {domain_args} \
  -d \
  -l/root/mtproxy_logs/mtproxy_443_v2.log \
> /dev/null 2>&1 &
echo "PID: $!"
"""
            status, out, err = run_ssh_raw(cmd, client)
            time.sleep(3)
            
            status, logs, err = run_ssh_raw("cat /root/mtproxy_logs/mtproxy_443_v2.log 2>&1 | tail -30", client)
            print(f"   Новые логи:\n{logs if logs else '(пусто)'}\n")
            
            status, port, err = run_ssh_raw("ss -tulpn | grep :443", client)
            print(f"   Порт 443: {port if port else 'НЕ СЛУШАЕТ'}\n")
        
        # Генерируем ссылки для Telegram
        print("="*60)
        if port:
            print("✅ MTProxy УСПЕШНО ЗАПУЩЕН!")
            print("="*60)
            
            link_tg = f"tg://proxy?server={HOST}&port=443&secret={secret}"
            link_https = f"https://t.me/proxy?server={HOST}&port=443&secret={secret}"
            
            print(f"\n📱 Telegram ссылка (tg://):")
            print(f"{link_tg}")
            print(f"\n🌐 Telegram ссылка (https://):")
            print(f"{link_https}")
            print(f"\n📖 Для использования: Настройки → Прокси → Добавить → Вставить ссылку")
            
            # Сохраняем ссылки
            with open("/content/mtproxy_443_link.txt", "w") as f:
                f.write(f"Telegram link (tg://): {link_tg}\n")
                f.write(f"Telegram link (https://): {link_https}\n")
                f.write(f"\nSecret: {secret}\n")
            
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
