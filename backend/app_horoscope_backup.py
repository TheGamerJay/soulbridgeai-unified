# app_horoscope_full.py — One-file Horoscope API + UI (port 8080)
# ------------------------------------------------------------------
# WHAT THIS DOES
# - /api/horoscope/today   (GET)   -> ?sign=aries
# - /api/horoscope/period  (POST)  -> {sign, period: daily|weekly|monthly, date?}
# - /api/horoscope/traits  (GET)   -> ?sign=aries (returns static metadata)
# - /api/horoscope/compat  (GET)   -> ?a=aries&b=leo (compatibility)
# - /horoscope             (UI)    -> simple "real life" cards with icons + shareable results
#
# NOTES
# - Entertainment content only (not astronomical forecasting).
# - Deterministic per (sign, period, date) so each day has consistent readings.
# - Put optional sign icons in ./static/horoscope/<sign>.png (lowercase).
# ------------------------------------------------------------------

import os, math, random, hashlib, datetime
from typing import Dict, Any, List, Tuple
from flask import Flask, Blueprint, jsonify, request, render_template_string

# -----------------------------
# Config
# -----------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(HERE, "static")
HORO_IMG_DIR = os.path.join(STATIC_DIR, "horoscope")
IMG_EXT = ".png"      # sign icon extension if you add icons
PORT = 8080

# -----------------------------
# Sign metadata (traits)
# -----------------------------
SIGNS: List[str] = [
    "aries","taurus","gemini","cancer","leo","virgo",
    "libra","scorpio","sagittarius","capricorn","aquarius","pisces"
]

ZODIAC: Dict[str, Dict[str, Any]] = {
    "aries": {"name":"Aries","symbol":"Ram","glyph":"♈","dates":"Mar 21 – Apr 19",
              "element":"Fire","modality":"Cardinal","planet":"Mars",
              "strengths":["bold","decisive","energetic","direct"],
              "weaknesses":["impulsive","impatient","combative","restless"]},
    "taurus": {"name":"Taurus","symbol":"Bull","glyph":"♉","dates":"Apr 20 – May 20",
              "element":"Earth","modality":"Fixed","planet":"Venus",
              "strengths":["steady","loyal","sensual","patient"],
              "weaknesses":["stubborn","possessive","comfort-seeking"]},
    "gemini": {"name":"Gemini","symbol":"Twins","glyph":"♊","dates":"May 21 – Jun 20",
              "element":"Air","modality":"Mutable","planet":"Mercury",
              "strengths":["curious","witty","adaptable","expressive"],
              "weaknesses":["scattered","inconsistent","restless"]},
    "cancer": {"name":"Cancer","symbol":"Crab","glyph":"♋","dates":"Jun 21 – Jul 22",
              "element":"Water","modality":"Cardinal","planet":"Moon",
              "strengths":["nurturing","intuitive","protective","devoted"],
              "weaknesses":["moody","clingy","avoidant"]},
    "leo": {"name":"Leo","symbol":"Lion","glyph":"♌","dates":"Jul 23 – Aug 22",
              "element":"Fire","modality":"Fixed","planet":"Sun",
              "strengths":["radiant","confident","generous","playful"],
              "weaknesses":["proud","dramatic","attention-seeking"]},
    "virgo": {"name":"Virgo","symbol":"Maiden","glyph":"♍","dates":"Aug 23 – Sep 22",
              "element":"Earth","modality":"Mutable","planet":"Mercury",
              "strengths":["precise","helpful","grounded","analytical"],
              "weaknesses":["critical","perfectionist","overthinking"]},
    "libra": {"name":"Libra","symbol":"Scales","glyph":"♎","dates":"Sep 23 – Oct 22",
              "element":"Air","modality":"Cardinal","planet":"Venus",
              "strengths":["charming","fair","diplomatic","artful"],
              "weaknesses":["indecisive","people-pleasing","avoidant of conflict"]},
    "scorpio": {"name":"Scorpio","symbol":"Scorpion","glyph":"♏","dates":"Oct 23 – Nov 21",
              "element":"Water","modality":"Fixed","planet":"Mars/Pluto",
              "strengths":["intense","loyal","strategic","transformative"],
              "weaknesses":["jealous","secretive","all-or-nothing"]},
    "sagittarius": {"name":"Sagittarius","symbol":"Archer","glyph":"♐","dates":"Nov 22 – Dec 21",
              "element":"Fire","modality":"Mutable","planet":"Jupiter",
              "strengths":["adventurous","optimistic","big-picture","honest"],
              "weaknesses":["blunt","restless","commitment-averse"]},
    "capricorn": {"name":"Capricorn","symbol":"Sea-Goat","glyph":"♑","dates":"Dec 22 – Jan 19",
              "element":"Earth","modality":"Cardinal","planet":"Saturn",
              "strengths":["ambitious","disciplined","pragmatic","resilient"],
              "weaknesses":["stoic","rigid","work-obsessed"]},
    "aquarius": {"name":"Aquarius","symbol":"Water-Bearer","glyph":"♒","dates":"Jan 20 – Feb 18",
              "element":"Air","modality":"Fixed","planet":"Saturn/Uranus",
              "strengths":["innovative","independent","humanitarian","original"],
              "weaknesses":["aloof","contrarian","detached"]},
    "pisces": {"name":"Pisces","symbol":"Fishes","glyph":"♓","dates":"Feb 19 – Mar 20",
              "element":"Water","modality":"Mutable","planet":"Jupiter/Neptune",
              "strengths":["empathetic","imaginative","spiritual","artistic"],
              "weaknesses":["escapist","over-idealistic","boundary-blurry"]},
}

