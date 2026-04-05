#!/usr/bin/env python3
import subprocess
import os
import sys

def run_command(cmd, shell=False):
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=shell, capture_output=True, text=True)
    print(f"STDOUT: {result.stdout}")
    if result.stderr:
        print(f"STDERR: {result.stderr}")
    return result

def main():
    # 1. Clone MTProxy
    clone_dir = "/root/mtproxy"
    if not os.path.exists(clone_dir):
        run_command(["git", "clone", "https://github.com/TelegramMessenger/MTProxy.git", clone_dir])
    else:
        print(f"MTProxy already cloned at {clone_dir}")

    # 2. Build
    os.chdir(clone_dir)
    run_command(["make"])

    # 3. Generate secret (32 hex digits)
    secret = subprocess.check_output(["openssl", "rand", "-hex", "16"]).decode().strip()
    print(f"Generated secret: {secret}")

    # 4. Stop any existing instances
    run_command(["pkill", "-f", "mtproto-proxy"])

    # 5. Start MTProxy with Fake TLS on port 19196
    # Note: -p is listening port, -H is port for external connections
    cmd = [
        f"{clone_dir}/objs/bin/mtproto-proxy",
        "-p", "19196",
        "-H", "19196",
        "-S", secret,
        "-D",
        "-f"
    ]
    print(f"Starting MTProxy: {cmd}")
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Wait a bit to see if it starts
    import time
    time.sleep(3)
    
    if proc.poll() is None:
        print("MTProxy started successfully")
        link = f"tg://proxy?server=91.108.237.229&port=19196&secret={secret}"
        print(f"Your Telegram link: {link}")
        # Save link to file
        with open("/root/mtproxy_link.txt", "w") as f:
            f.write(link)
    else:
        stdout, stderr = proc.communicate()
        print("MTProxy failed to start")
        print(f"STDOUT: {stdout.decode()}")
        print(f"STDERR: {stderr.decode()}")
        sys.exit(1)

if __name__ == "__main__":
    main()