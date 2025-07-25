#!/bin/bash
PORT=${PORT:-8080}
cd /app/backend
exec gunicorn app:app --bind 0.0.0.0:$PORT --workers 4 --timeout 120