# ============================
# 📁 backend/routes/api_uploads.py
# ============================
import os, uuid
from flask import Blueprint, request, jsonify, session
from werkzeug.utils import secure_filename
from .common import safe_api, rate_limit, has_allowed_ext, ALLOWED_EXTS_AUDIO, ALLOWED_EXTS_MIDI, ALLOWED_EXTS_IMAGE
from config import PATHS
import logging

logger = logging.getLogger(__name__)

def is_logged_in():
    return session.get('user_id') is not None

def get_effective_plan(user_plan, trial_active):
    """Get effective plan - Bronze users with active trial get Gold access"""
    if trial_active and user_plan == "bronze":
        return "gold"
    return user_plan

bp = Blueprint("api_uploads", __name__)

def _save_file(file, subdir, allowed_extensions):
    """Save uploaded file with validation"""
    if not file or not file.filename:
        raise ValueError("No file provided")
    
    filename = secure_filename(file.filename)
    if not filename:
        raise ValueError("Invalid filename")
    
    if not has_allowed_ext(filename, allowed_extensions):
        raise ValueError(f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}")
    
    # Create upload directory
    upload_dir = os.path.join(PATHS["uploads"], subdir)
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate unique filename
    base, ext = os.path.splitext(filename)
    unique_filename = f"{uuid.uuid4().hex}{ext.lower()}"
    file_path = os.path.join(upload_dir, unique_filename)
    
    # Save file
    file.save(file_path)
    logger.info(f"File uploaded: {file_path}")
    
    return file_path

@bp.route("/api/upload/audio", methods=["POST"])
@rate_limit(per_min=20)
@safe_api
def upload_audio():
    """Upload audio files for Mini Studio processing"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        # Check access permissions
        user_plan = session.get('user_plan', 'free')
        trial_active = session.get('trial_active', False)
        effective_plan = get_effective_plan(user_plan, trial_active)
        
        if effective_plan != 'gold':
            return jsonify({"success": False, "error": "Mini Studio requires Gold tier or trial"}), 403
        
        if "file" not in request.files:
            return jsonify({"success": False, "error": "No file provided"}), 400
        
        file = request.files["file"]
        file_path = _save_file(file, "audio", ALLOWED_EXTS_AUDIO)
        
        return jsonify({
            "success": True,
            "message": "Audio file uploaded successfully",
            "path": file_path,
            "filename": os.path.basename(file_path)
        })
        
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        logger.error(f"Audio upload error: {e}")
        return jsonify({"success": False, "error": "Upload failed"}), 500

@bp.route("/api/upload/midi", methods=["POST"])
@rate_limit(per_min=30)
@safe_api
def upload_midi():
    """Upload MIDI files for Mini Studio"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        user_plan = session.get('user_plan', 'free')
        trial_active = session.get('trial_active', False)
        effective_plan = get_effective_plan(user_plan, trial_active)
        
        if effective_plan != 'gold':
            return jsonify({"success": False, "error": "Mini Studio requires Gold tier or trial"}), 403
        
        if "file" not in request.files:
            return jsonify({"success": False, "error": "No file provided"}), 400
        
        file = request.files["file"]
        file_path = _save_file(file, "midi", ALLOWED_EXTS_MIDI)
        
        return jsonify({
            "success": True,
            "message": "MIDI file uploaded successfully",
            "path": file_path,
            "filename": os.path.basename(file_path)
        })
        
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        logger.error(f"MIDI upload error: {e}")
        return jsonify({"success": False, "error": "Upload failed"}), 500

@bp.route("/api/upload/image", methods=["POST"])
@rate_limit(per_min=15)
@safe_api
def upload_image():
    """Upload image files (for reference, backgrounds, etc.)"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        user_plan = session.get('user_plan', 'free')
        trial_active = session.get('trial_active', False)
        effective_plan = get_effective_plan(user_plan, trial_active)
        
        if effective_plan != 'gold':
            return jsonify({"success": False, "error": "Mini Studio requires Gold tier or trial"}), 403
        
        if "file" not in request.files:
            return jsonify({"success": False, "error": "No file provided"}), 400
        
        file = request.files["file"]
        file_path = _save_file(file, "images", ALLOWED_EXTS_IMAGE)
        
        return jsonify({
            "success": True,
            "message": "Image file uploaded successfully",
            "path": file_path,
            "filename": os.path.basename(file_path)
        })
        
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        logger.error(f"Image upload error: {e}")
        return jsonify({"success": False, "error": "Upload failed"}), 500