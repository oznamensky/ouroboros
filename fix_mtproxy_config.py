#!/usr/bin/env python3
"""
Проверка и исправление конфигурации MTProxy.
"""
import paramiko
import time

HOST = "91.108.237.229"
USERNAME = "root"
PASSWORD = "kYyA08DTsHxn1P"

def run_ssh(command, client):
    stdin, stdout, stderr = client.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode().strip()
    error = stderr.read().decode().strip()
    return exit_status, output, error

def main():
    print("=== Проверка и исправление конфигурации MTProxy ===\n")
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, username=USERNAME, password=PASSWORD, timeout=10)
        
        # Проверяем существующий конфиг
        print("1. Проверка существующего конфига:")
        status, config, err = run_ssh("cat /root/proxy-multi.conf 2>/dev/null || echo 'Файл не найден'", client)
        print(f"   {config}\n")
        
        # Создаем новый конфиг для порта 443
        print("2. Создание нового конфига для порта 443...")
        new_config = """# MTProxy configuration for port 443
# Secret: generated at runtime
# Port: 443 (HTTPS)

# Certificate and key (self-signed)
cert = /root/cert.pem
privkey = /root/key.pem

# Listen on port 443
# Secret will be provided at runtime
"""
        status, _, err = run_ssh("cat > /root/mtproxy_443.conf << 'EOF'\n" + new_config + "\nEOF", client)
        print(f"   Создан: /root/mtproxy_443.conf\n")
        
        # Генерируем secret
        print("3. Генерация секретного ключа...")
        status, secret, err = run_ssh("openssl rand -hex 16", client)
        secret = secret.strip()
        print(f"   Secret: {secret}\n")
        
        # Останавливаем все MTProxy
        print("4. Остановка всех процессов MTProxy...")
        run_ssh("pkill -f mtproto-proxy 2>/dev/null || true", client)
        time.sleep(1)
        
        # Запускаем MTProxy с указанием конфига
        print("5. Запуск MTProxy с конфигом...")
        cmd = f"""
cd /root/mtproxy-tls && \
nohup ./objs/bin/mtproto-proxy \
  -p443 \
  -H443 \
  -S{secret} \
  -f \
  -d \
  -l/root/mtproxy_443.log \
  /root/mtproxy_443.conf \
> /dev/null 2>&1 &
"""
        run_ssh(cmd, client)
        time.sleep(3)
        
        # Проверяем
        print("\n6. Проверка запуска...")
        status, proc, err = run_ssh("ps aux | grep mtproto-proxy | grep -v grep", client)
        print(f"   Процесс: {proc if proc else 'НЕ ЗАПУЩЕН'}")
        
        status, logs, err = run_ssh("tail -30 /root/mtproxy_443.log", client)
        print(f"\n   Логи:\n{logs if logs else '(пусто)'}")
        
        status, port, err = run_ssh("ss -tulpn | grep :443", client)
        print(f"\n   Порт 443: {port if port else 'НЕ СЛУШАЕТ'}")
        
        # Если порт не слушает, пробуем другой подход
        if not port:
            print("\n   Проблема: порт 443 не слушает. Попробуем альтернативный запуск...")
            run_ssh("pkill -f mtproto-proxy 2>/dev/null || true", client)
            time.sleep(1)
            
            # Прямой запуск без конфига, с указанием сертификата через параметры
            print("   Прямой запуск с указанием сертификата...")
            cmd = f"""
cd /root/mtproxy-tls && \
nohup ./objs/bin/mtproto-proxy \
  --port=443 \
  --http-ports=443 \
  --mtproto-secret={secret} \
  --aes-pwd=/root/mtproxy_443.conf \
  --log=/root/mtproxy_443.log \
  --daemonize \
> /dev/null 2>&1 &
"""
            run_ssh(cmd, client)
            time.sleep(3)
            
            status, logs, err = run_ssh("tail -30 /root/mtproxy_443.log", client)
            print(f"\n   Новые логи:\n{logs if logs else '(пусто)'}")
            
            status, port, err = run_ssh("ss -tulpn | grep :443", client)
            print(f"   Порт 443: {port if port else 'НЕ СЛУШАЕТ'}")
        
        # Generate links
        link_tg = f"tg://proxy?server={HOST}&port=443&secret={secret}"
        link_https = f"https://t.me/proxy?server={HOST}&port=443&secret={secret}"
        
        print("\n" + "="*60)
        print("✅ ГОТОВО!")
        print("="*60)
        print(f"\nTelegram link (tg://):")
        print(f"{link_tg}")
        print(f"\nTelegram link (https://):")
        print(f"{link_https}")
        
        # Save
        with open("/content/mtproxy_443_link.txt", "w") as f:
            f.write(f"{link_tg}\n")
        
        print("\nСсылка сохранена в /content/mtproxy_443_link.txt")
        
        client.close()
        
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
