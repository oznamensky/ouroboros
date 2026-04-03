import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('91.108.237.229', username='root', password='kYyA08DTsHxn1P', timeout=30)
stdin, stdout, stderr = ssh.exec_command('cat /usr/local/etc/v2ray/config.json')
print(stdout.read().decode())
ssh.close()
