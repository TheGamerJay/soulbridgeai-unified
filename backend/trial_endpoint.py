# --- TRIAL START ENDPOINT (psycopg2 primary, SQLite fallback) -----------------
from datetime import datetime, timedelta, timezone
import json
import logging
import os

from flask import Blueprint, request, jsonify, session

# Primary: Postgres via psycopg2
try:
    import psycopg2
    import psycopg2.extras
except Exception:
    psycopg2 = None  # In case the env only has SQLite

# Fallback: SQLite
import sqlite3

bp_trial = Blueprint("trial", __name__)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///app.db")
TRIAL_DURATION_HOURS = int(os.getenv("TRIAL_DURATION_HOURS", "5"))

def _db_flavor_and_connect():
    """
    Returns (flavor, conn) where flavor ∈ {"postgres", "sqlite"}.
    """
    url = DATABASE_URL or ""
    if url.startswith("postgres://") or url.startswith("postgresql://"):
        if not psycopg2:
            raise RuntimeError("psycopg2 not available but DATABASE_URL is Postgres.")
        logging.info("Connecting to PostgreSQL with URL: %s", DATABASE_URL[:60] + "...")
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = False
        return "postgres", conn
    # SQLite fallback (accepts "sqlite:///file.db" or just path)
    if url.startswith("sqlite:///"):
        path = url.replace("sqlite:///", "", 1)
    elif url.startswith("sqlite://"):
        path = url.replace("sqlite://", "", 1)
    else:
        # Treat as a bare SQLite file path
        path = url
    logging.info("Connecting to SQLite at path: %s", path)
    conn = sqlite3.connect(path)
    conn.isolation_level = None  # We'll use explicit BEGIN/COMMIT
    return "sqlite", conn

def _get_column_types(conn):
    """Return a dict of {col_name: data_type} for the users table (Postgres only)."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name='users'
              AND column_name IN ('trial_active','trial_used_permanently','trial_warning_sent',
                                  'trial_started_at','trial_expires_at')
        """)
        return {name: dtype for (name, dtype) in cur.fetchall()}

def _ensure_trial_columns(conn, flavor: str):
    """
    Create missing columns with correct types.
    Postgres: Schema invariants guarantee correct types at startup
    SQLite:   TEXT ISO8601 timestamps + INTEGER booleans (0/1)
    """
    if flavor == "postgres":
        # Schema invariants handle this at startup - just ensure columns exist
        with conn.cursor() as cur:
            cur.execute("""
            ALTER TABLE users
              ADD COLUMN IF NOT EXISTS trial_started_at       timestamptz,
              ADD COLUMN IF NOT EXISTS trial_expires_at       timestamptz,
              ADD COLUMN IF NOT EXISTS trial_active           boolean NOT NULL DEFAULT FALSE,
              ADD COLUMN IF NOT EXISTS trial_used_permanently boolean NOT NULL DEFAULT FALSE,
              ADD COLUMN IF NOT EXISTS trial_warning_sent     boolean NOT NULL DEFAULT FALSE;
            """)
        logging.info("✅ PostgreSQL trial columns ensured (schema invariants handle types)")
    else:
        # SQLite: check pragma for existing columns
        cur = conn.cursor()
        cur.execute("BEGIN")
        cur.execute("PRAGMA table_info(users);")
        cols = {row[1] for row in cur.fetchall()}  # row[1] is name
        add_sql = []
        if "trial_started_at" not in cols:
            add_sql.append("ALTER TABLE users ADD COLUMN trial_started_at TEXT;")
        if "trial_expires_at" not in cols:
            add_sql.append("ALTER TABLE users ADD COLUMN trial_expires_at TEXT;")
        if "trial_active" not in cols:
            add_sql.append("ALTER TABLE users ADD COLUMN trial_active INTEGER NOT NULL DEFAULT 0;")
        if "trial_used_permanently" not in cols:
            add_sql.append("ALTER TABLE users ADD COLUMN trial_used_permanently INTEGER NOT NULL DEFAULT 0;")
        if "trial_warning_sent" not in cols:
            add_sql.append("ALTER TABLE users ADD COLUMN trial_warning_sent INTEGER NOT NULL DEFAULT 0;")
        for stmt in add_sql:
            cur.execute(stmt)
        cur.execute("COMMIT")
        logging.info("✅ SQLite trial columns ensured")

