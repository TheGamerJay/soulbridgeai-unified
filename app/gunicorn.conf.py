import multiprocessing, os

bind = f"0.0.0.0:{os.getenv('PORT','8080')}"   # IMPORTANT: no quotes around $PORT in Railway env
workers = int(os.getenv("WEB_CONCURRENCY", str(max(multiprocessing.cpu_count(), 2))))
threads = int(os.getenv("WEB_THREADS", "4"))
timeout = int(os.getenv("WEB_TIMEOUT", "180"))
graceful_timeout = 30
keepalive = 20
worker_class = "gthread"
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info")