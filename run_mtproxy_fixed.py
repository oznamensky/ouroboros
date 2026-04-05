#!/usr/bin/env python3
"""
Запуск MTProxy с правильным синтаксисом параметров.
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
    print("=== Запуск MTProxy с правильными параметрами ===\n")
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, username=USERNAME, password=PASSWORD, timeout=10)
        
        # Kill existing
        print("Остановка существующих процессов...")
        run_ssh("pkill -f mtproto-proxy 2>/dev/null || true", client)
        time.sleep(1)
        
        # Generate secret
        status, secret, err = run_ssh("openssl rand -hex 16", client)
        secret = secret.strip()
        print(f"Secret: {secret}\n")
        
        # Правильный запуск с синтаксисом из help:
        # -p<port> -H<http-port> -S<secret> -f -d
        print("Запуск MTProxy (Fake TLS, port 443)...")
        cmd = f"""
cd /root/mtproxy-tls && \
nohup ./objs/bin/mtproto-proxy \
  -p443 \
  -H443 \
  -S{secret} \
  -f \
  -d \
  -l/root/mtproxy.log \
> /dev/null 2>&1 &
"""
        run_ssh(cmd, client)
        time.sleep(2)
        
        # Check
        print("\nПроверка запуска...")
        status, proc, err = run_ssh("ps aux | grep mtproto-proxy | grep -v grep", client)
        print(f"Процесс: {proc if proc else 'НЕ ЗАПУЩЕН'}")
        
        status, logs, err = run_ssh("tail -20 /root/mtproxy.log", client)
        print(f"\nЛоги:\n{logs if logs else '(пусто)'}")
        
        status, port, err = run_ssh("ss -tulpn | grep :443", client)
        print(f"\nПорт 443: {port if port else 'НЕ СЛУШАЕТ'}")
        
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
        with open("/content/mtproxy_final_link.txt", "w") as f:
            f.write(f"{link_tg}\n")
        
        print("\nСсылка сохранена в /content/mtproxy_final_link.txt")
        
        client.close()
        
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
