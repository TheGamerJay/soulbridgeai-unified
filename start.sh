#!/bin/bash
set -e  # Exit on error for better debugging

PORT=${PORT:-8080}
WEB_CONCURRENCY=${WEB_CONCURRENCY:-1}
WORKER_CLASS=${WORKER_CLASS:-sync}
GUNICORN_TIMEOUT=${GUNICORN_TIMEOUT:-300}

echo "=== SoulBridge AI Startup Sequence ==="
echo "PORT: $PORT"
echo "WORKERS: $WEB_CONCURRENCY"
echo "WORKER_CLASS: $WORKER_CLASS"
echo "TIMEOUT: $GUNICORN_TIMEOUT"
echo ""

cd /app/backend || { echo "ERROR: Cannot cd to /app/backend"; exit 1; }
echo "✓ Changed to /app/backend directory"

# Check Python version
python --version

# Test basic imports
echo ""
echo "Testing critical imports..."
python -c "import flask; print('✓ Flask import OK')" || { echo "ERROR: Flask import failed"; exit 1; }
python -c "from app import create_app; print('✓ App import OK')" || { echo "ERROR: App import failed"; exit 1; }

# Run database fix before starting the app (fail-safe approach)
echo ""
echo "Running database schema fix..."
python fix_user_activity_log.py && echo "✓ Database fix completed" || echo "⚠ Database fix skipped, continuing..."

echo ""
echo "Starting Gunicorn server on 0.0.0.0:$PORT..."
exec gunicorn app:app --bind 0.0.0.0:$PORT --workers $WEB_CONCURRENCY --worker-class $WORKER_CLASS --timeout $GUNICORN_TIMEOUT --log-level debug