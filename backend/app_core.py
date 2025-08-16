# app_core.py
# SoulBridgeAI – Plug-and-Play (Block A, FULL)
# Plans/Trial + Trainer Credits + Stripe + Disclaimer gate + Library/Community
# + Cron-safe monthly reset + optional trial cleanup

import os, secrets, shutil, subprocess, tempfile
from datetime import datetime, timedelta, timezone

from flask import Flask, request, session, redirect, url_for, render_template_string, send_file, abort, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy

# ---------- Optional deps ----------
try:
    import stripe
except Exception:
    stripe = None

try:
    import numpy as np, librosa, soundfile as sf
except Exception:
    np = None

# ---------- App/DB ----------
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY') or os.urandom(32)

# Use existing database configuration if available
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL:
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///soulbridgeai.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
LIBRARY_DIR = os.path.join(DATA_DIR, 'library')
COMMUNITY_DIR = os.path.join(DATA_DIR, 'community')
for d in (DATA_DIR, LIBRARY_DIR, COMMUNITY_DIR):
    os.makedirs(d, exist_ok=True)

# ---------- Stripe (Top-ups: $3.50 → +350 credits) ----------
STRIPE_SK = os.getenv('STRIPE_SECRET_KEY')
STRIPE_PK = os.getenv('STRIPE_PUBLIC_KEY')
PRICE_350 = os.getenv('TRAINER_PRICE_350')   # Stripe Price ID for $3.50
if stripe and STRIPE_SK:
    stripe.api_key = STRIPE_SK

# ---------- Admin token for cron-protected endpoints ----------
ADMIN_TOKEN = os.getenv('ADMIN_TOKEN', '')  # set a strong random value

# ---------- Credit rules ----------
MONTHLY_CREDITS_MAX = 650       # for Max subscribers
TRIAL_CREDITS = 60              # for 5-hour Max trial
CREDIT_COST_PER_SONG = 1        # 1 credit per new output (trim is free)

# ---------- Models ----------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), unique=True, nullable=False)
    plan = db.Column(db.String(20), default='free')   # free | growth | max
    trainer_credits = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    disclaimer_accepted_at = db.Column(db.DateTime, nullable=True)
    used_max_trial = db.Column(db.Boolean, default=False)
    last_credit_reset = db.Column(db.Date, nullable=True)  # month-by-month reset marker
    
    # Additional fields for compatibility with existing system
    password_hash = db.Column(db.String(255), nullable=True)
    referrals = db.Column(db.Integer, default=0)
    trial_active = db.Column(db.Boolean, default=False)
    trial_started_at = db.Column(db.DateTime, nullable=True)
    trial_expires_at = db.Column(db.DateTime, nullable=True)
    trial_used_permanently = db.Column(db.Boolean, default=False)

class MaxTrial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    expires_at = db.Column(db.DateTime, nullable=False)
    credits_granted = db.Column(db.Integer, default=TRIAL_CREDITS)
    active = db.Column(db.Boolean, default=True)

class TrainerPurchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    credits = db.Column(db.Integer, nullable=False)
    stripe_session_id = db.Column(db.String(255), unique=True)
    paid = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Song(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    title = db.Column(db.String(200))
    tags = db.Column(db.String(200))
    file_path = db.Column(db.String(500))
    likes = db.Column(db.Integer, default=0)
    play_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def mp3_path(self):
        base, _ = os.path.splitext(self.file_path)
        return base + '.mp3'

with app.app_context():
    db.create_all()

# ---------- Helpers ----------
def today_utc_date():
    return datetime.now(timezone.utc).date()

def current_user():
    uid = session.get('user_id') or session.get('uid')  # Support both session keys
    return db.session.get(User, uid) if uid else None

def login_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrap(*a, **k):
        if not current_user():
            return redirect(url_for('login', next=request.path))
        return fn(*a, **k)
    return wrap

def has_active_max_trial(user):
    if not user: return False
    trial = MaxTrial.query.filter_by(user_id=user.id, active=True).order_by(MaxTrial.id.desc()).first()
    if not trial: return False
    if trial.expires_at <= datetime.utcnow():
        trial.active = False
        db.session.commit()
        return False
    return True

def is_max_allowed(user):
    return bool(user and (user.plan == 'max' or has_active_max_trial(user)))

def add_trainer_credits(user, amount):
    user.trainer_credits = int(user.trainer_credits or 0) + int(amount or 0)
    db.session.commit()

def ensure_monthly_credits(user):
    """
    Resets monthly credits to 650 for Max subscribers once per calendar month.
    Triggered when visiting pages (soft auto-reset). Cron route below provides a hard reset.
    """
    if not user or user.plan != 'max':
        return
    today = today_utc_date()
    if (user.last_credit_reset is None) or (user.last_credit_reset.year != today.year) or (user.last_credit_reset.month != today.month):
        user.trainer_credits = MONTHLY_CREDITS_MAX
        user.last_credit_reset = today
        db.session.commit()

def ffmpeg_ok():
    try:
        subprocess.run(['ffmpeg', '-version'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False

def _check_admin_token():
    token = request.headers.get('X-Admin-Token') or request.args.get('token') or ''
    if not ADMIN_TOKEN or token != ADMIN_TOKEN:
        abort(403, description="Forbidden: invalid admin token")

# ---------- Auth routes (integrate with existing system) ----------
@app.route('/music/login', methods=['GET','POST'])
def music_login():
    if request.method == 'POST':
        email = (request.form.get('email') or '').strip().lower()
        if not email: return 'Email required', 400
        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(email=email, plan='free', trainer_credits=0)
            db.session.add(user); db.session.commit()
        session['uid'] = user.id
        session['user_id'] = user.id  # Compatibility with existing system
        session['user_email'] = user.email
        return redirect(request.args.get('next') or url_for('music_home'))
    return render_template_string('''
    <h2>Music Studio Login</h2>
    <form method="post">
      <input name="email" placeholder="you@example.com" required>
      <button>Login</button>
    </form>
    ''')

@app.route('/music/logout')
@login_required
def music_logout():
    session.pop('uid', None)
    return redirect(url_for('music_login'))

# ---------- Plans + Trial + Credit checkout ----------
@app.route('/music')
@login_required
def music_home():
    u = current_user()
    ensure_monthly_credits(u)
    trial = MaxTrial.query.filter_by(user_id=u.id, active=True).first()
    return render_template_string('''
<!doctype html><meta charset="utf-8">
<title>SoulBridge AI – Music Studio</title>
<style>
body{font-family:system-ui;background:#0b0f17;color:#e6f1ff;padding:24px}
.card{background:#111827;border:1px solid #1f2937;border-radius:12px;padding:16px;display:inline-block;margin:8px;width:300px}
a.btn,button{background:#06b6d4;color:#001018;border:none;padding:10px 14px;border-radius:8px;text-decoration:none;cursor:pointer}
.muted{color:#9aa8bd}.row{display:flex;gap:12px;flex-wrap:wrap}
.top{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}
</style>
<div class="top">
  <div>
    <div>Logged in as <b>{{u.email}}</b></div>
    <div class="muted">Plan: <b>{{u.plan}}</b> • Trainer Time: <b>{{u.trainer_credits}}</b> credits</div>
  </div>
  <div>
    <a class="btn" href="{{url_for('library')}}">🎵 Library</a>
    <a class="btn" href="{{url_for('community')}}">🌐 Community</a>
    {% if allowed %}<a class="btn" href="{{url_for('mini_studio')}}">🎶 Mini Studio</a>{% else %}<span class="muted">(Mini Studio: Max or 5-hr Max Trial)</span>{% endif %}
    <a class="btn" href="/">← Back to Main</a>
    <a class="btn" style="background:#ef4444;color:#fff" href="{{url_for('music_logout')}}">Logout</a>
  </div>
</div>

<h1>Music Studio Plans</h1>
<div class="row">
  <div class="card"><h3>Free</h3><p>Basic chat features. No Mini Studio.</p></div>
  <div class="card"><h3>Growth</h3><p>More features. No Mini Studio.</p></div>
  <div class="card">
    <h3>Max</h3><p>Full features + Mini Studio access.</p>
    {% if u.plan != 'max' %}
      <form method="post" action="{{url_for('upgrade_plan')}}"><input type="hidden" name="plan" value="max"><button>Upgrade to Max</button></form>
    {% else %}<div class="muted">You're on Max. Monthly credits reset automatically.</div>{% endif %}
    <div style="margin-top:10px">
      {% if not u.used_max_trial and not trial_active %}
        <form method="post" action="{{url_for('start_max_trial')}}"><button>Start 5-Hour Max Trial (60 credits)</button></form>
        <div class="muted">Mini Studio + 60 credits for 5 hours. Persists across logouts until expiry.</div>
      {% elif trial_active %}
        <div class="muted">Max Trial active until {{trial_expiry}}.</div>
      {% else %}
        <div class="muted">Max Trial already used.</div>
      {% endif %}
    </div>
  </div>
</div>

<h2 style="margin-top:24px">Buy Trainer Time</h2>
<div class="row">
  <form class="card" method="post" action="{{url_for('create_checkout_session')}}">
    <h3>+350 credits</h3>
    <input type="hidden" name="credits" value="350">
    <button>Buy for $3.50</button>
    <div class="muted" style="margin-top:6px">Instantly added after payment.</div>
  </form>
</div>
''', u=u, allowed=is_max_allowed(u), trial_active=bool(trial and trial.active),
       trial_expiry=(trial.expires_at.strftime('%Y-%m-%d %H:%M') if trial and trial.active else None))

@app.route('/music/upgrade', methods=['POST'])
@login_required
def upgrade_plan():
    plan = request.form.get('plan')
    if plan not in ('free','growth','max'): return 'bad plan', 400
    u = current_user(); u.plan = plan; db.session.commit()
    # On upgrading to Max, assign monthly credits immediately
    if plan == 'max':
        ensure_monthly_credits(u)
    return redirect(url_for('music_home'))

@app.route('/music/trial/max/start', methods=['POST'])
@login_required
def start_max_trial():
    u = current_user()
    if u.used_max_trial: return 'Trial already used', 400
    expires = datetime.now(timezone.utc) + timedelta(hours=5)  # exact 5h in UTC
    trial = MaxTrial(user_id=u.id, expires_at=expires, active=True, credits_granted=TRIAL_CREDITS)
    db.session.add(trial)
    add_trainer_credits(u, TRIAL_CREDITS)    # grant credits on trial start
    u.used_max_trial = True
    db.session.commit()
    return '', 204

@app.route('/music/billing/checkout', methods=['POST'])
@login_required
def create_checkout_session():
    if not stripe: return 'Stripe not installed', 500
    credits = int(request.form.get('credits','0'))
    if credits != 350: return 'Invalid top-up', 400
    if not PRICE_350: return 'Missing Stripe price id TRAINER_PRICE_350', 500
    u = current_user()
    success = url_for('billing_success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}'
    cancel  = url_for('music_home', _external=True)
    checkout = stripe.checkout.Session.create(
        mode='payment',
        line_items=[{'price': PRICE_350, 'quantity': 1}],
        success_url=success, cancel_url=cancel,
        metadata={'user_id': u.id, 'credits': credits}
    )
    db.session.add(TrainerPurchase(user_id=u.id, credits=credits, stripe_session_id=checkout.id, paid=False))
    db.session.commit()
    return redirect(checkout.url)

@app.route('/music/billing/success')
@login_required
def billing_success():
    if not stripe: return 'Stripe not installed', 500
    session_id = request.args.get('session_id'); 
    if not session_id: return 'Missing session_id', 400
    sess = stripe.checkout.Session.retrieve(session_id, expand=['payment_intent','line_items'])
    if sess.payment_status != 'paid': return 'Payment not completed', 400
    pr = TrainerPurchase.query.filter_by(stripe_session_id=session_id).first()
    if pr and not pr.paid:
        pr.paid = True; db.session.commit()
        user = db.session.get(User, pr.user_id)
        add_trainer_credits(user, pr.credits)
    return render_template_string('<h2>✅ Payment success</h2><a href="/music">Back</a>')

# ---------- Disclaimer / Mini Studio gate ----------
DISCLAIMER_HTML = """
<h2>Mini Studio Disclaimer</h2>
<p>By using Mini Studio, you confirm you have the rights to any material you upload or transform and agree not to infringe third-party rights. Do not attempt to recreate identifiable artists. Output may transform vocals and audio via DSP/ML; use at your own risk.</p>
<form method="post" action="/music/mini-studio/disclaimer/accept"><button>Accept & Continue</button></form>
"""

@app.route('/music/mini-studio')
@login_required
def mini_studio():
    u = current_user()
    ensure_monthly_credits(u)
    if not is_max_allowed(u): return 'Mini Studio is Max or Max Trial only.', 403
    if not u.disclaimer_accepted_at: return render_template_string(DISCLAIMER_HTML)
    return render_template_string('''
    <h1>🎶 Mini Studio</h1>
    <div>
      <a class="btn" href="{{url_for('library')}}">Your Library</a>
      <a class="btn" href="{{url_for('community')}}">Community</a>
      <a class="btn" href="{{url_for('music_home')}}">Plans</a>
      <form style="display:inline" method="post" action="{{url_for('create_checkout_session')}}">
        <input type="hidden" name="credits" value="350"><button class="btn">Buy +350 Credits ($3.50)</button>
      </form>
    </div>
    <p class="muted">Each new output costs 1 credit. Trim is free. Song max length: 4:30. Prompts/lyrics ≤ 3,500 chars.</p>
    
    <h2>Audio Tools</h2>
    <div class="card">
      <h3>Upload Audio</h3>
      <form method="post" action="/api/song/upload" enctype="multipart/form-data">
        <input type="file" name="audio" accept="audio/*" required>
        <input name="title" placeholder="Song title" required>
        <input name="tags" placeholder="Tags (optional)">
        <button>Upload</button>
      </form>
    </div>
    ''')

@app.route('/music/mini-studio/disclaimer/accept', methods=['POST'])
@login_required
def accept_disclaimer():
    u = current_user()
    u.disclaimer_accepted_at = datetime.utcnow()
    db.session.commit()
    return redirect(url_for('mini_studio'))

# ---------- Library ----------
@app.route('/music/library')
@login_required
def library():
    u = current_user()
    ensure_monthly_credits(u)
    songs = Song.query.filter_by(user_id=u.id).order_by(Song.created_at.desc()).all()
    return render_template_string('''
<!doctype html><meta charset="utf-8"><title>Library</title>
<style>
body{font-family:system-ui;background:#0b0f17;color:#e6f1ff;padding:24px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:14px}
.card{background:#111827;border:1px solid #1f2937;border-radius:12px;padding:12px}
.title{display:flex;justify-content:space-between;align-items:center}
.btn{background:#06b6d4;color:#001018;border:none;padding:8px 12px;border-radius:8px;text-decoration:none;cursor:pointer}
.menu button{width:100%;text-align:left;background:#0a1625;border:1px solid #1b2a3a;color:#e6f1ff;padding:8px;border-radius:8px}
</style>
<div style="display:flex;gap:8px;align-items:center;justify-content:space-between;margin-bottom:12px">
  <div>
    <a href="/music" class="btn">Plans</a>
    {% if allowed %}<a href="/music/mini-studio" class="btn">Mini Studio</a>{% endif %}
    <a href="/music/community" class="btn">Community</a>
  </div>
  <div class="muted">Credits: <b>{{u.trainer_credits}}</b></div>
  <form method="post" action="{{url_for('create_checkout_session')}}" style="margin:0">
    <input type="hidden" name="credits" value="350"><button class="btn">Buy +350</button>
  </form>
</div>
<div class="grid">
{% for s in songs %}
  <div class="card">
    <div class="title"><b>{{s.title}}</b><small>{{s.created_at.strftime('%Y-%m-%d')}}</small></div>
    <audio id="audio-{{s.id}}" controls src="/music/audio/{{s.id}}"></audio>
    <div>❤️ {{s.likes}} • ▶️ {{s.play_count}}</div>
    <div style="display:flex;gap:6px;margin-top:6px">
      <button onclick="shareToCommunity({{s.id}})" class="btn">Share Anonymously</button>
      <a href="/music/audio/{{s.id}}" download class="btn">Download</a>
    </div>
  </div>
{% endfor %}
</div>
<script>
async function shareToCommunity(id){
  if(!confirm('Share anonymously to Community?')) return;
  const r=await fetch('/music/community/share/'+id,{method:'POST'});
  alert(await r.text());
}
</script>
''', songs=songs, allowed=is_max_allowed(u), u=u)

@app.route('/music/audio/<int:song_id>')
@login_required
def audio(song_id):
    s = db.session.get(Song, song_id)
    if not s or s.user_id != current_user().id: return 'Not found', 404
    mp3 = s.mp3_path()
    return send_file(mp3) if os.path.exists(mp3) else send_file(s.file_path)

# ---------- Community (anonymous) ----------
@app.route('/music/community')
@login_required
def community():
    files = [f for f in sorted(os.listdir(COMMUNITY_DIR), reverse=True)
             if f.lower().endswith(('.mp3','.wav'))]
    return render_template_string('''
<!doctype html><meta charset="utf-8"><title>Community</title>
<style>body{font-family:system-ui;background:#0b0f17;color:#e6f1ff;padding:24px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:14px}
.card{background:#111827;border:1px solid #1f2937;border-radius:12px;padding:12px}
a.btn{background:#06b6d4;color:#001018;border:none;padding:8px 12px;border-radius:8px;text-decoration:none}
</style>
<div style="display:flex;gap:8px;margin-bottom:12px">
  <a href="/music" class="btn">Plans</a>
  <a href="/music/library" class="btn">Library</a>
</div>
<div class="grid">
  {% for f in files %}
    <div class="card">
      <audio controls src="/music/community/file/{{f}}"></audio>
      <div style="margin-top:6px">{{f}}</div>
    </div>
  {% endfor %}
</div>
<div style="margin-top:20px;color:#9aa8bd;font-size:.9rem">Anonymous: files here are not linked to account identities.</div>
''', files=files)

@app.route('/music/community/file/<path:fname>')
@login_required
def community_file(fname):
    path = os.path.join(COMMUNITY_DIR, fname)
    if not os.path.exists(path): return 'Not found', 404
    return send_file(path)

@app.route('/music/community/share/<int:song_id>', methods=['POST'])
@login_required
def share_to_community(song_id):
    s = db.session.get(Song, song_id)
    if not s or s.user_id != current_user().id: return 'Not found', 404
    base = f"shared_{secrets.token_hex(6)}"
    src = s.file_path; ext = os.path.splitext(src)[1]
    shutil.copy2(src, os.path.join(COMMUNITY_DIR, base+ext))
    mp3 = s.mp3_path()
    if os.path.exists(mp3):
        shutil.copy2(mp3, os.path.join(COMMUNITY_DIR, base+'.mp3'))
    return '✅ Shared anonymously to Community', 200

# ---------- Save helpers ----------
def _save_new_song(user_id, title, y, sr, tags=None):
    if not (np and sf): return None
    os.makedirs(LIBRARY_DIR, exist_ok=True)
    file_id = secrets.token_hex(6)
    wav_path = os.path.join(LIBRARY_DIR, f"{file_id}_{title.replace(' ','_')}.wav")
    sf.write(wav_path, y, sr)
    if ffmpeg_ok():
        mp3_path = os.path.splitext(wav_path)[0] + '.mp3'
        subprocess.run(['ffmpeg','-y','-i', wav_path, '-codec:a','libmp3lame','-q:a','2', mp3_path],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    song = Song(user_id=user_id, title=title, tags=tags or '', file_path=wav_path)
    db.session.add(song); db.session.commit()
    return song

# ---------- Upload route ----------
@app.route('/api/song/upload', methods=['POST'])
@login_required
def upload_song():
    if not (np and sf): return 'Audio processing not available', 500
    u = current_user()
    if not u: return 'Not logged in', 401
    
    file = request.files.get('audio')
    title = request.form.get('title', '').strip()
    tags = request.form.get('tags', '').strip()
    
    if not file or not title:
        return 'Missing file or title', 400
    
    # SECURITY: Validate file type and size
    allowed_audio_extensions = {'.wav', '.mp3', '.flac', '.m4a', '.ogg'}
    file_ext = os.path.splitext(file.filename)[1].lower() if file.filename else ''
    if file_ext not in allowed_audio_extensions:
        return 'Invalid audio file type. Allowed: WAV, MP3, FLAC, M4A, OGG', 400
    
    # Check file size (max 50MB for audio)
    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    if size > 50 * 1024 * 1024:
        return 'File too large (max 50MB)', 400
    
    # Save uploaded file temporarily with safe extension
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
        file.save(tmp.name)
        
        try:
            # Load and process audio
            y, sr = librosa.load(tmp.name, sr=None, mono=True)
            # Apply length cap
            from block_c_limits import MAX_SONG_LENGTH_SECONDS
            max_len = int(MAX_SONG_LENGTH_SECONDS * sr)
            if len(y) > max_len:
                y = y[:max_len]
            
            song = _save_new_song(u.id, title, y, sr, tags)
            if song:
                return redirect(url_for('library'))
            else:
                return 'Failed to save song', 500
                
        finally:
            os.unlink(tmp.name)

# ---------- Import audio routes (Block B provides these) ----------
from audio_tools import register_audio_routes
register_audio_routes(app, db, Song, current_user, is_max_allowed, _save_new_song)

# ---------- Cron-safe admin endpoints ----------
@app.route('/admin/reset-max-credits', methods=['POST', 'GET'])
def reset_max_credits():
    """
    Cron-safe endpoint to refill all active Max subscribers to MONTHLY_CREDITS_MAX.
    Use:
      POST with header: X-Admin-Token: <ADMIN_TOKEN>
      or GET with ?token=<ADMIN_TOKEN>&dry_run=1 (preview only)
    """
    _check_admin_token()

    dry = request.args.get('dry_run') in ('1', 'true', 'yes')
    today = today_utc_date()

    users = User.query.filter_by(plan='max').all()
    to_reset = []
    for u in users:
        if (u.last_credit_reset is None or
            u.last_credit_reset.year != today.year or
            u.last_credit_reset.month != today.month):
            to_reset.append(u)

    if dry:
        return {"eligible_count": len(to_reset), "today": str(today),
                "monthly_max": MONTHLY_CREDITS_MAX}, 200

    for u in to_reset:
        u.trainer_credits = MONTHLY_CREDITS_MAX
        u.last_credit_reset = today
    db.session.commit()

    return {"reset_count": len(to_reset), "today": str(today),
            "monthly_max": MONTHLY_CREDITS_MAX}, 200

@app.route('/admin/cleanup-trials', methods=['POST', 'GET'])
def cleanup_trials():
    """
    Cron-safe endpoint to deactivate expired Max trials (defensive housekeeping).
    """
    _check_admin_token()

    now = datetime.utcnow()
    trials = MaxTrial.query.filter_by(active=True).all()
    expired = [t for t in trials if t.expires_at <= now]

    if request.args.get('dry_run') in ('1','true','yes'):
        return {"expired_count": len(expired)}, 200

    for t in expired:
        t.active = False
    db.session.commit()
    return {"deactivated": len(expired)}, 200

# ---------- Integration with main app ----------
def register_music_routes(main_app):
    """Register music routes with the main app"""
    for rule in app.url_map.iter_rules():
        main_app.add_url_rule(
            rule.rule, 
            rule.endpoint + '_music', 
            app.view_functions[rule.endpoint],
            methods=rule.methods
        )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)