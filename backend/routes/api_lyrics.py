# ====================================
# 📁 FILE: backend/routes/api_lyrics.py
# ====================================
from flask import Blueprint, request, jsonify, session
from studio.inspiration_writer import write_lyrics
from studio.library import studio_library
import logging

logger = logging.getLogger(__name__)

def is_logged_in():
    return session.get('user_id') is not None

def get_effective_plan(user_plan, trial_active):
    if trial_active and user_plan == "free":
        return "max"
    return user_plan

bp = Blueprint("api_lyrics", __name__)

@bp.route("/api/lyrics", methods=["POST"])
def api_lyrics():
    """Generate song lyrics using InspirationWriter"""
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
        theme = data.get("theme", "love").strip()
        mood = data.get("mood", "emotional").strip()
        lang = data.get("lang", "en").strip()
        syllables = int(data.get("syllables", 10))
        
        if not theme:
            return jsonify({"success": False, "error": "Theme is required"}), 400
        
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
        
        # Generate lyrics
        try:
            lyrics_content = write_lyrics(
                theme=theme,
                mood=mood,
                lang=lang,
                syllables=syllables
            )
            
            # Save to library as text file
            import os
            try:
                from config import PATHS
                tmp_dir = PATHS["tmp"]
            except ImportError:
                tmp_dir = "tmp"
                os.makedirs(tmp_dir, exist_ok=True)
            
            from studio.utils import new_id
            lyrics_file = os.path.join(tmp_dir, f"{new_id()}_lyrics.txt")
            with open(lyrics_file, 'w', encoding='utf-8') as f:
                f.write(lyrics_content)
            
            asset_id = studio_library.save_asset(
                user_id=user_id,
                kind="lyrics",
                path=lyrics_file,
                meta={
                    "theme": theme,
                    "mood": mood,
                    "language": lang,
                    "syllables": syllables
                }
            )
            
            return jsonify({
                "success": True,
                "message": "Lyrics generated successfully",
                "lyrics": lyrics_content,
                "asset_id": asset_id,
                "credits_remaining": credits - 1
            })
            
        except Exception as e:
            logger.error(f"Lyrics generation error: {e}")
            return jsonify({
                "success": False, 
                "error": f"Failed to generate lyrics: {str(e)}"
            }), 500
        
    except Exception as e:
        logger.error(f"API lyrics error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500