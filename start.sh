#!/bin/bash

PORT=${PORT:-8080}
WEB_CONCURRENCY=${WEB_CONCURRENCY:-1}
WORKER_CLASS=${WORKER_CLASS:-sync}
GUNICORN_TIMEOUT=${GUNICORN_TIMEOUT:-300}

cd /app/backend

# Run database fix before starting the app (fail-safe approach)
echo "Starting SoulBridge AI deployment..."
echo "Running database schema fix..."

# Try to run the database fix with timeout, but continue regardless of outcome
python fix_user_activity_log.py && echo "✅ Database fix completed" || echo "⚠️ Database fix skipped, continuing..."

echo "Starting Gunicorn server..."
exec gunicorn app:app --bind 0.0.0.0:$PORT --workers $WEB_CONCURRENCY --worker-class $WORKER_CLASS --timeout $GUNICORN_TIMEOUT