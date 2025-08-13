# ====================================
# 📁 FILE: backend/routes/api_vocals.py
# ====================================
from flask import Blueprint, request, jsonify, session
from studio.diffsinger_engine import DiffSingerEngine
from studio.library import studio_library
import logging

logger = logging.getLogger(__name__)

def is_logged_in():
    return session.get('user_id') is not None

def get_effective_plan(user_plan, trial_active):
    if trial_active and user_plan == "free":
        return "max"
    return user_plan

bp = Blueprint("api_vocals", __name__)

@bp.route("/api/vocals", methods=["POST"])
def api_vocals():
    """Generate AI vocals using DiffSinger"""
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
        lyrics = data.get("lyrics", "").strip()
        midi_path = data.get("midi_path")  # optional
        voice = data.get("voice", "default")
        bpm = int(data.get("bpm", 88))
        
        if not lyrics:
            return jsonify({"success": False, "error": "Lyrics are required"}), 400
        
        # Check credits
        user_id = session.get('user_id')
        try:
            from unified_tier_system import get_user_credits, deduct_credits, get_trial_trainer_time
            credits = get_user_credits(user_id) if user_id else 0
            
            if user_plan == 'free' and trial_active:
                trial_credits = get_trial_trainer_time(user_id)
                credits = max(credits, trial_credits)
            
            if credits <= 0:
                return jsonify({"success": False, "error": "No studio time remaining"}), 403
        except ImportError:
            # Fallback if unified_tier_system not available
            credits = 60 if (user_plan == 'free' and trial_active) else 0
        
        # Generate vocals
        try:
            engine = DiffSingerEngine(voice_name=voice)
            out_wav = engine.generate_vocals(lyrics, midi_path=midi_path, bpm=bpm)
            
            # Save to library
            asset_id = studio_library.save_asset(
                user_id=user_id,
                kind="vocal",
                path=out_wav,
                meta={
                    "lyrics": lyrics,
                    "voice": voice,
                    "bpm": bpm,
                    "midi_path": midi_path
                }
            )
            
            return jsonify({
                "success": True,
                "message": "Vocals generated successfully",
                "wav_path": out_wav,
                "asset_id": asset_id,
                "credits_remaining": credits - 1
            })
            
        except Exception as e:
            logger.error(f"Vocal generation error: {e}")
            return jsonify({
                "success": False, 
                "error": f"Failed to generate vocals: {str(e)}"
            }), 500
        
    except Exception as e:
        logger.error(f"API vocals error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500