# element groups for simple compatibility
ELEMENT_GROUPS = {
    "Fire": {"best":["Fire","Air"], "challenging":["Water"]},
    "Earth": {"best":["Earth","Water"], "challenging":["Fire"]},
    "Air": {"best":["Air","Fire"], "challenging":["Earth"]},
    "Water": {"best":["Water","Earth"], "challenging":["Air"]},
}

# -----------------------------
# Deterministic generator
# -----------------------------
def _seed(sign: str, date: datetime.date, period: str):
    base = f"{sign}|{period}|{date.isoformat()}"
    h = hashlib.sha256(base.encode()).hexdigest()
    random.seed(int(h[:16], 16))

BLURB_OPENERS = [
    "Your energy today gravitates toward",
    "The lesson surfacing revolves around",
    "A gentle nudge pushes you toward",
    "Cosmic weather highlights",
    "Your focus is best placed on",
    "An opportunity unfolds through",
]
DOMAINS = ["communication","work & craft","home & foundations","relationships","health & routines",
           "creativity","learning","finances","boundaries","long-term goals","self-trust","recovery"]

ADVICE_VERBS = ["ground","simplify","commit","experiment with","reframe","reach out about","prioritize",
                "declutter","set boundaries around","journal about","celebrate","rest before"]
TONES = ["confident","curious","steady","reflective","optimistic","protective","playful","pragmatic"]

LUCKY_COLORS = ["crimson","emerald","sapphire","gold","silver","indigo","rose","teal","amber","ivory","charcoal","coral"]
LUCKY_TIMES = ["08:08","10:10","11:11","12:12","14:44","16:16","20:20"]
MOODS = ["focused","cozy","electric","expansive","tender","quiet","brave","clear-headed"]
NUMBERS = list(range(1, 78))  # cute nod to tarot

def _sentence(sign: str) -> str:
    s = ZODIAC[sign]
    opener = random.choice(BLURB_OPENERS)
    domain = random.choice(DOMAINS)
    verb = random.choice(ADVICE_VERBS)
    tone = random.choice(TONES)
    target = 'that' if verb != 'celebrate' else 'what you have already achieved'
    return (f"{opener} {domain}. Lean into your {s['element'].lower()} nature and {verb} "
            f"{target}. Keep your tone {tone} and the path clarifies.")

def _lucky() -> Dict[str, Any]:
    return {
        "color": random.choice(LUCKY_COLORS),
        "time": random.choice(LUCKY_TIMES),
        "numbers": random.sample(NUMBERS, 3),
        "mood": random.choice(MOODS),
    }

def _period_dates(date: datetime.date, period: str) -> Tuple[datetime.date, datetime.date]:
    if period == "weekly":
        # Monday–Sunday of that ISO week
        start = date - datetime.timedelta(days=date.weekday())
        end = start + datetime.timedelta(days=6)
        return start, end
    if period == "monthly":
        start = date.replace(day=1)
        if start.month == 12:
            next_month = start.replace(year=start.year+1, month=1, day=1)
        else:
            next_month = start.replace(month=start.month+1, day=1)
        end = next_month - datetime.timedelta(days=1)
        return start, end
    # daily default
    return date, date

