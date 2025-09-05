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
from datetime import datetime
from flask import Blueprint, jsonify, request, session, g, render_template, redirect
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

def _is_admin() -> bool:
    """Check if current user is admin using your existing Watchdog admin system"""
    try:
        # PRIMARY CHECK: Watchdog admin authentication (matches your surveillance route)
        if session.get('admin_authenticated'):
            return True
            
        # SECONDARY CHECKS: Other possible admin session flags
        admin_session_flags = [
            'is_admin',           # Generic admin flag
            'admin_logged_in',    # Alternative admin flag
            'watchdog_admin',     # Specific watchdog flag
        ]
        
        for flag in admin_session_flags:
            if session.get(flag):
                return True
        
        # TERTIARY CHECK: Admin emails (if regular user login with admin email)
        admin_emails = [
            'admin@soulbridge.ai', 
            'soulbridgeai.contact@gmail.com',
            'watchdog@soulbridge.ai'
        ]
        user_email = session.get('user_email', '').lower()
        if user_email in admin_emails:
            return True
        
        # QUATERNARY CHECK: Environment variable for admin user IDs
        user_id = _user_id()
        if user_id != "anon":
            admin_user_ids = os.getenv('ADMIN_USER_IDS', '').split(',')
            if user_id in admin_user_ids:
                return True
            
        # FINAL CHECK: Admin roles in session
        user_roles = session.get('user_roles', [])
        if 'admin' in user_roles or 'watchdog' in user_roles:
            return True
            
        return False
        
    except Exception as e:
        logger.error(f"Error checking admin status: {e}")
        return False

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
    return render_template('ai_training_policy.html')

@consent_bp.route("/admin")
def admin_dashboard():
    """Admin-only dashboard for viewing consent data and contributed content"""
    try:
        # Check if user is admin using your existing admin system
        if not _is_admin():
            # Redirect to your existing admin login
            return redirect('/admin/login?redirect=/api/consent/admin')
        
        return render_template('consent_admin.html')
        
    except Exception as e:
        logger.error(f"Error in admin dashboard: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return jsonify({
            "error": "An unexpected error occurred",
            "details": str(e)
        }), 500

@consent_bp.route("/admin/test")
def admin_test():
    """Test route to debug template rendering - REMOVE IN PRODUCTION"""
    try:
        return render_template('consent_admin.html')
    except Exception as e:
        import traceback
        return jsonify({
            "error": str(e),
            "traceback": traceback.format_exc(),
            "template_path": "consent_admin.html"
        }), 500

@consent_bp.route("/admin/debug")
def admin_debug():
    """Debug route to check admin authentication - REMOVE IN PRODUCTION"""
    try:
        user_id = _user_id()
        is_admin_result = _is_admin()
        
        # Check session data
        session_data = {
            'user_id': session.get('user_id'),
            'logged_in': session.get('logged_in'), 
            'is_admin': session.get('is_admin'),
            'admin_logged_in': session.get('admin_logged_in'),
            'watchdog_admin': session.get('watchdog_admin'),
            'admin_authenticated': session.get('admin_authenticated'),
            'user_email': session.get('user_email'),
            'user_roles': session.get('user_roles')
        }
        
        return jsonify({
            "user_id": user_id,
            "is_admin": is_admin_result,
            "session_data": session_data,
            "admin_emails_checked": ['admin@soulbridge.ai', 'soulbridgeai.contact@gmail.com', 'watchdog@soulbridge.ai'],
            "admin_user_ids_env": os.getenv('ADMIN_USER_IDS', 'NOT_SET')
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

@consent_bp.route("/admin/users")
def admin_users():
    """Get all users with their consent status (admin only)"""
    if not _is_admin():
        return jsonify({"error": "Admin access required"}), 403
    
    try:
        users_data = []
        
        # List all consent files
        for consent_file in ROOT.glob("*.json"):
            user_id = consent_file.stem
            if user_id != "anon":  # Skip anonymous user
                consent_data = _load(user_id)
                users_data.append({
                    "user_id": user_id,
                    "status": consent_data.get("status", "opt_out"),
                    "timestamp": consent_data.get("ts"),
                    "content_types": consent_data.get("content_types", []),
                    "last_updated": datetime.fromtimestamp(consent_data.get("ts", 0)).isoformat() if consent_data.get("ts") else None
                })
        
        # Sort by most recent first
        users_data.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
        
        return jsonify({
            "success": True,
            "users": users_data,
            "total_users": len(users_data),
            "opted_in": len([u for u in users_data if u["status"] == "opt_in"]),
            "opted_out": len([u for u in users_data if u["status"] == "opt_out"])
        })
        
    except Exception as e:
        logger.error(f"Error getting admin users data: {e}")
        return jsonify({"error": "Failed to retrieve user data"}), 500

@consent_bp.route("/admin/stats")  
def admin_stats():
    """Get consent statistics (admin only)"""
    if not _is_admin():
        return jsonify({"error": "Admin access required"}), 403
        
    try:
        stats = {
            "total_users": 0,
            "opted_in": 0,
            "opted_out": 0,
            "content_types": {},
            "recent_changes": []
        }
        
        # Analyze all consent files
        for consent_file in ROOT.glob("*.json"):
            user_id = consent_file.stem
            if user_id != "anon":
                consent_data = _load(user_id)
                stats["total_users"] += 1
                
                if consent_data.get("status") == "opt_in":
                    stats["opted_in"] += 1
                else:
                    stats["opted_out"] += 1
                
                # Count content types
                for content_type in consent_data.get("content_types", []):
                    stats["content_types"][content_type] = stats["content_types"].get(content_type, 0) + 1
                
                # Add to recent changes if timestamp exists
                if consent_data.get("ts"):
                    stats["recent_changes"].append({
                        "user_id": user_id,
                        "status": consent_data.get("status"),
                        "timestamp": consent_data.get("ts"),
                        "date": datetime.fromtimestamp(consent_data.get("ts")).isoformat()
                    })
        
        # Sort recent changes by most recent
        stats["recent_changes"].sort(key=lambda x: x["timestamp"], reverse=True)
        stats["recent_changes"] = stats["recent_changes"][:20]  # Last 20 changes
        
        return jsonify({
            "success": True,
            "stats": stats
        })
        
    except Exception as e:
        logger.error(f"Error getting admin stats: {e}")
        return jsonify({"error": "Failed to retrieve statistics"}), 500

@consent_bp.route("/admin/export")
def admin_export():
    """Export all consent data (admin only)"""
    if not _is_admin():
        return jsonify({"error": "Admin access required"}), 403
        
    try:
        export_data = {
            "export_date": datetime.now().isoformat(),
            "users": []
        }
        
        # Export all consent data
        for consent_file in ROOT.glob("*.json"):
            user_id = consent_file.stem
            if user_id != "anon":
                consent_data = _load(user_id)
                export_data["users"].append({
                    "user_id": user_id,
                    **consent_data
                })
        
        return jsonify({
            "success": True,
            "data": export_data
        })
        
    except Exception as e:
        logger.error(f"Error exporting consent data: {e}")
        return jsonify({"error": "Failed to export data"}), 500

@consent_bp.before_request
def require_auth():
    """Ensure user is authenticated for consent operations"""
    # Allow policy page without authentication
    if request.endpoint and 'policy' in request.endpoint:
        return
    
    # Allow admin endpoints to handle their own authentication
    if request.endpoint and 'admin' in request.endpoint:
        return
    
    if not session.get('logged_in'):
        return jsonify({"error": "Authentication required"}), 401