#!/usr/bin/env python3
"""
Настройка MTProxy 0.02 с правильным форматом конфига
"""
import paramiko

HOST = "91.108.237.229"
USERNAME = "root"
PASSWORD = "kYyA08DTsHxn1P"

def run_ssh_raw(command, client, timeout=30):
    stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
    exit_status = stdout.channel.recv_exit_status()
    out = stdout.read().decode()
    err = stderr.read().decode()
    return exit_status, out, err

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, username=USERNAME, password=PASSWORD, timeout=10)
        
        # Остановка всех MTProxy процессов
        run_ssh_raw("pkill -f mtproto-proxy 2>/dev/null || true", client)
        
        # Генерация секрета (16 байт = 32 hex символа)
        status, secret, err = run_ssh_raw("openssl rand -hex 16", client)
        secret = secret.strip()
        
        print("=== MTProxy 0.02 - правильная настройка ===\n")
        print(f"Secret: {secret}\n")
        
        # Правильный формат конфига для MTProxy 0.02:
        # Line 1: proxy <listen_ip>:<listen_port>;
        # Line 2: <secret>:<proxy_tag>
        # Для domain fronting: указываем домены через -D флаг
        
        config_content = f"proxy 0.0.0.0:443;\n{secret}:00000000000000000000000000000000\n"
        run_ssh_raw(f'echo -e "{config_content}" > /root/mtproxy.conf', client)
        
        # Проверяем конфиг
        status, conf, err = run_ssh_raw("cat /root/mtproxy.conf", client)
        print(f"Конфиг:\n{conf}\n")
        
        # Запуск MTProxy 0.02 с domain fronting
        # -D telegram.org - разрешает только этот домен
        # -p443 - слушать на порту 443
        # -H443 - HTTP порт (для TLS)
        # -l - лог файл
        cmd = f"""
cd /root/mtproxy-tls && \
timeout 5 ./objs/bin/mtproto-proxy \
  -p443 \
  -H443 \
  -Dtelegram.org \
  -Dcdn.telegram.org \
  -l/root/mtproxy.log \
  /root/mtproxy.conf 2>&1
"""
        
        print("Запуск MTProxy 0.02 с domain fronting (порт 443)...\n")
        status, out, err = run_ssh_raw(cmd, client, timeout=10)
        
        print(f"=== Exit code: {status} ===\n")
        if out:
            print(f"=== STDOUT ===\n{out}\n")
        if err:
            print(f"=== STDERR ===\n{err}\n")
        
        # Проверяем, запущен ли процесс
        status, proc, err = run_ssh_raw("ps aux | grep mtproto-proxy | grep -v grep", client)
        print(f"=== Процесс ===\n{proc if proc else 'НЕ ЗАПУЩЕН'}\n")
        
        # Проверяем лог
        status, log, err = run_ssh_raw("cat /root/mtproxy.log 2>/dev/null | tail -20", client)
        if log:
            print(f"=== Лог (последние 20 строк) ===\n{log}\n")
        
        # Проверяем порт 443
        status, port, err = run_ssh_raw("ss -tulpn | grep :443", client)
        print(f"=== Порт 443 ===\n{port if port else 'НЕ СЛУШАЕТ'}\n")
        
        # Генерируем ссылку для Telegram
        # Формат: tg://proxy?server=<ip>&port=<port>&secret=<secret>
        print(f"=== Ссылка для Telegram ===\n")
        print(f"tg://proxy?server=91.108.237.229&port=443&secret={secret}\n")
        print(f"ИЛИ в виде hex: tg://proxy?server=91.108.237.229&port=443&secret=01{secret}\n")
        
        client.close()
        
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
