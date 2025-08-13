# ============================================
# 📁 backend/routes/api_mastering.py
# Professional mastering API endpoints
# ============================================
from flask import Blueprint, request, jsonify, session
from .common import safe_api, rate_limit, is_safe_path, has_allowed_ext, ALLOWED_EXTS_AUDIO
from studio.mastering import master_track, make_seamless_loop
import logging

logger = logging.getLogger(__name__)

def is_logged_in():
    return session.get('user_id') is not None

def get_effective_plan(user_plan, trial_active):
    if trial_active and user_plan == "free":
        return "max"
    return user_plan

bp = Blueprint("api_mastering", __name__)

@bp.route("/api/master", methods=["POST"])
@rate_limit(per_min=20)
@safe_api
def api_master():
    """Professional audio mastering with LUFS normalization"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        # Check access permissions
        user_plan = session.get('user_plan', 'free')
        trial_active = session.get('trial_active', False)
        effective_plan = get_effective_plan(user_plan, trial_active)
        
        if effective_plan != 'max':
            return jsonify({"success": False, "error": "Mini Studio requires Max tier or trial"}), 403
        
        data = request.get_json(force=True, silent=True) or {}
        wav_path = data.get("wav_path", "").strip()
        
        if not wav_path:
            return jsonify({"success": False, "error": "wav_path is required"}), 400
        
        if not (is_safe_path(wav_path) and has_allowed_ext(wav_path, ALLOWED_EXTS_AUDIO)):
            return jsonify({"success": False, "error": "Invalid or unsafe wav_path"}), 400
        
        # Mastering parameters with validation
        target_lufs = float(data.get("target_lufs", -14.0))
        ceiling_db = float(data.get("ceiling_db", -1.0))
        highpass_hz = data.get("highpass_hz")
        lowpass_hz = data.get("lowpass_hz")
        
        # Validate parameters
        if target_lufs < -50 or target_lufs > 0:
            return jsonify({"success": False, "error": "target_lufs must be between -50 and 0"}), 400
        
        if ceiling_db < -10 or ceiling_db > 0:
            return jsonify({"success": False, "error": "ceiling_db must be between -10 and 0"}), 400
        
        # Convert None/0 values for filters
        highpass_hz = float(highpass_hz) if highpass_hz and float(highpass_hz) > 0 else None
        lowpass_hz = float(lowpass_hz) if lowpass_hz and float(lowpass_hz) > 0 else None
        
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
        
        # Master the track
        output_path = master_track(
            wav_path=wav_path,
            target_lufs=target_lufs,
            ceiling_db=ceiling_db,
            highpass_hz=highpass_hz,
            lowpass_hz=lowpass_hz
        )
        
        return jsonify({
            "success": True,
            "message": "Track mastered successfully",
            "wav_path": output_path,
            "credits_remaining": credits - 1
        })
        
    except Exception as e:
        logger.error(f"Mastering error: {e}")
        return jsonify({"success": False, "error": "Mastering failed"}), 500

@bp.route("/api/loop", methods=["POST"])
@rate_limit(per_min=25)
@safe_api
def api_loop():
    """Create seamless loop with crossfading"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        user_plan = session.get('user_plan', 'free')
        trial_active = session.get('trial_active', False)
        effective_plan = get_effective_plan(user_plan, trial_active)
        
        if effective_plan != 'max':
            return jsonify({"success": False, "error": "Mini Studio requires Max tier or trial"}), 403
        
        data = request.get_json(force=True, silent=True) or {}
        wav_path = data.get("wav_path", "").strip()
        
        if not wav_path:
            return jsonify({"success": False, "error": "wav_path is required"}), 400
        
        if not (is_safe_path(wav_path) and has_allowed_ext(wav_path, ALLOWED_EXTS_AUDIO)):
            return jsonify({"success": False, "error": "Invalid or unsafe wav_path"}), 400
        
        # Loop parameters with validation
        loop_seconds = int(data.get("loop_seconds", 8))
        crossfade_ms = int(data.get("crossfade_ms", 120))
        
        if loop_seconds < 1 or loop_seconds > 60:
            return jsonify({"success": False, "error": "loop_seconds must be between 1 and 60"}), 400
        
        if crossfade_ms < 10 or crossfade_ms > 2000:
            return jsonify({"success": False, "error": "crossfade_ms must be between 10 and 2000"}), 400
        
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
        
        # Create seamless loop
        output_path = make_seamless_loop(
            wav_path=wav_path,
            loop_seconds=loop_seconds,
            crossfade_ms=crossfade_ms
        )
        
        return jsonify({
            "success": True,
            "message": "Seamless loop created successfully",
            "wav_path": output_path,
            "credits_remaining": credits - 1
        })
        
    except Exception as e:
        logger.error(f"Loop creation error: {e}")
        return jsonify({"success": False, "error": "Loop creation failed"}), 500