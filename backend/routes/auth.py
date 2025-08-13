# backend/routes/auth.py
from flask import Blueprint, request, session
from werkzeug.security import check_password_hash
from sqlalchemy import select
from db import SessionLocal
from models import User
from routes.common import j_ok, j_err, safe_api, rate_limit

bp = Blueprint("auth", __name__)

@bp.post("/api/login")
@rate_limit(per_min=30)
@safe_api
def login():
    data = request.get_json(force=True, silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    if not email or not password:
        return j_err("Missing email/password", 400)

    with SessionLocal() as db:
        user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
        if not user:
            return j_err("Invalid credentials", 401)
        if not check_password_hash(user.password_hash, password):
            return j_err("Invalid credentials", 401)

        # ✅ tie Flask session to your user_id
        session["user_id"] = str(user.id)
        session["user_plan"] = user.user_plan or "free"

    return j_ok(user_id=session["user_id"], plan=session["user_plan"])

@bp.post("/api/logout")
@rate_limit(per_min=60)
@safe_api
def logout():
    session.clear()
    return j_ok()