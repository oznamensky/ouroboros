#!/usr/bin/env python3
import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('91.108.237.229', username='root', password='kYyA08DTsHxn1P', timeout=10)

# Read current service file
stdin, stdout, stderr = client.exec_command('cat /etc/systemd/system/mtproxy.service')
current_service = stdout.read().decode()
print("Current service file:")
print(current_service)
print("\n" + "="*60 + "\n")

# Fix the path: /root/MTProxy -> /root/mtproxy
fixed_service = current_service.replace('/root/MTProxy', '/root/mtproxy')
print("Fixed service file:")
print(fixed_service)
print("\n" + "="*60 + "\n")

# Write fixed service file
stdin, stdout, stderr = client.exec_command('cat > /etc/systemd/system/mtproxy.service << "EOF"\n' + fixed_service + '\nEOF')
print("Writing fixed service file...")
print("Exit code:", stdout.channel.recv_exit_status())

# Reload systemd
stdin, stdout, stderr = client.exec_command('systemctl daemon-reload')
print("Daemon reload exit code:", stdout.channel.recv_exit_status())

# Restart service
stdin, stdout, stderr = client.exec_command('systemctl restart mtproxy')
print("Restart exit code:", stdout.channel.recv_exit_status())

# Check status
stdin, stdout, stderr = client.exec_command('systemctl status mtproxy --no-pager')
print("\nService status after restart:")
print(stdout.read().decode())

# Check if process is running
stdin, stdout, stderr = client.exec_command('ps aux | grep mtproto-proxy | grep -v grep')
print("Running processes:")
print(stdout.read().decode())

# Check listening ports
stdin, stdout, stderr = client.exec_command('ss -tulpn | grep LISTEN | grep -E ":(19196|443)"')
print("Listening ports:")
print(stdout.read().decode())

client.close()