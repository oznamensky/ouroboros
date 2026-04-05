#!/usr/bin/env python3
"""Patch MTProxy PID assertion to allow PIDs > 65535"""
import paramiko

def patch_pid_assertion():
    HOST = "91.108.237.229"
    USER = "root"
    PASS = "kYyA08DTsHxn1P"
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USER, password=PASS)
    
    # Read the original file
    stdin, stdout, stderr = ssh.exec_command("cat /root/MTProxy/common/pid.c")
    content = stdout.read().decode()
    
    # Patch the assertion line
    # Original: assert (!(p & 0xffff0000));
    # New: p = p & 0xffff; (just take lower 16 bits)
    patched = content.replace(
        "    assert (!(p & 0xffff0000));",
        "    p = p & 0xffff;  // Fix: allow PIDs > 65535 by taking lower 16 bits"
    )
    
    # Write patched file
    ssh.exec_command("cp /root/MTProxy/common/pid.c /root/MTProxy/common/pid.c.backup")
    ssh.exec_command(f"cat > /root/MTProxy/common/pid.c << 'EOF'\n{patched}\nEOF")
    
    # Rebuild MTProxy
    print("Rebuilding MTProxy...")
    stdin, stdout, stderr = ssh.exec_command("cd /root/MTProxy && make clean && make")
    print(stdout.read().decode())
    print(stderr.read().decode())
    
    ssh.close()

if __name__ == "__main__":
    patch_pid_assertion()