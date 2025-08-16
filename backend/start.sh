#!/bin/bash
exec gunicorn app:app -b 0.0.0.0:${PORT:-8080} --worker-class gthread --threads 4 --workers 2 --timeout 300