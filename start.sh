#!/bin/bash
set -e

PORT=${PORT:-8080}
cd /app/backend

echo "Starting SoulBridge AI on port $PORT"
echo "Current directory: $(pwd)"
echo "Python path: $PYTHONPATH"

# Start gunicorn with better settings
exec gunicorn app:app \
  --bind 0.0.0.0:$PORT \
  --workers 1 \
  --worker-class sync \
  --timeout 120 \
  --keepalive 5 \
  --max-requests 1000 \
  --max-requests-jitter 100 \
  --preload \
  --log-level info \
  --access-logfile - \
  --error-logfile -