def _boolean_params(flavor: str, *values):
    """
    Convert Python booleans for the DB:
      - Postgres: True/False
      - SQLite:   1/0
    """
    if flavor == "sqlite":
        return tuple(1 if v else 0 for v in values)
    return values

def _timestamp_params(flavor: str, dt):
    """
    Convert datetimes for the DB:
      - Postgres: keep aware datetime (psycopg2 handles timestamptz)
      - SQLite:   store ISO string
    """
    if flavor == "sqlite":
        # Always store UTC ISO8601
        return dt.astimezone(timezone.utc).isoformat()
    # Postgres: pass datetime directly
    return dt

def _update_trial_row(conn, flavor: str, user_id: int, started_dt, expires_dt, active_bool, used_perm_bool):
    """
    Perform the UPDATE with the right placeholders and types.
    Uses strictly boolean values for PostgreSQL after schema normalization.
    """
    if flavor == "postgres":
        sql = """
        UPDATE users
        SET
          trial_started_at = %s,
          trial_expires_at = %s,
          trial_active = %s,
          trial_used_permanently = %s
        WHERE id = %s
        """
        # Strictly boolean writes - schema invariants guarantee boolean columns
        params = (
            _timestamp_params(flavor, started_dt),
            _timestamp_params(flavor, expires_dt),
            active_bool,      # Python boolean → PostgreSQL boolean
            used_perm_bool,   # Python boolean → PostgreSQL boolean
            user_id,
        )
        with conn.cursor() as cur:
            cur.execute(sql, params)
    else:
        # SQLite: use 1/0 for boolean values
        sql = """
        UPDATE users
        SET
          trial_started_at = ?,
          trial_expires_at = ?,
          trial_active = ?,
          trial_used_permanently = ?
        WHERE id = ?
        """
        b_active, b_used = _boolean_params(flavor, active_bool, used_perm_bool)
        params = (
            _timestamp_params(flavor, started_dt),
            _timestamp_params(flavor, expires_dt),
            b_active,
            b_used,
            user_id,
        )
        cur = conn.cursor()
        cur.execute("BEGIN")
        cur.execute(sql, params)
        cur.execute("COMMIT")

def _reset_trial_row(conn, flavor: str, user_id: int):
    """Optional helper to reset a user's trial entirely."""
    if flavor == "postgres":
        sql = """
        UPDATE users
        SET
          trial_active = %s,
          trial_started_at = NULL,
          trial_expires_at = NULL,
          trial_warning_sent = %s,
          trial_used_permanently = %s
        WHERE id = %s
        """
        # Strictly boolean writes - schema invariants guarantee boolean columns
        with conn.cursor() as cur:
            cur.execute(sql, (False, False, False, user_id))

    else:
        # SQLite: store booleans as 0/1 and timestamps as NULL
        sql = """
        UPDATE users
        SET
          trial_active = ?,
          trial_started_at = NULL,
          trial_expires_at = NULL,
          trial_warning_sent = ?,
          trial_used_permanently = ?
        WHERE id = ?
        """
        cur = conn.cursor()
        cur.execute("BEGIN")
        cur.execute(sql, (0, 0, 0, user_id))
        cur.execute("COMMIT")

def _init_session_trial_flags(now_utc: datetime, expires_utc: datetime, user_plan: str):
    """
    Set session flags to simulate Max features with plan-based limits.
    (You already log these; here we make sure they're synced.)
    """
    session["trial_active"] = True
    session["trial_started_at"] = now_utc.isoformat()
    session["trial_expires_at"] = expires_utc.isoformat()
    session["trial_used_permanently"] = False
    session["trial_warning_sent"] = False

    # Access gates (your earlier pattern):
    session["access_trial"] = True
    session["access_max"] = True
    session["access_growth"] = True
    session["access_free"] = True

    # Keep limits tied to actual user_plan (Free/Growth/Max)
    session["user_plan"] = user_plan or session.get("user_plan", "Free")

