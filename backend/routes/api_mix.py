# ==================================
# 📁 FILE: backend/routes/api_mix.py
# ==================================
from flask import Blueprint, request, jsonify, session
from studio.mixer import mix_tracks
from studio.library import studio_library
import logging

logger = logging.getLogger(__name__)

def is_logged_in():
    return session.get('user_id') is not None

def get_effective_plan(user_plan, trial_active):
    if trial_active and user_plan == "free":
        return "max"
    return user_plan

bp = Blueprint("api_mix", __name__)

@bp.route("/api/mix", methods=["POST"])
def api_mix():
    """Mix vocals with background music"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        # Check access permissions
        user_plan = session.get('user_plan', 'free')
        trial_active = session.get('trial_active', False)
        effective_plan = get_effective_plan(user_plan, trial_active)
        
        if effective_plan != 'max':
            return jsonify({"success": False, "error": "Mini Studio requires Max tier or trial"}), 403
        
        data = request.get_json(force=True)
        vocals_wav = data.get("vocals_wav", "").strip()
        bgm_wav = data.get("bgm_wav", "").strip()
        vocal_db = float(data.get("vocal_db", -3.0))
        bgm_db = float(data.get("bgm_db", -8.0))
        
        if not vocals_wav:
            return jsonify({"success": False, "error": "Vocals WAV file path is required"}), 400
        
        if not bgm_wav:
            return jsonify({"success": False, "error": "Background music WAV file path is required"}), 400
        
        # Check if files exist
        import os
        if not os.path.exists(vocals_wav):
            return jsonify({"success": False, "error": "Vocals WAV file not found"}), 404
        
        if not os.path.exists(bgm_wav):
            return jsonify({"success": False, "error": "Background music WAV file not found"}), 404
        
        # Check credits
        user_id = session.get('user_id')
        try:
            from unified_tier_system import get_user_credits, get_trial_trainer_time
            credits = get_user_credits(user_id) if user_id else 0
            
            if user_plan == 'free' and trial_active:
                trial_credits = get_trial_trainer_time(user_id)
                credits = max(credits, trial_credits)
            
            if credits <= 0:
                return jsonify({"success": False, "error": "No studio time remaining"}), 403
        except ImportError:
            credits = 60 if (user_plan == 'free' and trial_active) else 0
        
        # Mix tracks
        try:
            mixed_path = mix_tracks(
                vocals_wav=vocals_wav,
                bgm_wav=bgm_wav,
                vocal_db=vocal_db,
                bgm_db=bgm_db
            )
            
            # Save to library
            asset_id = studio_library.save_asset(
                user_id=user_id,
                kind="mixed",
                path=mixed_path,
                meta={
                    "vocals_wav": vocals_wav,
                    "bgm_wav": bgm_wav,
                    "vocal_db": vocal_db,
                    "bgm_db": bgm_db
                }
            )
            
            return jsonify({
                "success": True,
                "message": "Tracks mixed successfully",
                "mixed_path": mixed_path,
                "asset_id": asset_id,
                "credits_remaining": credits - 1
            })
            
        except Exception as e:
            logger.error(f"Mixing error: {e}")
            return jsonify({
                "success": False, 
                "error": f"Failed to mix tracks: {str(e)}"
            }), 500
        
    except Exception as e:
        logger.error(f"API mix error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500