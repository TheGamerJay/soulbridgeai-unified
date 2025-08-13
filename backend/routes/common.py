# ===============================
# 📁 backend/routes/common.py
# ===============================
import os, time, functools, logging
from flask import request, jsonify
from config import PATHS

log = logging.getLogger("api")

# ---- Path safety helpers
def is_safe_path(path: str, base_dir: str = None) -> bool:
    """Check if path is within allowed storage directory"""
    if not base_dir:
        base_dir = PATHS.get("storage", "storage")
    
    try:
        ap = os.path.abspath(path)
        base = os.path.abspath(base_dir)
        return ap.startswith(base)
    except (OSError, ValueError):
        return False

# ---- File extension validation
def has_allowed_ext(path: str, allowed: set[str]) -> bool:
    """Check if file has allowed extension"""
    _, ext = os.path.splitext(path.lower())
    return ext in allowed

# ---- Audio/MIDI/Image extensions
ALLOWED_EXTS_AUDIO = {".wav", ".mp3", ".flac", ".m4a"}
ALLOWED_EXTS_MIDI  = {".mid", ".midi"}
ALLOWED_EXTS_IMAGE = {".png", ".jpg", ".jpeg", ".webp"}

# ---- Simple in-memory rate limiting
_BUCKETS = {}

def rate_limit(per_min: int = 60):
    """Simple rate limiting decorator"""
    def decorator(fn):
        @functools.wraps(fn)
        def wrapped(*args, **kwargs):
            # Get client IP
            ip = request.remote_addr or "unknown"
            now = int(time.time() // 60)  # minute bucket
            bucket_key = (ip, fn.__name__, now)
            
            # Increment counter
            count = _BUCKETS.get(bucket_key, 0) + 1
            _BUCKETS[bucket_key] = count
            
            # Check limit
            if count > per_min:
                return jsonify({
                    "success": False, 
                    "error": "Rate limit exceeded. Try again shortly."
                }), 429
            
            return fn(*args, **kwargs)
        return wrapped
    return decorator

# ---- Global API error wrapper
def safe_api(fn):
    """Catch and log unhandled API errors"""
    @functools.wraps(fn)
    def wrapped(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            log.exception("Unhandled API error in %s", fn.__name__)
            return jsonify({
                "success": False, 
                "error": f"Internal server error: {str(e)}"
            }), 500
    return wrapped

# ---- File size validation
def validate_file_size(file_path: str, max_mb: int = 32) -> bool:
    """Check if file is within size limits"""
    try:
        size_bytes = os.path.getsize(file_path)
        size_mb = size_bytes / (1024 * 1024)
        return size_mb <= max_mb
    except OSError:
        return False

# ---- Clean old buckets periodically
def cleanup_rate_limit_buckets():
    """Remove old rate limit buckets (call periodically)"""
    now = int(time.time() // 60)
    to_remove = [k for k in _BUCKETS.keys() if k[2] < now - 5]  # Keep 5 minutes
    for k in to_remove:
        del _BUCKETS[k]