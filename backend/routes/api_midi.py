# ===================================
# 📁 FILE: backend/routes/api_midi.py
# ===================================
from flask import Blueprint, request, jsonify, session
from studio.auto_midi import generate_midi
from studio.library import studio_library
import logging

logger = logging.getLogger(__name__)

def is_logged_in():
    return session.get('user_id') is not None

def get_effective_plan(user_plan, trial_active):
    if trial_active and user_plan == "bronze":
        return "gold"
    return user_plan

bp = Blueprint("api_midi", __name__)

@bp.route("/api/midi", methods=["POST"])
def api_midi():
    """Generate MIDI files using Auto-MIDI"""
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
        chords = data.get("chords", "Cmaj7|Am|F|G").strip()
        bpm = int(data.get("bpm", 88))
        bars = int(data.get("bars", 8))
        style = data.get("style", "arp").strip()
        
        if not chords:
            return jsonify({"success": False, "error": "Chord progression is required"}), 400
        
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
        
        # Generate MIDI
        try:
            midi_path = generate_midi(
                chords=chords,
                bpm=bpm,
                bars=bars,
                style=style
            )
            
            # Save to library
            asset_id = studio_library.save_asset(
                user_id=user_id,
                kind="midi",
                path=midi_path,
                meta={
                    "chords": chords,
                    "bpm": bpm,
                    "bars": bars,
                    "style": style
                }
            )
            
            return jsonify({
                "success": True,
                "message": "MIDI generated successfully",
                "midi_path": midi_path,
                "asset_id": asset_id,
                "credits_remaining": credits - 1
            })
            
        except Exception as e:
            logger.error(f"MIDI generation error: {e}")
            return jsonify({
                "success": False, 
                "error": f"Failed to generate MIDI: {str(e)}"
            }), 500
        
    except Exception as e:
        logger.error(f"API MIDI error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500