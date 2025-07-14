#!/bin/bash

# Stop the service
cd "$(dirname "$0")"
if [ -f service.pid ]; then
    PID=$(cat service.pid)
    if ps -p $PID > /dev/null; then
        echo "Stopping service with PID $PID"
        kill $PID
        rm service.pid
    else
        echo "Service is not running (PID $PID not found)"
        rm service.pid
    fi
else
    echo "Service is not running (no PID file found)"
fi