@bp_trial.route("/api/start-trial", methods=["POST"])
def start_trial():
    """
    Starts a 5-hour trial for the logged-in user.
    - Ensures columns exist (schema safe)
    - Writes booleans correctly (no 1/0 into boolean columns on Postgres)
    - Syncs session flags
    """
    # Basic auth check: adapt to your existing guard if needed
    user_id = session.get("user_id")
    user_email = session.get("user_email")
    user_plan = session.get("user_plan", "Free")
    if not user_id or not user_email:
        return jsonify({"ok": False, "error": "Not authenticated"}), 401

    logging.info("🎯 TRIAL START: user_id=%s, email=%s", user_id, user_email)

    now_utc = datetime.now(timezone.utc)
    expires_utc = now_utc + timedelta(hours=TRIAL_DURATION_HOURS)

    flavor = None
    conn = None
    try:
        flavor, conn = _db_flavor_and_connect()
        logging.info("🕒 TRIAL START DEBUG: TRIAL_DURATION_HOURS=%s", TRIAL_DURATION_HOURS)
        logging.info("🕒 TRIAL START DEBUG: now=%s, expires=%s", now_utc, expires_utc)
        logging.info("🕒 TRIAL START DEBUG: duration_seconds=%s", (expires_utc - now_utc).total_seconds())

        # Ensure schema (never write ints into booleans on Postgres)
        logging.info("🔍 TRIAL: Ensuring DB trial columns exist")
        _ensure_trial_columns(conn, flavor)

        # Persist to DB (correct boolean handling per flavor)
        _update_trial_row(
            conn=conn,
            flavor=flavor,
            user_id=int(user_id),
            started_dt=now_utc,
            expires_dt=expires_utc,
            active_bool=True,
            used_perm_bool=False,
        )

        # Commit for Postgres (SQLite commits inside helper)
        if flavor == "postgres":
            conn.commit()

        # Mirror in session
        _init_session_trial_flags(now_utc, expires_utc, user_plan)

        logging.info(
            "✅ TRIAL SUCCESS: user_id=%s, trial_active=True, expires_at=%s",
            user_id, expires_utc.isoformat()
        )
        # Your UI expects Max features with plan-based limits:
        return jsonify({
            "ok": True,
            "user_id": user_id,
            "trial_active": True,
            "trial_started_at": now_utc.isoformat(),
            "trial_expires_at": expires_utc.isoformat(),
            "plan_limits_from": user_plan,  # limits source (Free/Growth/Max)
            "db_flavor": flavor,
        }), 200

    except Exception as e:
        logging.exception("❌ TRIAL START FAILED")
        # IMPORTANT: Do not claim success if DB update failed.
        # But you may still set session flags if you want temporary UI unlock:
        # _init_session_trial_flags(now_utc, expires_utc, user_plan)
        # Return failure so you can fix DB state.
        return jsonify({"ok": False, "error": str(e)}), 500

    finally:
        try:
            if conn:
                if flavor == "postgres":
                    # If an error occurred before commit, roll back
                    if conn.closed == 0:
                        conn.rollback()
                conn.close()
        except Exception:
            pass

@bp_trial.route("/api/reset-trial", methods=["POST"])
def reset_trial():
    """
    Optional: resets the trial fields for the current user in DB and session.
    """
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"ok": False, "error": "Not authenticated"}), 401

    flavor = None
    conn = None
    try:
        flavor, conn = _db_flavor_and_connect()
        _ensure_trial_columns(conn, flavor)
        _reset_trial_row(conn, flavor, int(user_id))
        if flavor == "postgres":
            conn.commit()

        # Clear session flags
        for k in [
            "trial_active", "trial_started_at", "trial_expires_at",
            "trial_warning_sent", "trial_used_permanently", "access_trial"
        ]:
            session.pop(k, None)

        return jsonify({"ok": True, "user_id": user_id}), 200

    except Exception as e:
        logging.exception("❌ RESET TRIAL FAILED")
        return jsonify({"ok": False, "error": str(e)}), 500

    finally:
        try:
            if conn:
                if flavor == "postgres":
                    if conn.closed == 0:
                        conn.rollback()
                conn.close()
        except Exception:
            pass
# -----------------------------------------------------------------------------