# =========================
# 📁 FILE: backend/config.py
# =========================
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
STORAGE_DIR = os.path.join(BASE_DIR, "storage")
MODELS_DIR  = os.path.join(BASE_DIR, "models")

PATHS = {
    "tmp":    os.path.join(STORAGE_DIR, "tmp"),
    "audio":  os.path.join(STORAGE_DIR, "audio"),
    "midi":   os.path.join(STORAGE_DIR, "midi"),
    "images": os.path.join(STORAGE_DIR, "images"),
    "models": os.path.join(MODELS_DIR),
    "diffsinger_models": os.path.join(MODELS_DIR, "diffsinger"),
    "logs":   os.path.join(BASE_DIR, "logs"),
    "uploads": os.path.join(STORAGE_DIR, "uploads"),
}

# Ensure folders
for p in PATHS.values():
    os.makedirs(p, exist_ok=True)

# Request/Upload limits & validation
MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH_MB", "32")) * 1024 * 1024  # 32 MB default
MAX_AUDIO_SECONDS = int(os.getenv("MAX_AUDIO_SECONDS", "600"))  # 10 minutes
MAX_LYRICS_LENGTH = int(os.getenv("MAX_LYRICS_LENGTH", "2000"))  # characters

# System dependencies
FFMPEG_PATH = os.getenv("FFMPEG_PATH", "ffmpeg")

# Environment toggles
USE_DIFFUSERS = os.getenv("USE_DIFFUSERS", "0") == "1"   # else OpenAI Images
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
USE_CUDA = os.getenv("USE_CUDA", "1") == "1"

# Rate limiting
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "1") == "1"
RATE_LIMIT_PER_MIN = int(os.getenv("RATE_LIMIT_PER_MIN", "60"))  # per IP

# Production safety
STUDIO_DEBUG_MODE = os.getenv("STUDIO_DEBUG_MODE", "1") == "1"

# CORS
CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "*")  # comma-separated or "*"

# Redis / RQ for background jobs
REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
RQ_QUEUE_NAME = os.getenv("RQ_QUEUE_NAME", "mini_studio")
RQ_ENABLED = os.getenv("RQ_ENABLED", "0") == "1"  # Enable background jobs