def generate(sign: str, date: datetime.date, period: str) -> Dict[str, Any]:
    if sign not in SIGNS:
        raise ValueError("Unknown sign.")
    if period not in ("daily","weekly","monthly"):
        raise ValueError("period must be daily|weekly|monthly")

    _seed(sign, date, period)
    s_meta = ZODIAC[sign]
    start, end = _period_dates(date, period)

    # craft 2-3 sentences
    lines = [
        _sentence(sign),
        f"Your {s_meta['modality'].lower()} drive pairs with {s_meta['planet']}'s influence—progress favors small consistent steps.",
    ]
    if period != "daily":
        lines.append("Expect momentum mid-period; late window rewards review and tidy follow-through.")

    return {
        "sign": sign,
        "date": date.isoformat(),
        "period": period,
        "window": {"start": start.isoformat(), "end": end.isoformat()},
        "summary": " ".join(lines),
        "lucky": _lucky(),
        "meta": s_meta,
    }

# -----------------------------
# Compatibility (very simple)
# -----------------------------
def compatibility(a: str, b: str) -> Dict[str, Any]:
    if a not in SIGNS or b not in SIGNS:
        raise ValueError("Unknown sign(s).")
    A, B = ZODIAC[a], ZODIAC[b]
    eA, eB = A["element"], B["element"]
    score = 50
    # element synergy
    if eB in ELEMENT_GROUPS[eA]["best"]: score += 25
    if eB in ELEMENT_GROUPS[eA]["challenging"]: score -= 15
    # modality spice
    if A["modality"] == B["modality"]: score += 5
    score = max(5, min(95, score))
    note = f"{A['element']} + {B['element']} dynamic; {A['modality']} meeting {B['modality']}."
    return {"a":a,"b":b,"score":score,"note":note}

# -----------------------------
# Interpretation system
# -----------------------------
INTERPRET_PHRASES = {
    "cosmic_weather": [
        "This suggests the universe is aligning to bring focus to",
        "The cosmic energies are drawing your attention toward",
        "This indicates a spiritual shift happening around",
        "The celestial forces are highlighting the importance of"
    ],
    "element_meaning": {
        "Fire": "your passionate, action-oriented nature is being called upon",
        "Earth": "your grounded, practical wisdom needs to take the lead", 
        "Air": "your intellectual and communicative gifts are essential now",
        "Water": "your intuitive, emotional intelligence holds the key"
    },
    "modality_meaning": {
        "Cardinal": "This is a time for leadership and initiating new directions",
        "Fixed": "Stability and determination will serve you best during this period",
        "Mutable": "Flexibility and adaptability are your greatest strengths right now"
    },
    "lucky_meanings": {
        "color": {
            "crimson": "bold action and courage", "emerald": "growth and healing",
            "sapphire": "wisdom and clarity", "gold": "success and abundance",
            "silver": "intuition and reflection", "indigo": "deep spiritual insight",
            "rose": "love and compassion", "teal": "emotional balance",
            "amber": "warmth and protection", "ivory": "purity and new beginnings",
            "charcoal": "grounding and mystery", "coral": "creativity and vitality"
        },
        "mood": {
            "focused": "concentrated effort will yield the best results",
            "cozy": "comfort and nurturing environments support your growth",
            "electric": "high energy and dynamic action are favored",
            "expansive": "thinking big and embracing possibilities serves you",
            "tender": "gentle, caring approaches will open doors",
            "quiet": "stillness and reflection bring important insights",
            "brave": "courage to face challenges head-on is your superpower",
            "clear-headed": "logical thinking and clarity will guide you well"
        }
    }
}

