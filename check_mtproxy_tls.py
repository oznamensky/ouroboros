#!/usr/bin/env python3
"""
Check MTProxy TLS status and restart if needed.
"""
import paramiko
import time

# SSH credentials
HOST = "91.108.237.229"
USERNAME = "root"
PASSWORD = "kYyA08DTsHxn1P"

def run_ssh_command(command, client):
    """Execute command via SSH and return output."""
    stdin, stdout, stderr = client.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode().strip()
    error = stderr.read().decode().strip()
    return exit_status, output, error

def main():
    print("Connecting to VPS via SSH...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, username=USERNAME, password=PASSWORD, timeout=10)
        print("Connected successfully.\n")
        
        # Check if MTProxy is running
        print("=== Checking MTProxy processes ===")
        status, out, err = run_ssh_command("ps aux | grep mtproto-proxy | grep -v grep", client)
        print(f"Processes: {out}")
        
        # Check logs
        print("\n=== Checking logs ===")
        status, out, err = run_ssh_command("tail -50 /root/mtproxy_tls.log", client)
        print(f"Logs:\n{out}")
        if not out:
            print("(log file empty or not found)")
        
        # Check port 443
        print("\n=== Checking port 443 ===")
        status, out, err = run_ssh_command("ss -tulpn | grep :443", client)
        print(f"Port 443: {out}")
        if not out:
            print("Port 443 not listening.")
        
        # Check certificate files
        print("\n=== Checking certificate ===")
        status, out, err = run_ssh_command("ls -la /root/cert.pem /root/key.pem", client)
        print(f"Certificate files: {out}")
        
        # Try to start MTProxy with correct parameters
        print("\n=== Starting MTProxy with correct parameters ===")
        # Generate secret
        status, secret, err = run_ssh_command("openssl rand -hex 16", client)
        secret = secret.strip()
        print(f"Generated secret: {secret}")
        
        # Kill existing processes
        run_ssh_command("pkill -f mtproto-proxy 2>/dev/null || true", client)
        time.sleep(1)
        
        # Start MTProxy with TLS
        # Based on MTProxy help: -p 443 -H 443 -S <secret> -C -d
        # Also need to specify certificate? Let's try without cert (should generate self-signed)
        cmd = f"cd /root/mtproxy-tls && nohup ./objs/bin/mtproto-proxy -p 443 -H 443 -S {secret} -C -d > /root/mtproxy_tls.log 2>&1 &"
        status, out, err = run_ssh_command(cmd, client)
        print(f"Start command status: {status}")
        
        # Wait
        time.sleep(3)
        
        # Check again
        print("\n=== Checking after restart ===")
        status, out, err = run_ssh_command("ps aux | grep mtproto-proxy | grep -v grep", client)
        print(f"Processes: {out}")
        
        status, out, err = run_ssh_command("tail -20 /root/mtproxy_tls.log", client)
        print(f"Logs:\n{out}")
        
        status, out, err = run_ssh_command("ss -tulpn | grep :443", client)
        print(f"Port 443: {out}")
        
        # Generate Telegram link
        link = f"tg://proxy?server={HOST}&port=443&secret={secret}"
        print(f"\nTelegram link: {link}")
        
        # Save to file
        with open("/content/mtproxy_tls_link.txt", "w") as f:
            f.write(f"MTProxy TLS Link: {link}\n")
            f.write(f"Secret: {secret}\n")
            f.write(f"Server: {HOST}:443\n")
        print("\nLink saved to /content/mtproxy_tls_link.txt")
        
        client.close()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
