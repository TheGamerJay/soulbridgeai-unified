#!/bin/bash
set -e

PORT=${PORT:-8080}
cd /app/backend

echo "Starting SoulBridge AI on port $PORT"
echo "Current directory: $(pwd)"
echo "Python path: $PYTHONPATH"
echo "Files in directory:"
ls -la

# Test imports first
echo "Testing Python imports..."
python3 test_imports.py || echo "Import test failed, using minimal app"

# Try to start the full app, fallback to minimal if it fails
echo "Attempting to start full application..."
if python3 -c "import app; print('Full app imports OK')"; then
    echo "Starting full SoulBridge AI application..."
    exec gunicorn app:app \
      --bind 0.0.0.0:$PORT \
      --workers 1 \
      --timeout 120 \
      --log-level info \
      --access-logfile - \
      --error-logfile -
else
    echo "Full app failed, starting minimal application..."
    exec gunicorn app_minimal:app \
      --bind 0.0.0.0:$PORT \
      --workers 1 \
      --timeout 120 \
      --log-level info \
      --access-logfile - \
      --error-logfile -
fi