def generate_interpretation(reading: Dict[str, Any]) -> str:
    sign_meta = reading["meta"]
    lucky = reading["lucky"]
    period = reading["period"]
    
    # Use same seed to ensure consistent interpretation
    date = datetime.date.fromisoformat(reading["date"])
    _seed(reading["sign"], date, f"{period}_interpret")
    
    lines = []
    
    # Opening cosmic context
    opener = random.choice(INTERPRET_PHRASES["cosmic_weather"])
    lines.append(f"{opener} your personal growth and life path.")
    
    # Element and modality meaning
    element_meaning = INTERPRET_PHRASES["element_meaning"][sign_meta["element"]]
    modality_meaning = INTERPRET_PHRASES["modality_meaning"][sign_meta["modality"]]
    lines.append(f"As a {sign_meta['element']} sign, {element_meaning}. {modality_meaning}.")
    
    # Lucky color interpretation
    color = lucky["color"]
    color_meaning = INTERPRET_PHRASES["lucky_meanings"]["color"].get(color, "positive transformation")
    lines.append(f"Your cosmic gift of {color} energy represents {color_meaning} - incorporate this color into your environment or wardrobe to amplify these qualities.")
    
    # Power hour meaning
    time = lucky["time"]
    lines.append(f"The {time} power hour is when cosmic energies are most aligned with your personal vibration - use this time for meditation, important decisions, or creative work.")
    
    # Mood interpretation
    mood = lucky["mood"]
    mood_meaning = INTERPRET_PHRASES["lucky_meanings"]["mood"].get(mood, "balanced energy serves you well")
    lines.append(f"Embodying {mood} vibes means {mood_meaning} during this {period} period.")
    
    # Numbers significance
    numbers = lucky["numbers"]
    lines.append(f"Your lucky numbers {', '.join(map(str, numbers))} may appear as signs of alignment - watch for them in addresses, times, or important documents.")
    
    # Planetary influence
    planet = sign_meta["planet"]
    planet_guidance = {
        "Mars": "brings courage and drive - take bold action on your goals",
        "Venus": "enhances love and creativity - focus on relationships and artistic pursuits", 
        "Mercury": "sharpens communication - important conversations and learning opportunities await",
        "Moon": "heightens intuition - trust your feelings and nurture your emotional needs",
        "Sun": "illuminates your path - step into your power and let your light shine",
        "Jupiter": "expands possibilities - think big and embrace opportunities for growth",
        "Saturn": "teaches discipline - hard work now builds lasting foundations",
        "Mars/Pluto": "transforms through intensity - embrace change and release what no longer serves",
        "Jupiter/Neptune": "inspires through dreams - pay attention to your visions and spiritual insights",
        "Saturn/Uranus": "innovates through structure - blend tradition with progressive ideas"
    }
    planet_msg = planet_guidance.get(planet, "guides your journey with cosmic wisdom")
    lines.append(f"Your ruling planet {planet} {planet_msg}.")
    
    return " ".join(lines)

# -----------------------------
# Flask
# -----------------------------
app = Flask(__name__, static_folder=STATIC_DIR, static_url_path="/static")
horo = Blueprint("horo", __name__, url_prefix="/api/horoscope")

@horo.get("/today")
def api_today():
    sign = (request.args.get("sign") or "").lower().strip()
    today = datetime.date.today()
    try:
        out = generate(sign, today, "daily")
        return jsonify(out), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@horo.post("/period")
def api_period():
    data = request.get_json(silent=True) or {}
    sign = (data.get("sign") or "").lower().strip()
    period = (data.get("period") or "daily").lower().strip()
    date_str = data.get("date")  # YYYY-MM-DD or None (today)
    if date_str:
        try:
            date = datetime.date.fromisoformat(date_str)
        except Exception:
            return jsonify({"error":"date must be YYYY-MM-DD"}), 400
    else:
        date = datetime.date.today()
    try:
        out = generate(sign, date, period)
        return jsonify(out), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@horo.get("/traits")
def api_traits():
    sign = (request.args.get("sign") or "").lower().strip()
    if sign not in SIGNS:
        return jsonify({"error":"Unknown sign."}), 400
    return jsonify({"sign": sign, "meta": ZODIAC[sign]}), 200

@horo.get("/compat")
def api_compat():
    a = (request.args.get("a") or "").lower().strip()
    b = (request.args.get("b") or "").lower().strip()
    try:
        return jsonify(compatibility(a, b)), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@horo.post("/interpret")
