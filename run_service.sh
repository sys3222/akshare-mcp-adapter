#!/bin/bash

# Run the service in the background
cd "$(dirname "$0")"
python main.py > service.log 2>&1 &
echo $! > service.pid
echo "Service started with PID $(cat service.pid)"
echo "Logs are being written to service.log"