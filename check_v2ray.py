import paramiko
import sys

def check_v2ray():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect('91.108.237.229', username='root', password='kYyA08DTsHxn1P', timeout=30)
        
        # Check if V2Ray config exists
        stdin, stdout, stderr = ssh.exec_command('cat /usr/local/etc/v2ray/config.json 2>/dev/null || echo "NO_CONFIG"')
        config = stdout.read().decode().strip()
        
        if config == "NO_CONFIG":
            print("V2Ray config not found")
            return None
        
        print("V2Ray config found:")
        print(config[:500])  # Print first 500 chars
        
        # Check if V2Ray service is running
        stdin, stdout, stderr = ssh.exec_command('systemctl is-active v2ray 2>/dev/null || echo "inactive"')
        status = stdout.read().decode().strip()
        print(f"V2Ray service status: {status}")
        
        # Check if port 443 is listening
        stdin, stdout, stderr = ssh.exec_command('netstat -tulpn 2>/dev/null | grep :443 || echo "Port 443 not listening"')
        port_info = stdout.read().decode().strip()
        print(f"Port 443: {port_info}")
        
        ssh.close()
        return config
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    check_v2ray()