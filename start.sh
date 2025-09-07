#!/bin/bash
PORT=${PORT:-8080}
WEB_CONCURRENCY=${WEB_CONCURRENCY:-1}
WORKER_CLASS=${WORKER_CLASS:-sync}
GUNICORN_TIMEOUT=${GUNICORN_TIMEOUT:-300}

cd /app/backend

# Run database fix before starting the app (one-time fix for user_activity_log table)
echo "Running database schema fix..."
if python fix_user_activity_log.py; then
    echo "Database fix completed successfully"
else
    echo "Database fix failed, continuing with app startup..."
fi

exec gunicorn app:app --bind 0.0.0.0:$PORT --workers $WEB_CONCURRENCY --worker-class $WORKER_CLASS --timeout $GUNICORN_TIMEOUT