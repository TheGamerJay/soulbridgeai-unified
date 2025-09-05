"""
CONSENT MANAGEMENT SYSTEM - Forward-Only Training Consent
Drop-in bundle for training consent across SoulBridge AI app.

Semantics:
- opt_in: start saving future drafts (no change to past)  
- opt_out: stop saving future drafts (already-saved stay)
"""

from __future__ import annotations
import os, json, time
from pathlib import Path
from flask import Blueprint, jsonify, request, session, g
import logging

logger = logging.getLogger(__name__)

consent_bp = Blueprint("consent", __name__, url_prefix="/api/consent")

# Storage directory for simple file-based consent state
ROOT = Path(os.getenv("CONSENT_DIR", "storage/consent"))
ROOT.mkdir(parents=True, exist_ok=True)

def _user_id() -> str:
    """Get current user ID from session or request headers"""
    # Try session first (SoulBridge AI uses session-based auth)
    if hasattr(g, 'user_id') and g.user_id:
        return str(g.user_id)
    
    user_id = session.get('user_id')
    if user_id:
        return str(user_id)
    
    # Fallback to headers
    user_id = request.headers.get("X-User-Id")
    if user_id:
        return str(user_id)
    
    return "anon"

def _path(uid: str) -> Path:
    return ROOT / f"{uid}.json"

def _load(uid: str) -> dict:
    """Load consent data for user"""
    p = _path(uid)
    if not p.exists():
        return {
            "status": "opt_out", 
            "ts": None, 
            "content_types": ["lyrics", "poems", "stories", "scripts", "articles", "letters"]
        }
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        logger.error(f"Error loading consent for {uid}: {e}")
        return {
            "status": "opt_out", 
            "ts": None, 
            "content_types": ["lyrics", "poems", "stories", "scripts", "articles", "letters"]
        }

def _save(uid: str, data: dict) -> None:
    """Save consent data for user"""
    try:
        _path(uid).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info(f"✅ Consent saved for user {uid}: {data['status']}")
    except Exception as e:
        logger.error(f"❌ Error saving consent for {uid}: {e}")

@consent_bp.get("/get")
def consent_get():
    """Get current consent status for user"""
    uid = _user_id()
    if uid == "anon":
        return jsonify({"error": "Authentication required"}), 401
    
    data = _load(uid)
    return jsonify(data)

@consent_bp.post("/set")
def consent_set():
    """
    Set consent status for user
    Body: { status: "opt_in" | "opt_out", content_types?: [...] }
    
    Semantics:
      - opt_in: start saving future drafts (no change to past)
      - opt_out: stop saving future drafts (already-saved stay)
    """
    uid = _user_id()
    if uid == "anon":
        return jsonify({"error": "Authentication required"}), 401
    
    body = request.get_json(silent=True) or {}
    want = (body.get("status") or "").lower()
    kinds = body.get("content_types") or ["lyrics", "poems", "stories", "scripts", "articles", "letters"]

    if want not in ("opt_in", "opt_out"):
        return jsonify(ok=False, error="Invalid status. Must be 'opt_in' or 'opt_out'"), 400

    new = {
        "status": want, 
        "ts": int(time.time()), 
        "content_types": kinds
    }
    _save(uid, new)
    
    logger.info(f"✅ User {uid} consent updated: {want}")
    return jsonify(ok=True, **new)

# Helper functions for server-side consent checking
def user_has_consent(user_id: str, kind: str) -> bool:
    """
    Check if user has consented to contribute content of a specific type
    
    Args:
        user_id: User identifier
        kind: Content type (lyrics, poems, stories, scripts, articles, letters)
    
    Returns:
        bool: True if user has opted in and content type is allowed
    """
    if not user_id or user_id == "anon":
        return False
        
    try:
        data = _load(user_id)
        is_opted_in = data.get("status") == "opt_in"
        content_types = data.get("content_types", [])
        
        # If no specific content types, assume all are allowed when opted in
        if not content_types:
            return is_opted_in
            
        return is_opted_in and kind in set(content_types)
        
    except Exception as e:
        logger.error(f"Error checking consent for user {user_id}, kind {kind}: {e}")
        return False

def get_user_consent_status(user_id: str = None) -> dict:
    """
    Get full consent status for user
    
    Args:
        user_id: User identifier (optional, will use current session if not provided)
    
    Returns:
        dict: Consent data including status, timestamp, and content types
    """
    if not user_id:
        user_id = _user_id()
        
    if user_id == "anon":
        return {"status": "opt_out", "ts": None, "content_types": []}
    
    return _load(user_id)

# Authentication middleware for consent endpoints
@consent_bp.route("/policy")
def consent_policy():
    """Serve the AI training policy page"""
    from flask import render_template
    return render_template('ai_training_policy.html')

@consent_bp.before_request
def require_auth():
    """Ensure user is authenticated for consent operations"""
    # Allow policy page without authentication
    if request.endpoint and 'policy' in request.endpoint:
        return
    
    if not session.get('logged_in'):
        return jsonify({"error": "Authentication required"}), 401