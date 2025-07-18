#!/bin/bash
PORT=${PORT:-8080}
exec gunicorn backend.app:app --bind 0.0.0.0:$PORT