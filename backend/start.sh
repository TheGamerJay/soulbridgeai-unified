#!/bin/bash
exec gunicorn app:app -b 0.0.0.0:${PORT:-8080} --worker-class eventlet --workers 2 --timeout 90