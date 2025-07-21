# Gunicorn configuration for SoulBridge AI
import os

# Server socket
bind = f"0.0.0.0:{os.environ.get('PORT', '8080')}"
backlog = 2048

# Worker processes  
worker_class = "eventlet"  # Use eventlet workers for SocketIO compatibility
workers = 1  # Single worker for SocketIO compatibility
worker_connections = 1000
timeout = 300
keepalive = 2

# Restart workers
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "-"  # Log to stdout for Railway
errorlog = "-"   # Log to stderr for Railway
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = "soulbridge-ai"

# Server mechanics
preload_app = True
daemon = False
pidfile = None
user = None
group = None
tmp_upload_dir = None

# SSL (not needed for Railway)
keyfile = None
certfile = None

# Application  
wsgi_application = "app:app"