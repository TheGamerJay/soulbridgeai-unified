# ===============================
# 📁 backend/logging_setup.py
# ===============================
import logging, os
from logging.handlers import RotatingFileHandler

def init_logging(app_name="mini_studio"):
    """Initialize structured logging with rotation"""
    # Create logs directory
    logs_dir = "logs"
    os.makedirs(logs_dir, exist_ok=True)
    
    log_path = os.path.join(logs_dir, f"{app_name}.log")
    
    # File handler with rotation
    handler = RotatingFileHandler(log_path, maxBytes=5_000_000, backupCount=5)
    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    handler.setFormatter(fmt)
    
    # Configure root logger
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(handler)
    
    # Also keep console for dev
    console = logging.StreamHandler()
    console.setFormatter(fmt)
    root.addHandler(console)
    
    logging.info("Logging initialized at %s", log_path)
    return log_path