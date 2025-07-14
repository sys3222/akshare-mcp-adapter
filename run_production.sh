#!/bin/bash

# Run the service in production mode
cd "$(dirname "$0")"

# Create cache directories
mkdir -p etf_cache
mkdir -p index_cache

# Start the service with uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 12000 --workers 4 > service.log 2>&1 &

echo $! > service.pid
echo "Service started in production mode with PID $(cat service.pid)"
echo "Logs are being written to service.log"