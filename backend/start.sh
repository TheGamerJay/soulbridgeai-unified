#!/usr/bin/env bash
set -e

# Set default PORT if not provided (Railway standard)
: "${PORT:=5000}"

echo "🚀 Starting SoulBridge AI with Gunicorn on port ${PORT}"

# Since the app uses eventlet monkey patching for SocketIO compatibility,
# use eventlet worker class with single worker to avoid conflicts
exec gunicorn "app:app" \
  --bind "0.0.0.0:${PORT}" \
  --worker-class eventlet \
  --workers 1 \
  --timeout 120 \
  --keep-alive 2 \
  --max-requests 1000 \
  --max-requests-jitter 50 \
  --preload \
  --access-logfile - \
  --error-logfile -