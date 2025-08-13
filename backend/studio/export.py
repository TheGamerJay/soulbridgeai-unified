# ==================================
# 📁 FILE: backend/studio/export.py
# ==================================
import os
from flask import send_file, abort

def export_file(asset_path, download_name=None):
    # Ensure the file exists and is safe to serve
    try:
        from config import STORAGE_DIR
    except ImportError:
        STORAGE_DIR = "storage"
    
    # asset_path should be an absolute path inside STORAGE_DIR
    if not os.path.abspath(asset_path).startswith(os.path.abspath(STORAGE_DIR)):
        return abort(403)
    if not os.path.isfile(asset_path):
        return abort(404)
    return send_file(asset_path, as_attachment=True, download_name=download_name or os.path.basename(asset_path))