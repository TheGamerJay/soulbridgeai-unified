# Gunicorn Configuration for SoulBridge AI Production Server
import multiprocessing
import os

# Server socket
bind = "0.0.0.0:8080"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1  # Recommended formula
worker_class = "eventlet"  # For SocketIO compatibility
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100

# Restart workers after this many requests, to prevent memory leaks
preload_app = True

# Logging
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stderr
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "soulbridge-ai"

# Server mechanics
daemon = False
pidfile = "/tmp/soulbridge-ai.pid"
user = None
group = None
tmp_upload_dir = None

# SSL (for production with certificates)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile" 

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Timeout settings
timeout = 120  # 2 minutes for AI responses
keepalive = 5
graceful_timeout = 30

# Environment settings
raw_env = [
    'FLASK_ENV=production',
    'PYTHONPATH=/app'
]

print("🚀 Gunicorn config loaded - optimized for SoulBridge AI production")