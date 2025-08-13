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
}

# Ensure folders
for p in PATHS.values():
    os.makedirs(p, exist_ok=True)

# Environment toggles
USE_DIFFUSERS = os.getenv("USE_DIFFUSERS", "0") == "1"   # else OpenAI Images
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
FFMPEG_PATH = os.getenv("FFMPEG_PATH", "ffmpeg")         # if not in PATH