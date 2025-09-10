# ============ requirements.txt ============
Flask==3.0.3
Flask-SQLAlchemy==3.1.1
SQLAlchemy==2.0.32
psycopg2-binary==2.9.9
Werkzeug==3.0.3
requests==2.32.3
"""

import os, secrets, hashlib, datetime, random, string
from typing import Optional

from flask import (
    Flask, request, jsonify, session, redirect, url_for, render_template_string, make_response
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import text, UniqueConstraint

# ---------------------------------------
# App & DB configuration (Railway-ready)
# ---------------------------------------
def _normalize_db_url(url: Optional[str]) -> Optional[str]:
    if not url:
        return url
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg2://", 1)
    return url

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY") or secrets.token_hex(32)

DATABASE_URL = _normalize_db_url(os.getenv("SQLALCHEMY_DATABASE_URI") or os.getenv("DATABASE_URL"))
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL or "sqlite:///dev.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True, "pool_recycle": 300}

# Email (Resend). If missing, we log to console and still succeed.
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
RESEND_FROM    = os.getenv("RESEND_FROM", "support@soulbridgeai.com")
SITE_URL       = os.getenv("SITE_URL", "https://www.soulbridgeai.com")

try:
    import requests
except Exception:
    requests = None

db = SQLAlchemy(app)

# ---------------------------
# Models
# ---------------------------
class User(db.Model):
    __tablename__ = "users"
    id              = db.Column(db.Integer, primary_key=True)
    email           = db.Column(db.Text, unique=True, nullable=False)
    password_hash   = db.Column(db.Text, nullable=False)
    referral_code        = db.Column(db.Text, unique=True)
    referred_by_user_id  = db.Column(db.Integer)
    created_at      = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at      = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow,
                                onupdate=datetime.datetime.utcnow)

class PasswordResetToken(db.Model):
    __tablename__ = "password_reset_tokens"
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, nullable=False, index=True)
    token_hash = db.Column(db.Text, unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    used_at    = db.Column(db.DateTime, nullable=True)
    request_ip = db.Column(db.Text, nullable=True)
    request_ua = db.Column(db.Text, nullable=True)

class Referral(db.Model):
    __tablename__ = "referrals"
    id                 = db.Column(db.Integer, primary_key=True)
    referrer_user_id   = db.Column(db.Integer, nullable=False)
    referee_user_id    = db.Column(db.Integer, nullable=False)
    created_at         = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    __table_args__ = (UniqueConstraint("referee_user_id", name="referrals_referee_unique"),)

with app.app_context():
    db.create_all()

# ---------------------------
# Helpers
# ---------------------------
def _now() -> datetime.datetime:
    return datetime.datetime.utcnow()

def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def _send_email(to_email: str, subject: str, html: str, text_body: Optional[str] = None) -> bool:
    try:
        if not RESEND_API_KEY or not requests:
            print("[EMAIL][DEV] Would send to:", to_email)
            print("[EMAIL][SUBJECT]", subject)
            print("[EMAIL][HTML]", html)
            if text_body:
                print("[EMAIL][TEXT]", text_body)
            return True
        r = requests.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"},
            json={"from": RESEND_FROM, "to": [to_email], "subject": subject, "html": html, "text": text_body or ""},
            timeout=10
        )
        ok = r.status_code in (200, 202)
        if not ok:
            print("[EMAIL][ERROR] Status:", r.status_code, "Body:", r.text)
        return ok
    except Exception as e:
        print("[EMAIL][ERROR] Exception:", repr(e))
        return False

def _current_user() -> Optional[User]:
    uid = session.get("user_id")
    return User.query.get(uid) if uid else None

# =======================================================
#            Forgot / Reset Password  (API + HTML)
# =======================================================
RESET_TOKEN_TTL_MINUTES = 60

def _reset_email_html(reset_url: str) -> str:
    return f"""
    <div style="font-family:system-ui,-apple-system,Segoe UI,Roboto">
      <h2>Password reset</h2>
      <p>Click the button below to set a new password. This link expires in {RESET_TOKEN_TTL_MINUTES} minutes.</p>
      <p><a href="{reset_url}" style="display:inline-block;background:#2563eb;color:#fff;padding:10px 16px;border-radius:8px;text-decoration:none">Reset Password</a></p>
      <p>If the button doesn't work, paste this URL in your browser:</p>
      <code>{reset_url}</code>
    </div>
    """

@app.post("/auth/forgot-password")
def api_forgot_password():
    """JSON or form. Always 200 generic to avoid enumeration."""
    generic = {"ok": True, "message": "If that email exists, a reset link was sent."}
    try:
        if request.is_json:
            email = (request.get_json(silent=True) or {}).get("email", "")
        else:
            email = request.form.get("email", "")
        email = email.strip().lower()
        if not email:
            return jsonify(generic), 200

        user = User.query.filter(User.email.ilike(email)).first()
        if not user:
            return jsonify(generic), 200

        raw_token  = secrets.token_urlsafe(32)
        token_hash = _sha256(raw_token)
        expires_at = _now() + datetime.timedelta(minutes=RESET_TOKEN_TTL_MINUTES)
        db.session.add(PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
            request_ip=request.headers.get("X-Forwarded-For", request.remote_addr or ""),
            request_ua=request.headers.get("User-Agent", "")
        ))
        db.session.commit()

        reset_url = f"{SITE_URL}/reset-password?token={raw_token}"
        _send_email(
            to_email=user.email,
            subject="Reset your password",
            html=_reset_email_html(reset_url),
            text_body=f"Reset your password: {reset_url}\nLink expires in {RESET_TOKEN_TTL_MINUTES} minutes."
        )
        return jsonify(generic), 200
    except Exception as e:
        print("[PW-RESET][ERROR][forgot]", repr(e))
        return jsonify(generic), 200

@app.get("/auth/reset-password/verify")
def api_verify_reset_token():
    try:
        token = (request.args.get("token") or "").strip()
        if not token:
            return jsonify({"ok": False, "error": "Invalid or expired token"}), 400
        row = PasswordResetToken.query.filter_by(token_hash=_sha256(token)).first()
        if not row or row.used_at is not None or row.expires_at < _now():
            return jsonify({"ok": False, "error": "Invalid or expired token"}), 400
        return jsonify({"ok": True}), 200
    except Exception as e:
        print("[PW-RESET][ERROR][verify]", repr(e))
        return jsonify({"ok": False, "error": "Invalid or expired token"}), 400

@app.post("/auth/reset-password")
def api_reset_password():
    """JSON or form. Returns JSON."""
    try:
        if request.is_json:
            data = request.get_json(silent=True) or {}
            token   = (data.get("token") or "").strip()
            passwd  = (data.get("password") or "").strip()
            confirm = (data.get("confirm") or "").strip()
        else:
            token   = (request.form.get("token") or "").strip()
            passwd  = (request.form.get("password") or "").strip()
            confirm = (request.form.get("confirm") or "").strip()

        if not token or not passwd or not confirm:
            return jsonify({"ok": False, "error": "Missing fields"}), 400
        if passwd != confirm:
            return jsonify({"ok": False, "error": "Passwords do not match"}), 400
        if len(passwd) < 8:
            return jsonify({"ok": False, "error": "Password must be at least 8 characters"}), 400

        row = PasswordResetToken.query.filter_by(token_hash=_sha256(token)).first()
        if not row or row.used_at is not None or row.expires_at < _now():
            return jsonify({"ok": False, "error": "Invalid or expired token"}), 400

        db.session.execute(text("UPDATE users SET password_hash = :ph WHERE id = :uid"),
                           {"ph": generate_password_hash(passwd), "uid": row.user_id})
        db.session.execute(text("UPDATE password_reset_tokens SET used_at = :now WHERE id = :id"),
                           {"now": _now(), "id": row.id})
        db.session.execute(text("""
            UPDATE password_reset_tokens SET used_at = COALESCE(used_at, :now)
            WHERE user_id = :uid AND used_at IS NULL
        """), {"uid": row.user_id, "now": _now()})
        db.session.commit()

        return jsonify({"ok": True, "message": "Password updated successfully"}), 200
    except Exception as e:
        print("[PW-RESET][ERROR][reset]", repr(e))
        return jsonify({"ok": False, "error": "An unexpected error occurred"}), 500

# --- HTML pages for Forgot/Reset (server-rendered) ---
BASE_CSS = """
*{box-sizing:border-box} body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;background:#f8fafc;color:#0f172a;margin:0}
.container{max-width:520px;margin:40px auto;padding:16px}
.card{background:#fff;border:1px solid #e5e7eb;border-radius:12px;padding:16px;box-shadow:0 1px 2px rgba(0,0,0,.04)}
h1,h2,h3{margin:0 0 12px} .muted{color:#64748b;font-size:14px}
input,button{font:inherit} input{width:100%;padding:10px;border:1px solid #d1d5db;border-radius:10px;margin:8px 0}
.btn{padding:10px 12px;border-radius:10px;border:1px solid #2563eb;background:#2563eb;color:#fff;cursor:pointer}
.link{color:#2563eb;text-decoration:none}
.notice{margin-top:8px}
code{background:#f1f5f9;border-radius:6px;padding:2px 6px}
.row{display:flex;gap:8px;align-items:center}
"""

TEMPLATE_BASE = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>{{ title }}</title>
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <style>{{ css }}</style>
  </head>
  <body>
    <div class="container">
      <div class="card">
        {% block content %}{% endblock %}
      </div>
      <div class="muted" style="margin-top:12px">
        <a class="link" href="{{ url_for('home') }}">Home</a>
        &nbsp;•&nbsp;
        <a class="link" href="{{ url_for('forgot_password_page') }}">Forgot Password</a>
        &nbsp;•&nbsp;
        <a class="link" href="{{ url_for('reset_password_page') }}">Reset Password</a>
        &nbsp;•&nbsp;
        <a class="link" href="{{ url_for('referrals_page') }}">Referrals</a>
        &nbsp;•&nbsp;
        <a class="link" href="{{ url_for('dev_login_page') }}">Dev Login</a>
      </div>
    </div>
  </body>
</html>
"""

@app.get("/")
def home():
    html = """
    {% extends base %}
    {% block content %}
    <h2>Welcome</h2>
    <p class="muted">This app includes Forgot/Reset Password and Referrals. Uses PostgreSQL via SQLAlchemy.</p>
    <ul>
      <li><a class="link" href="{{ url_for('forgot_password_page') }}">Forgot Password (HTML)</a></li>
      <li><a class="link" href="{{ url_for('reset_password_page') }}">Reset Password (HTML)</a></li>
      <li><a class="link" href="{{ url_for('referrals_page') }}">Referrals (HTML)</a></li>
      <li><a class="link" href="{{ url_for('dev_login_page') }}">Dev Login (HTML)</a></li>
    </ul>
    {% endblock %}
    """
    return render_template_string(html, base=TEMPLATE_BASE, css=BASE_CSS, title="Home")

@app.get("/forgot-password")
def forgot_password_page():
    html = """
    {% extends base %}
    {% block content %}
      <h3>Forgot your password?</h3>
      <form method="POST" action="{{ url_for('api_forgot_password') }}">
        <input name="email" type="email" placeholder="you@example.com" required />
        <button class="btn">Send reset link</button>
      </form>
      <div class="muted">You'll get the same confirmation whether or not the email exists.</div>
    {% endblock %}
    """
    return render_template_string(html, base=TEMPLATE_BASE, css=BASE_CSS, title="Forgot Password")

@app.get("/reset-password")
def reset_password_page():
    token = request.args.get("token", "").strip()
    html = """
    {% extends base %}
    {% block content %}
      <h3>Set a new password</h3>
      {% if token %}
        <form method="POST" action="{{ url_for('api_reset_password') }}">
          <input type="hidden" name="token" value="{{ token }}" />
          <input name="password" type="password" placeholder="New password (min 8 chars)" minlength="8" required />
          <input name="confirm" type="password" placeholder="Confirm password" minlength="8" required />
          <button class="btn">Update password</button>
        </form>
      {% else %}
        <div class="muted">Missing token. Use your email link.</div>
      {% endif %}
    {% endblock %}
    """
    return render_template_string(html, base=TEMPLATE_BASE, css=BASE_CSS, title="Reset Password", token=token)

# =======================================================
#                     Referrals (API + HTML)
# =======================================================
REFERRAL_UNLOCK_THRESHOLDS = [2, 4, 6, 8, 10]
REFERRAL_CODE_LENGTH = 8

def _generate_referral_code(n: int = REFERRAL_CODE_LENGTH) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(random.choice(alphabet) for _ in range(n))

def _ensure_user_has_code(user: User) -> None:
    if user.referral_code:
        return
    while True:
        code = _generate_referral_code()
        exists = User.query.filter_by(referral_code=code).first()
        if not exists:
            user.referral_code = code
            db.session.commit()
            break

def _referral_stats(user_id: int) -> dict:
    total = db.session.query(Referral).filter_by(referrer_user_id=user_id).count()
    unlocked = [t for t in REFERRAL_UNLOCK_THRESHOLDS if total >= t]
    nxt = None
    for t in REFERRAL_UNLOCK_THRESHOLDS:
        if total < t:
            nxt = {"at": t, "remaining": t - total}
            break
    return {"total": total, "unlocked": unlocked, "next_unlock": nxt}

@app.get("/api/referrals/me")
def api_referrals_me():
    user = _current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    _ensure_user_has_code(user)
    return jsonify({
        "code": user.referral_code,
        "referred_by_user_id": user.referred_by_user_id,
        "stats": _referral_stats(user.id)
    }), 200

@app.post("/api/referrals/submit")
def api_referrals_submit():
    user = _current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    code = ((request.get_json(silent=True) or {}).get("code") if request.is_json else request.form.get("code")) or ""
    code = code.strip().upper()
    if not code:
        return jsonify({"error": "No code provided"}), 400

    if user.referred_by_user_id:
        stats = _referral_stats(user.referred_by_user_id)
        return jsonify({
            "ok": True, "message": "You have already used a referral code.",
            "referrer_user_id": user.referred_by_user_id, "stats_for_referrer": stats
        }), 200

    referrer = User.query.filter_by(referral_code=code).first()
    if not referrer:
        return jsonify({"error": "Invalid referral code"}), 404
    if referrer.id == user.id:
        return jsonify({"error": "You cannot use your own referral code"}), 400

    exists = Referral.query.filter_by(referee_user_id=user.id).first()
    if exists:
        if not user.referred_by_user_id:
            user.referred_by_user_id = referrer.id
            db.session.commit()
        stats = _referral_stats(referrer.id)
        return jsonify({
            "ok": True, "message": "Referral already recorded.",
            "referrer_user_id": referrer.id, "stats_for_referrer": stats
        }), 200

    db.session.add(Referral(referrer_user_id=referrer.id, referee_user_id=user.id))
    user.referred_by_user_id = referrer.id
    db.session.commit()

    stats = _referral_stats(referrer.id)
    return jsonify({
        "ok": True, "message": "Referral applied successfully.",
        "referrer_user_id": referrer.id, "stats_for_referrer": stats
    }), 200

# HTML page for referrals
@app.route("/referrals", methods=["GET", "POST"])
def referrals_page():
    user = _current_user()
    if not user:
        return redirect(url_for("dev_login_page"))

    message = ""
    if request.method == "POST":
        code = (request.form.get("code") or "").strip().upper()
        if not code:
            message = "Enter a code first."
        else:
            # Call the same logic as API
            if user.referred_by_user_id:
                message = "You have already used a referral code."
            else:
                referrer = User.query.filter_by(referral_code=code).first()
                if not referrer:
                    message = "Invalid referral code."
                elif referrer.id == user.id:
                    message = "You cannot use your own referral code."
                else:
                    exists = Referral.query.filter_by(referee_user_id=user.id).first()
                    if exists and not user.referred_by_user_id:
                        user.referred_by_user_id = referrer.id
                        db.session.commit()
                        message = "Referral already recorded."
                    else:
                        db.session.add(Referral(referrer_user_id=referrer.id, referee_user_id=user.id))
                        user.referred_by_user_id = referrer.id
                        db.session.commit()
                        message = "Referral applied successfully."

    _ensure_user_has_code(user)
    stats = _referral_stats(user.id)
    share_link = f"{SITE_URL}/?ref={user.referral_code}" if user.referral_code else ""
    html = """
    {% extends base %}
    {% block content %}
      <h3>Referral Program</h3>
      <div class="muted">Share your code or link; one referral per user, no self-referrals.</div>

      <h4 style="margin-top:12px">Your Referral Code</h4>
      <div class="row">
        <code>{{ code or "—" }}</code>
        {% if share_link %}
          <span class="muted">Share link:</span> <code>{{ share_link }}</code>
        {% endif %}
      </div>

      <h4 style="margin-top:12px">Enter a Friend's Code</h4>
      {% if referred_by %}
        <div class="muted">A referral is already linked to your account. Thanks!</div>
      {% else %}
        <form method="POST">
          <input name="code" placeholder="ABCD1234" maxlength="12" />
          <button class="btn">Apply</button>
        </form>
      {% endif %}

      <h4 style="margin-top:12px">Your Progress</h4>
      <div>Total referrals: <b>{{ stats.total }}</b></div>
      <div>Unlocked thresholds: <b>{{ stats.unlocked|join(", ") if stats.unlocked else "none yet" }}</b></div>
      {% if stats.next_unlock %}
        <div>Next unlock at <b>{{ stats.next_unlock.at }}</b> (need <b>{{ stats.next_unlock.remaining }}</b> more)</div>
      {% else %}
        <div>All current thresholds unlocked 🎉</div>
      {% endif %}

      {% if message %}
        <div class="notice">{{ message }}</div>
      {% endif %}
    {% endblock %}
    """
    return render_template_string(
        html, base=TEMPLATE_BASE, css=BASE_CSS, title="Referrals",
        code=user.referral_code, share_link=share_link,
        referred_by=user.referred_by_user_id, stats=stats, message=message
    )

# =======================================================
#            Dev login/logout (HTML) for testing
# =======================================================
@app.route("/__dev/login", methods=["GET", "POST"])
def dev_login_page():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = (request.form.get("password") or "").strip()
        if not email or not password:
            msg = "Email and password are required."
        else:
            user = User.query.filter(User.email.ilike(email)).first()
            if not user:
                user = User(email=email, password_hash=generate_password_hash(password))
                db.session.add(user)
                db.session.commit()
            elif not check_password_hash(user.password_hash, password):
                # For dev convenience, update to the provided password if wrong.
                user.password_hash = generate_password_hash(password)
                db.session.commit()
            session["user_id"] = user.id
            return redirect(url_for("referrals_page"))
    else:
        msg = ""

    html = """
    {% extends base %}
    {% block content %}
      <h3>Dev Login</h3>
      <form method="POST">
        <input name="email" type="email" placeholder="you@example.com" required />
        <input name="password" type="password" placeholder="password" required />
        <button class="btn">Login</button>
      </form>
      {% if msg %}<div class="notice">{{ msg }}</div>{% endif %}
      <div class="muted" style="margin-top:8px">Creates the user if missing. Dev-only.</div>
    {% endblock %}
    """
    return render_template_string(html, base=TEMPLATE_BASE, css=BASE_CSS, title="Dev Login", msg=msg)

@app.post("/__dev/logout")
def dev_logout():
    session.pop("user_id", None)
    return redirect(url_for("home"))

# =======================================================
#                    Health check
# =======================================================
@app.get("/__health/db")
def db_health():
    try:
        engine = str(db.engine.url)
        db.session.execute(text("SELECT 1"))
        try:
            db.session.execute(text("SELECT 1 FROM users LIMIT 1"))
            users_ok = True
        except Exception:
            users_ok = False
        return jsonify({"ok": True, "engine": engine, "users_table": users_ok}), 200
    except Exception as e:
        return jsonify({"ok": False, "error": repr(e)}), 500

# =======================================================
#                    App runner
# =======================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=True)