# ======================================
# 📁 FILE: backend/routes/api_effects.py
# ======================================
from flask import Blueprint, request, jsonify, session
from studio.effects import apply_effects
from studio.library import studio_library
import logging

logger = logging.getLogger(__name__)

def is_logged_in():
    return session.get('user_id') is not None

def get_effective_plan(user_plan, trial_active):
    if trial_active and user_plan == "bronze":
        return "gold"
    return user_plan

bp = Blueprint("api_effects", __name__)

@bp.route("/api/effects", methods=["POST"])
def api_effects():
    """Apply audio effects to vocal tracks"""
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
        wav_path = data.get("wav_path", "").strip()
        pitch_semitones = float(data.get("pitch_semitones", 0))
        reverb_amount = float(data.get("reverb_amount", 0.0))
        eq = data.get("eq")  # Optional EQ settings
        
        if not wav_path:
            return jsonify({"success": False, "error": "WAV file path is required"}), 400
        
        # Check if file exists
        import os
        if not os.path.exists(wav_path):
            return jsonify({"success": False, "error": "WAV file not found"}), 404
        
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
        
        # Apply effects
        try:
            processed_path = apply_effects(
                wav_path=wav_path,
                pitch_semitones=pitch_semitones,
                reverb_amount=reverb_amount,
                eq=eq
            )
            
            # Save to library
            asset_id = studio_library.save_asset(
                user_id=user_id,
                kind="vocal_fx",
                path=processed_path,
                meta={
                    "original_path": wav_path,
                    "pitch_semitones": pitch_semitones,
                    "reverb_amount": reverb_amount,
                    "eq": eq
                }
            )
            
            return jsonify({
                "success": True,
                "message": "Effects applied successfully",
                "processed_path": processed_path,
                "asset_id": asset_id,
                "credits_remaining": credits - 1
            })
            
        except Exception as e:
            logger.error(f"Effects processing error: {e}")
            return jsonify({
                "success": False, 
                "error": f"Failed to apply effects: {str(e)}"
            }), 500
        
    except Exception as e:
        logger.error(f"API effects error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500