#!/bin/bash
# One-command wrapper for remote executor
# Usage: ./run_remote_executor.sh

cd /root
export REMOTE_EXECUTOR_TOKEN="ourob_$(date +%s)_$(head -c 16 /dev/urandom | md5sum | cut -d' ' -f1)"
echo "Starting remote executor with token: $REMOTE_EXECUTOR_TOKEN"
nohup python3 remote_executor.py > /root/remote_executor.log 2>&1 &
echo "Server started with PID: $!"
echo "Check log: tail -f /root/remote_executor.log"