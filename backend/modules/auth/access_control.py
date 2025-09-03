from functools import wraps
from flask import session, request, redirect, jsonify, flash
from typing import Literal, Optional

Tier = Literal["bronze", "silver", "gold"]

TIER_ORDER = {"bronze": 0, "silver": 1, "gold": 2}

def _get_user_plan() -> Tier:
    plan = (session.get("user_plan") or "bronze").lower()
    return plan if plan in TIER_ORDER else "bronze"

def _is_trial_active() -> bool:
    # Your app already sets this; keep the name consistent
    return bool(session.get("trial_active", False))

def _effective_has_tier(required: Tier, allow_trial: bool = True) -> bool:
    """
    Users with required tier or higher pass.
    If allow_trial=True, Bronze trial users get temporary ACCESS to Silver/Gold features.
    Their actual tier stays Bronze - they just unlock feature access temporarily.
    """
    if allow_trial and _is_trial_active():
        return True

    user_plan = _get_user_plan()
    return TIER_ORDER.get(user_plan, 0) >= TIER_ORDER.get(required, 2)

def _wants_json() -> bool:
    """
    Decide if we should return JSON (API) or redirect (web page).
    We treat JSON if:
      - Content-Type is JSON, or
      - Accept prefers JSON, or
      - URL path starts with /api/
    """
    if request.path.startswith("/api/"):
        return True
    if request.is_json:
        return True
    accept = request.headers.get("Accept", "")
    return "application/json" in accept

def require_tier(required: Tier, *, allow_trial: bool = True, redirect_to: str = "/intro"):
    """
    Decorator enforcing minimum tier.
    - Bronze < Silver < Gold
    - If allow_trial is True, Bronze trial users get temporary feature access (not tier change).
    - Returns 401 if not logged in (let your requires_login handle first),
      or 403 if logged in but insufficient tier (JSON), or redirects with flash (pages).
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # If your route is not guarded by requires_login,
            # we still detect absence of user session to produce a sane 401 for APIs.
            user_id: Optional[int] = session.get("user_id")
            if not user_id:
                if _wants_json():
                    return jsonify({"ok": False, "error": "unauthorized", "code": 401}), 401
                flash("Please log in to continue.", "error")
                return redirect("/login")

            if _effective_has_tier(required, allow_trial=allow_trial):
                return func(*args, **kwargs)

            # Insufficient privileges
            if _wants_json():
                return jsonify({
                    "ok": False,
                    "error": "forbidden",
                    "required_tier": required,
                    "user_plan": _get_user_plan(),
                    "trial_active": _is_trial_active(),
                    "code": 403
                }), 403

            flash(f"Mini Studio requires {required.title()} tier access.", "error")
            return redirect(redirect_to)

        return wrapper
    return decorator

# Convenience wrappers
def require_gold_access(func=None, *, allow_trial: bool = True, redirect_to: str = "/intro"):
    """
    Use as:
      @require_gold_access
      def route(): ...

    Or:
      @require_gold_access(allow_trial=False)
    """
    def _apply(f):
        return require_tier("gold", allow_trial=allow_trial, redirect_to=redirect_to)(f)
    return _apply if func is None else _apply(func)