def api_interpret():
    data = request.get_json(silent=True) or {}
    sign = (data.get("sign") or "").lower().strip()
    period = (data.get("period") or "daily").lower().strip()
    date_str = data.get("date")
    
    if date_str:
        try:
            date = datetime.date.fromisoformat(date_str)
        except Exception:
            return jsonify({"error":"date must be YYYY-MM-DD"}), 400
    else:
        date = datetime.date.today()
    
    try:
        # Get the original reading first
        reading = generate(sign, date, period)
        
        # Generate interpretation
        interpretation = generate_interpretation(reading)
        
        return jsonify({"interpretation": interpretation}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

app.register_blueprint(horo)

# -----------------------------
# Minimal UI
# -----------------------------
HTML = r"""
<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>Horoscope</title>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <style>
    :root { --w: 1100px; --gap: 14px; }
    body { 
      font-family: Georgia, 'Times New Roman', serif; 
      margin:0; 
      background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 40%, #2e1065 100%);
      color: #d4af37; 
      min-height: 100vh;
    }
    header { 
      background: rgba(0,0,0,0.8); 
      color: #d4af37; 
      padding: 24px; 
      text-align: center;
      backdrop-filter: blur(10px);
      border-bottom: 2px solid #d4af37;
    }
    header h1 {
      font-size: 2.8rem;
      margin: 0;
      text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
      font-weight: bold;
    }
    .subtitle {
      font-size: 1.2rem;
      margin-top: 8px;
      opacity: 0.9;
      font-style: italic;
    }
    main { max-width: var(--w); margin: 0 auto; padding: 20px; }
    .row { display:flex; flex-wrap:wrap; gap:12px; align-items:end; margin-bottom: 20px; }
    .panel { 
      background: rgba(20, 20, 40, 0.9); 
      border: 1px solid #d4af37; 
      border-radius: 15px; 
      padding: 16px;
      backdrop-filter: blur(5px);
      box-shadow: 0 4px 15px rgba(212, 175, 55, 0.2);
    }
    .panel label {
      display: block;
      margin-bottom: 6px;
      font-weight: bold;
      color: #d4af37;
    }
    select, input, button { 
      padding: 10px 12px; 
      border: 1px solid #d4af37; 
      border-radius: 10px; 
      background: rgba(0,0,0,0.7);
      color: #d4af37;
      font-family: inherit;
    }
    select option {
      background: #1a1a2e;
      color: #d4af37;
    }
    button { 
      background: linear-gradient(45deg, #d4af37, #ffd700); 
      color: #0f0f23; 
      cursor: pointer; 
      font-weight: bold;
      border: none;
      transition: all 0.3s ease;
    }
    button:hover {
      transform: translateY(-2px);
      box-shadow: 0 6px 20px rgba(212, 175, 55, 0.4);
    }
    .grid { display:grid; grid-template-columns: repeat(auto-fit, minmax(350px,1fr)); gap: var(--gap); margin-top:20px; }
    .card { 
      background: rgba(20, 20, 40, 0.95); 
      border: 2px solid #d4af37; 
      border-radius: 20px; 
      padding: 20px; 
      display: flex; 
      gap: 16px;
      backdrop-filter: blur(10px);
      box-shadow: 0 8px 25px rgba(212, 175, 55, 0.3);
      transition: all 0.3s ease;
    }
    .card:hover {
      transform: translateY(-5px);
      box-shadow: 0 12px 35px rgba(212, 175, 55, 0.4);
    }
    .icon { 
      width: 80px; 
      height: 80px; 
      border-radius: 15px; 
      background: linear-gradient(45deg, #d4af37, #ffd700); 
      display: flex; 
      align-items: center; 
      justify-content: center; 
      font-size: 42px; 
      color: #0f0f23;
      box-shadow: 0 4px 15px rgba(212, 175, 55, 0.3);
    }
    .icon img {
      border-radius: 15px;
    }
    .meta { font-size: 14px; color: #a0a0c0; }
    .pill { 
      display: inline-block; 
      padding: 4px 12px; 
      border-radius: 20px; 
      background: rgba(212, 175, 55, 0.2); 
      border: 1px solid #d4af37;
      font-size: 12px; 
      margin-right: 8px;
      color: #d4af37;
      margin-bottom: 4px;
    }
    .lucky { 
      font-size: 14px; 
      color: #ffd700; 
      background: rgba(255, 215, 0, 0.1);
      padding: 10px;
      border-radius: 10px;
      border: 1px solid #ffd700;
      margin-top: 10px;
    }
    .card-title {
      font-size: 1.3rem;
      font-weight: bold;
      margin-bottom: 8px;
      color: #ffd700;
    }
    .card-content {
      line-height: 1.6;
      color: #e0e0e0;
    }
    footer { 
      color: #a0a0c0; 
      font-size: 12px; 
      text-align: center; 
      padding: 20px;
      margin-top: 40px;
      border-top: 1px solid rgba(212, 175, 55, 0.3);
    }
    .compat-result {
      background: rgba(20, 20, 40, 0.95);
      border: 2px solid #d4af37;
      border-radius: 20px;
      padding: 20px;
      margin-top: 15px;
      backdrop-filter: blur(10px);
      box-shadow: 0 8px 25px rgba(212, 175, 55, 0.3);
    }
    .compat-score {
      font-size: 2.5rem;
      font-weight: bold;
      color: #ffd700;
      text-align: center;
      margin: 10px 0;
    }
    .loading {
      text-align: center;
      color: #ffd700;
      font-style: italic;
      padding: 20px;
    }
    hr {
      border: none;
      border-top: 1px solid rgba(212, 175, 55, 0.3);
      margin: 30px 0;
    }
  </style>
</head>
<body>
  <header>
    <div style="display: flex; align-items: center; justify-content: center; gap: 20px; flex-wrap: wrap;">
      <img src="/static/logos/horoscope sky.png" alt="Horoscope Sky" style="height: 80px; border-radius: 15px; box-shadow: 0 4px 15px rgba(212, 175, 55, 0.3);">
      <div>
        <h1 style="margin: 0;">Horoscope Sky</h1>
        <div class="subtitle">Your Daily Cosmic Guidance</div>
      </div>
    </div>
  </header>
  <main>
    <div class="row">
      <div class="panel">
        <label>🌟 Choose Your Zodiac Sign
          <select id="sign">
            {{options|safe}}
          </select>
        </label>
      </div>
      <div class="panel">
        <label>📅 Reading Type
          <select id="period">
            <option value="daily">Daily Horoscope</option>
            <option value="weekly">Weekly Forecast</option>
            <option value="monthly">Monthly Reading</option>
          </select>
        </label>
      </div>
      <div class="panel">
        <label>📆 Specific Date (Optional)
          <input type="date" id="date" />
        </label>
        <small style="color: #a0a0c0; font-size: 11px;">Leave blank for today</small>
      </div>
      <div class="panel">
        <button id="go" style="font-size: 1.1rem; padding: 12px 20px;">✨ Get My Horoscope ✨</button>
      </div>
    </div>

    <div id="out" class="grid"></div>

    <hr style="margin:20px 0; border:none; border-top:1px solid #eee"/>

    <div class="row">
      <div class="panel">
        <label>💕 First Sign
          <select id="compatA">{{options|safe}}</select>
        </label>
      </div>
      <div class="panel">
        <label>💕 Second Sign
          <select id="compatB">{{options|safe}}</select>
        </label>
      </div>
      <div class="panel">
        <button id="compatGo" style="font-size: 1.1rem; padding: 12px 20px;">💖 Check Compatibility 💖</button>
      </div>
    </div>
    <div id="compat"></div>
  </main>
  <footer>✨ Horoscope Sky's cosmic guidance • Celestial wisdom for your journey through the stars ✨</footer>

<script>
const EXT = "{{ext}}";
const ICON = (s) => `/static/horoscope/${s}${EXT}`;
const pretty = (s) => s[0].toUpperCase()+s.slice(1);

async function fetchPeriod(sign, period, date){
  const body = { sign, period };
  if (date) body.date = date;
  const r = await fetch("/api/horoscope/period", {
    method:"POST", headers:{ "Content-Type":"application/json" }, body:JSON.stringify(body)
  });
  return await r.json();
}

function card(h){
  const m = h.meta;
  return `
  <div class="card">
    <div class="icon"><img src="${ICON(h.sign)}" onerror="this.style.display='none'; this.parentElement.textContent=m.glyph" alt="${m.name}" width="80" height="80"/></div>
    <div style="flex: 1;">
      <div class="card-title">${m.name} ${h.period.charAt(0).toUpperCase() + h.period.slice(1)}</div>
      <div class="meta">${m.glyph} • ${m.dates}</div>
      <div style="margin: 10px 0;">
        <span class="pill">${m.element}</span>
        <span class="pill">${m.modality}</span>
        <span class="pill">${m.planet}</span>
      </div>
      <div class="card-content">${h.summary}</div>
      <div class="lucky">
        ✨ <strong>Cosmic Gifts:</strong> ${h.lucky.color} energy, ${h.lucky.time} power hour, numbers ${h.lucky.numbers.join(", ")}, ${h.lucky.mood} vibes
      </div>
      <div style="margin-top: 15px; text-align: center;">
        <button onclick="interpretReading('${h.sign}', '${h.period}', '${h.date}')" style="font-size: 0.95rem; padding: 8px 16px;">🔮 Interpret My Reading 🔮</button>
      </div>
      <div id="interpretation-${h.sign}-${h.period}" style="display: none; margin-top: 15px; padding: 15px; background: rgba(0,0,0,0.3); border-radius: 10px; border-left: 4px solid #d4af37;">
        <div class="loading">✨ Channeling deeper cosmic insights...</div>
      </div>
    </div>
  </div>`;
}

async function getHoroscope() {
  const s = document.getElementById("sign").value;
  const p = document.getElementById("period").value;
  const d = document.getElementById("date").value;
  const out = document.getElementById("out");
  
  if (!s) {
    out.innerHTML = "<div style='color:#ff6b6b; padding: 20px; text-align: center;'>Please select your zodiac sign first!</div>";
    return;
  }
  
  out.innerHTML = "<div class='loading'>✨ Consulting the cosmic energies...</div>";
  
  try {
    const h = await fetchPeriod(s, p, d || null);
    if (h.error) { 
      out.innerHTML = `<div style="color:#ff6b6b; padding: 20px; text-align: center;">${h.error}</div>`; 
      return; 
    }
    out.innerHTML = card(h);
  } catch (error) {
    out.innerHTML = `<div style="color:#ff6b6b; padding: 20px; text-align: center;">Connection error. Please try again.</div>`;
  }
}

// Simple button-only approach - no auto-triggering
document.getElementById("go").addEventListener("click", getHoroscope);

async function interpretReading(sign, period, date) {
  const interpretDiv = document.getElementById(`interpretation-${sign}-${period}`);
  
  if (interpretDiv.style.display === 'none') {
    interpretDiv.style.display = 'block';
    
    try {
      const body = { sign, period };
      if (date) body.date = date;
      
      const r = await fetch("/api/horoscope/interpret", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
      });
      
      const data = await r.json();
      
      if (data.error) {
        interpretDiv.innerHTML = `<div style="color:#ff6b6b;">${data.error}</div>`;
        return;
      }
      
      interpretDiv.innerHTML = `
        <div style="color: #d4af37; font-weight: bold; margin-bottom: 10px; border-bottom: 1px solid #d4af37; padding-bottom: 8px;">
          🔮 Deeper Cosmic Insights
        </div>
        <div style="line-height: 1.7; color: #e8e8e8; font-style: italic;">
          ${data.interpretation}
        </div>
      `;
    } catch (error) {
      interpretDiv.innerHTML = `<div style="color:#ff6b6b;">Connection error. Please try again.</div>`;
    }
  } else {
    interpretDiv.style.display = 'none';
  }
}

document.getElementById("compatGo").addEventListener("click", async () => {
  const a = document.getElementById("compatA").value;
  const b = document.getElementById("compatB").value;
  const wrap = document.getElementById("compat");
  
  if (!a || !b) {
    wrap.innerHTML = `<div style="color:#ff6b6b; padding: 20px; text-align: center;">Please select both zodiac signs!</div>`;
    return;
  }
  
  wrap.innerHTML = `<div class="loading">✨ Analyzing cosmic compatibility...</div>`;
  
  try {
    const r = await fetch(`/api/horoscope/compat?a=${a}&b=${b}`);
    const d = await r.json();
    if (d.error) { 
      wrap.innerHTML = `<div style="color:#ff6b6b; padding: 20px; text-align: center;">${d.error}</div>`; 
      return; 
    }
    wrap.innerHTML = `<div class="compat-result">
      <div class="card-title" style="text-align: center;">${pretty(d.a)} × ${pretty(d.b)} Compatibility</div>
      <div class="compat-score">${d.score}%</div>
      <div class="meta" style="text-align: center;">${d.note}</div>
    </div>`;
  } catch (error) {
    wrap.innerHTML = `<div style="color:#ff6b6b; padding: 20px; text-align: center;">Connection error. Please try again.</div>`;
  }
});
</script>
</body>
</html>
"""

@app.get("/horoscope")
def horoscope_page():
    opts = '<option value="">Select your zodiac sign...</option>\n' + "\n".join([
        f'<option value="{s}">{ZODIAC[s]["name"]} ({ZODIAC[s]["dates"]})</option>' 
        for s in SIGNS
    ])
    return render_template_string(HTML, options=opts, ext=IMG_EXT)

# -----------------------------
# Run
# -----------------------------
if __name__ == "__main__":
    os.makedirs(HORO_IMG_DIR, exist_ok=True)
    app.run(host="0.0.0.0", port=PORT, debug=True)