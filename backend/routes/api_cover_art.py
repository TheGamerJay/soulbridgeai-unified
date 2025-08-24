# =======================================
# 📁 FILE: backend/routes/api_cover_art.py
# =======================================
from flask import Blueprint, request, jsonify, session
from studio.cover_art import generate_art
from studio.library import studio_library
import logging

logger = logging.getLogger(__name__)

def is_logged_in():
    return session.get('user_id') is not None

def get_effective_plan(user_plan, trial_active):
    if trial_active and user_plan == "bronze":
        return "gold"
    return user_plan

bp = Blueprint("api_cover_art", __name__)

@bp.route("/api/cover-art", methods=["POST"])
def api_cover_art():
    """Generate AI cover art for songs"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        # Check access permissions
        user_plan = session.get('user_plan', 'bronze')
        trial_active = session.get('trial_active', False)
        effective_plan = get_effective_plan(user_plan, trial_active)
        
        if effective_plan != 'gold':
            return jsonify({"success": False, "error": "Mini Studio requires Gold tier or trial"}), 403
        
        data = request.get_json(force=True)
        prompt = data.get("prompt", "").strip()
        size = data.get("size", "1024x1024")
        
        if not prompt:
            return jsonify({"success": False, "error": "Prompt is required"}), 400
        
        # Check credits
        user_id = session.get('user_id')
        try:
            from unified_tier_system import get_user_credits, get_trial_trainer_time
            credits = get_user_credits(user_id) if user_id else 0
            
            if user_plan == 'bronze' and trial_active:
                trial_credits = get_trial_trainer_time(user_id)
                credits = max(credits, trial_credits)
            
            if credits <= 0:
                return jsonify({"success": False, "error": "No studio time remaining"}), 403
        except ImportError:
            credits = 60 if (user_plan == 'bronze' and trial_active) else 0
        
        # Generate cover art
        try:
            art_path = generate_art(
                prompt=prompt,
                size=size
            )
            
            # Save to library
            asset_id = studio_library.save_asset(
                user_id=user_id,
                kind="cover_art",
                path=art_path,
                meta={
                    "prompt": prompt,
                    "size": size
                }
            )
            
            return jsonify({
                "success": True,
                "message": "Cover art generated successfully",
                "art_path": art_path,
                "asset_id": asset_id,
                "credits_remaining": credits - 1
            })
            
        except Exception as e:
            logger.error(f"Cover art generation error: {e}")
            return jsonify({
                "success": False, 
                "error": f"Failed to generate cover art: {str(e)}"
            }), 500
        
    except Exception as e:
        logger.error(f"API cover art error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500