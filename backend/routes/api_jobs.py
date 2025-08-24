# ============================
# 📁 backend/routes/api_jobs.py
# Background job management API
# ============================
from flask import Blueprint, request, jsonify, session
from .common import safe_api, rate_limit, is_safe_path, has_allowed_ext, ALLOWED_EXTS_AUDIO, ALLOWED_EXTS_MIDI
from config import REDIS_URL, RQ_QUEUE_NAME, RQ_ENABLED
import logging

logger = logging.getLogger(__name__)

# Conditional imports for RQ (graceful fallback if Redis unavailable)
try:
    if RQ_ENABLED:
        from redis import Redis
        from rq import Queue
        from rq.job import Job
        redis_conn = Redis.from_url(REDIS_URL)
        job_queue = Queue(RQ_QUEUE_NAME, connection=redis_conn)
        RQ_AVAILABLE = True
    else:
        RQ_AVAILABLE = False
except Exception as e:
    logger.warning(f"Redis/RQ not available: {e}")
    RQ_AVAILABLE = False

def is_logged_in():
    return session.get('user_id') is not None

def get_effective_plan(user_plan, trial_active):
    if trial_active and user_plan == "bronze":
        return "gold"
    return user_plan

bp = Blueprint("api_jobs", __name__)

@bp.route("/api/jobs/vocals", methods=["POST"])
@rate_limit(per_min=10)  # Lower limit for heavy tasks
@safe_api
def jobs_vocals():
    """Queue vocal generation as background job"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        user_plan = session.get('user_plan', 'free')
        trial_active = session.get('trial_active', False)
        effective_plan = get_effective_plan(user_plan, trial_active)
        
        if effective_plan != 'max':
            return jsonify({"success": False, "error": "Mini Studio requires Max tier or trial"}), 403
        
        if not RQ_AVAILABLE:
            return jsonify({"success": False, "error": "Background jobs not available"}), 503
        
        data = request.get_json(force=True, silent=True) or {}
        lyrics = (data.get("lyrics") or "").strip()
        if not lyrics:
            return jsonify({"success": False, "error": "Missing 'lyrics'"}), 400
        
        midi_path = data.get("midi_path")
        if midi_path and not (is_safe_path(midi_path) and has_allowed_ext(midi_path, ALLOWED_EXTS_MIDI)):
            return jsonify({"success": False, "error": "Invalid MIDI path"}), 400
        
        voice = (data.get("voice") or "default").strip()
        bpm = int(data.get("bpm", 120))
        
        # Import task function
        from tasks import task_generate_vocals
        
        # Enqueue job
        job = job_queue.enqueue(task_generate_vocals, lyrics, midi_path, voice, bpm, timeout=600)
        
        return jsonify({
            "success": True,
            "message": "Vocal generation job queued",
            "job_id": job.id
        })
        
    except Exception as e:
        logger.error(f"Job queue error: {e}")
        return jsonify({"success": False, "error": "Failed to queue job"}), 500

@bp.route("/api/jobs/effects", methods=["POST"])
@rate_limit(per_min=15)
@safe_api
def jobs_effects():
    """Queue audio effects as background job"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        user_plan = session.get('user_plan', 'free')
        trial_active = session.get('trial_active', False)
        effective_plan = get_effective_plan(user_plan, trial_active)
        
        if effective_plan != 'max':
            return jsonify({"success": False, "error": "Mini Studio requires Max tier or trial"}), 403
        
        if not RQ_AVAILABLE:
            return jsonify({"success": False, "error": "Background jobs not available"}), 503
        
        data = request.get_json(force=True, silent=True) or {}
        wav_path = data.get("wav_path")
        if not wav_path or not (is_safe_path(wav_path) and has_allowed_ext(wav_path, ALLOWED_EXTS_AUDIO)):
            return jsonify({"success": False, "error": "Invalid 'wav_path'"}), 400
        
        pitch = int(data.get("pitch_semitones", 0))
        reverb = float(data.get("reverb_amount", 0.0))
        
        from tasks import task_apply_fx
        job = job_queue.enqueue(task_apply_fx, wav_path, pitch, reverb, timeout=300)
        
        return jsonify({
            "success": True,
            "message": "Effects job queued",
            "job_id": job.id
        })
        
    except Exception as e:
        logger.error(f"Effects job error: {e}")
        return jsonify({"success": False, "error": "Failed to queue effects job"}), 500

@bp.route("/api/jobs/<job_id>", methods=["GET"])
@rate_limit(per_min=120)
@safe_api
def job_status(job_id):
    """Check background job status"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        if not RQ_AVAILABLE:
            return jsonify({"success": False, "error": "Background jobs not available"}), 503
        
        try:
            job = Job.fetch(job_id, connection=redis_conn)
        except Exception:
            return jsonify({"success": False, "error": "Invalid job_id"}), 404
        
        status = job.get_status()
        result = job.result if job.is_finished else None
        error = str(job.exc_info) if job.is_failed else None
        
        return jsonify({
            "success": True,
            "job_id": job_id,
            "status": status,
            "result": result,
            "error": error,
            "progress": getattr(job.meta, 'progress', None) if hasattr(job, 'meta') else None
        })
        
    except Exception as e:
        logger.error(f"Job status error: {e}")
        return jsonify({"success": False, "error": "Failed to get job status"}), 500

@bp.route("/api/jobs/health", methods=["GET"])
@safe_api
def jobs_health():
    """Check if background job system is available"""
    return jsonify({
        "success": True,
        "rq_available": RQ_AVAILABLE,
        "queue_name": RQ_QUEUE_NAME if RQ_AVAILABLE else None,
        "message": "Background jobs ready" if RQ_AVAILABLE else "Background jobs disabled"
    })