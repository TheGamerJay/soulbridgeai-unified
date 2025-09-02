#!/usr/bin/env python3
"""
SoulBridge AI - Enhanced Tarot System (PNG Version)
Standalone complete tarot API + UI with 3D cards, reversals, clarifiers
Converted from JPG to PNG to match our organized tarot card system
"""

# Before running: put your images in static/tarot/ (see naming rules in comments below), 
# put your JSON in data/tarot_meanings_full.json, then run python app_tarot_full.py.
# ----------------------------------------------------------------------------- 
# WHAT THIS DOES
# - Serves /api/tarot/spreads and /api/tarot/reading (JSON) for your AI.
# - Serves a full UI at /tarot with 3D flip cards, reversals, clarifiers, seed.
# - Uses your meanings file: ./data/tarot_meanings_full.json (78 cards)
# - Loads images from: ./static/tarot/
#
# IMAGES (already organized in PNG format)
# - Place 78 front images + 1 back image in: ./static/tarot/
# - Filenames must follow these slugs (lowercase, underscores):
# Major: the_fool.png, the_magician.png, the_high_priestess.png, ... , the_world.png
# Wands: ace_of_wands.png, two_of_wands.png, ... , king_of_wands.png  
# Cups: ace_of_cups.png, ... , king_of_cups.png
# Swords: ace_of_swords.png, ... , king_of_swords.png
# Pentacles: ace_of_pentacles.png, ... , king_of_pentacles.png
# - Provide a card back image named: back.png
#
# RUN
# python app_tarot_full.py
# Then open http://localhost:8080/tarot
#
# NOTES
# - Meanings JSON schema (one entry per card):
# {
#   "The Fool": {
#     "upright": "…",
#     "reversed": "…", 
#     "symbols": "…"
#   },
#   "Ace of Wands": { ... },
#   ...
# }
# - This app does not ship any images; you must supply your own, licensed deck.
# -----------------------------------------------------------------------------

import os, json, random
from datetime import datetime
from typing import Dict, List, Any, Optional
from flask import Flask, Blueprint, jsonify, request, send_from_directory, render_template_string

# OpenAI integration for interpretations
try:
    from openai import OpenAI
    openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY")) if os.environ.get("OPENAI_API_KEY") else None
except ImportError:
    openai_client = None

# -----------------------------
# Config
# -----------------------------
HERE = os.path.dirname(os.path.abspath(__file__))

# Library integration for auto-saving readings (standalone version)
READINGS_DIR = os.path.join(HERE, "saved_readings")
os.makedirs(READINGS_DIR, exist_ok=True)
DATA_FILE = os.path.join(HERE, "data", "tarot_meanings_full.json")
STATIC_DIR = os.path.join(HERE, "static")
TAROT_IMG_DIR = os.path.join(STATIC_DIR, "tarot")
IMG_EXT = ".png"  # Changed from .jpg to .png to match our organized system
PORT = 8080  # hardcoded port as requested

# -----------------------------
# Spreads
# -----------------------------
SPREADS: Dict[str, List[str]] = {
    "1 Card": ["Message"],
    "3 Card": ["Past", "Present", "Future"],
    "5 Card": ["Situation", "Challenge", "Advice", "Hidden Factor", "Likely Outcome"],
    "Celtic Cross": [
        "Present (Heart of the matter)",
        "Challenge (Crossing you)", 
        "Past (Root/Foundation)",
        "Future (Near term)",
        "Above (Conscious/Goal)",
        "Below (Subconscious/Drive)",
        "Advice/You",
        "External influences",
        "Hopes & fears",
        "Outcome (Trajectory)"
    ],
    "Advanced": [f"Position {i}" for i in range(1, 22)],
}

# -----------------------------
# Utility: Name → image slug
# -----------------------------
REPLACERS = {
    "The ": "the_",
    " of ": "_of_",
    " & ": "_and_",
    "-": "_",
    "'": "",
    "'": "",
}

def to_slug(card_name: str) -> str:
    s = card_name.strip().lower()
    for a,b in REPLACERS.items():
        s = s.replace(a.lower(), b)
    s = "_".join(s.split())  # collapse whitespace to underscores
    return s

# -----------------------------
# Load Deck
# -----------------------------
def load_deck() -> Dict[str, Dict[str, str]]:
    if not os.path.exists(DATA_FILE):
        raise FileNotFoundError(f"Missing meanings file: {DATA_FILE}")
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    # normalize & sanity check
    for card, entry in data.items():
        if not isinstance(entry, dict):
            raise ValueError(f"Card '{card}' entry must be an object.")
        if "upright" not in entry or "reversed" not in entry:
            raise ValueError(f"Card '{card}' missing 'upright'/'reversed'.")
        entry.setdefault("symbols", "")
    return data

DECK = load_deck()

# -----------------------------
# Core Reading
# -----------------------------
def do_reading(
    spread_name: str = "3 Card",
    reversals: bool = True,
    seed: Optional[str] = None,
    clarifiers: int = 0,
    allow_duplicates: bool = False,
) -> Dict[str, Any]:
    if seed is not None and str(seed).strip():
        random.seed(str(seed))
    
    positions = SPREADS.get(spread_name, SPREADS["3 Card"])
    cards = list(DECK.keys())
    n = len(positions)
    
    if allow_duplicates:
        drawn = [random.choice(cards) for _ in range(n)]
    else:
        drawn = random.sample(cards, n)
    
    results = []
    already = set(drawn)
    
    for pos, card in zip(positions, drawn):
        orientation = "Upright"
        if reversals:
            orientation = random.choice(["Upright", "Reversed"])
        
        entry = DECK[card]
        meaning = entry["upright"] if orientation == "Upright" else entry["reversed"]
        
        one = {
            "position": pos,
            "card": card,
            "slug": to_slug(card),
            "orientation": orientation,
            "meaning": meaning,
            "symbols": entry.get("symbols", "")
        }
        
        if clarifiers and clarifiers > 0:
            one["clarifiers"] = []
            for _ in range(int(clarifiers)):
                if allow_duplicates:
                    clar = random.choice(cards)
                else:
                    remaining = [c for c in cards if c not in already]
                    if not remaining:
                        break
                    clar = random.choice(remaining)
                already.add(clar)
                
                cor = "Upright" if not reversals else random.choice(["Upright", "Reversed"])
                centry = DECK[clar]
                cmeaning = centry["upright"] if cor == "Upright" else centry["reversed"]
                
                one["clarifiers"].append({
                    "card": clar,
                    "slug": to_slug(clar),
                    "orientation": cor,
                    "meaning": cmeaning,
                    "symbols": centry.get("symbols", "")
                })
        
        results.append(one)
    
    return {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "spread": spread_name,
        "reversals": bool(reversals),
        "seed": seed,
        "clarifiers_per_position": int(clarifiers),
        "cards": results
    }

# -----------------------------
# AI Interpretation
# -----------------------------
def get_reading_interpretation(reading_data: Dict[str, Any]) -> str:
    """Generate plain English interpretation of the tarot reading using AI"""
    if not openai_client:
        return "AI interpretation unavailable - OpenAI API key not configured."
    
    try:
        # Build card summary for AI
        card_list = []
        for card in reading_data["cards"]:
            card_info = f"{card['position']}: {card['card']} ({card['orientation']}) - {card['meaning']}"
            card_list.append(card_info)
            
            # Include clarifiers if present
            if card.get("clarifiers"):
                for i, clarifier in enumerate(card["clarifiers"]):
                    card_info = f"  Clarifier {i+1}: {clarifier['card']} ({clarifier['orientation']}) - {clarifier['meaning']}"
                    card_list.append(card_info)
        
        cards_text = "\n".join(card_list)
        
        prompt = f"""You are a wise, compassionate spiritual guide from SoulBridge AI. You've just performed a {reading_data['spread']} tarot reading for someone seeking guidance. Speak as their personal tarot reader in first person.

The cards I've drawn for you are:

{cards_text}

Please respond as the spiritual guide, speaking directly to them:
1. Start with "I see the cards have revealed..." or similar personal opening
2. Give a simple summary of what this reading means in plain English (like "The cards are telling you to be a leader, try new stuff, listen to wise people, and trust yourself")
3. Provide 2-3 practical pieces of guidance as if you're personally advising them
4. End with an encouraging, mystical closing
5. Keep it warm, personal, and easy to understand - you're their spiritual companion

Speak as if you've personally drawn these cards for them and are interpreting their sacred message."""

        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a practical tarot interpreter who explains readings in simple, clear language."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=400
        )
        
        if response.choices and response.choices[0].message.content:
            return response.choices[0].message.content.strip()
        else:
            return "Unable to generate interpretation at this time."
            
    except Exception as e:
        return f"AI interpretation error: {str(e)}"

# -----------------------------
# Library Auto-Save
# -----------------------------
def save_reading_to_library(user_id: int, reading_data: Dict[str, Any]) -> bool:
    """Auto-save tarot reading to local file (standalone version)"""
    try:
        # Create title based on spread type and timestamp
        spread_name = reading_data.get('spread', 'Tarot Reading')
        now = datetime.now()
        timestamp = now.strftime('%B %d, %Y at %I:%M %p')
        filename = now.strftime('%Y%m%d_%H%M%S') + f"_{spread_name.replace(' ', '_')}.json"
        
        # Create readable content for display
        cards_summary = []
        for card in reading_data.get('cards', []):
            card_info = f"**{card['position']}**: {card['card']} ({card['orientation']})"
            cards_summary.append(card_info)
            
            # Include clarifiers if present
            if card.get('clarifiers'):
                for clarifier in card['clarifiers']:
                    card_info = f"  *Clarifier*: {clarifier['card']} ({clarifier['orientation']})"
                    cards_summary.append(card_info)
        
        readable_content = f"""**{spread_name} Tarot Reading**
**Date**: {timestamp}
**Reversals**: {'Enabled' if reading_data.get('reversals') else 'Disabled'}

**Cards Drawn**:
{chr(10).join(cards_summary)}"""

        # Add interpretation if available
        if reading_data.get('interpretation'):
            readable_content += f"\n\n**Your Personal Reading**:\n{reading_data['interpretation']}"
        
        # Prepare complete reading data for saving
        save_data = {
            'title': f"{spread_name} - {timestamp}",
            'timestamp': now.isoformat(),
            'readable_content': readable_content,
            'raw_data': reading_data,
            'metadata': {
                'spread_type': reading_data.get('spread'),
                'card_count': len(reading_data.get('cards', [])),
                'reversals': reading_data.get('reversals'),
                'clarifiers': reading_data.get('clarifiers_per_position', 0),
                'has_interpretation': bool(reading_data.get('interpretation'))
            }
        }
        
        # Save to file
        file_path = os.path.join(READINGS_DIR, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)
        
        return True
        
    except Exception as e:
        print(f"Failed to save reading to library: {e}")
        return False

# -----------------------------
# Flask App
# -----------------------------
app = Flask(__name__, static_folder=STATIC_DIR, static_url_path="/static")

# API blueprint
tarot_bp = Blueprint("tarot", __name__, url_prefix="/api/tarot")

@tarot_bp.get("/spreads")
def api_spreads():
    return jsonify({"spreads": {k: len(v) for k,v in SPREADS.items()}})

@tarot_bp.post("/reading") 
def api_reading():
    data = request.get_json(silent=True) or {}
    spread = str(data.get("spread", "3 Card"))
    reversals = bool(data.get("reversals", True))
    seed = data.get("seed")
    clarifiers = int(data.get("clarifiers", 0))
    allow_duplicates = bool(data.get("allow_duplicates", False))
    include_interpretation = bool(data.get("interpretation", False))
    user_id = data.get("user_id", 1)  # Default user for standalone app
    auto_save = bool(data.get("auto_save", True))  # Auto-save by default
    
    try:
        out = do_reading(spread, reversals, seed, clarifiers, allow_duplicates)
        
        # Add AI interpretation if requested
        if include_interpretation:
            out["interpretation"] = get_reading_interpretation(out)
        
        # Auto-save to library if enabled
        if auto_save:
            saved = save_reading_to_library(user_id, out)
            out["saved_to_library"] = saved
        
        return jsonify(out), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@tarot_bp.post("/interpret")
def api_interpret():
    """Get AI interpretation for an existing reading"""
    data = request.get_json(silent=True) or {}
    
    if not data.get("cards"):
        return jsonify({"error": "No cards provided for interpretation"}), 400
    
    try:
        interpretation = get_reading_interpretation(data)
        return jsonify({"interpretation": interpretation}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

app.register_blueprint(tarot_bp)

# -----------------------------
# Minimal UI (flip, images, reversals, clarifiers)
# -----------------------------
HTML = r"""
<!doctype html>
<html>
<head>
    <meta charset="utf-8" />
    <title>SoulBridge AI - Mystical Tarot Reading</title>
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600&family=Inter:wght@300;400;500&display=swap');
        
        :root {
            --gap: 14px;
            --card-w: 180px;
            --card-h: 300px;
            --radius: 12px;
            --primary: #6366f1;
            --primary-dark: #4f46e5;
            --secondary: #8b5cf6;
            --accent: #f59e0b;
            --dark: #1e1b4b;
            --darker: #0f0c29;
            --light: #f8fafc;
            --text-light: #e2e8f0;
        }
        
        body {
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
            margin: 0;
            color: var(--text-light);
            background: linear-gradient(135deg, var(--darker) 0%, var(--dark) 50%, #24184f 100%);
            min-height: 100vh;
            position: relative;
        }
        
        body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: 
                radial-gradient(circle at 20% 80%, rgba(120, 119, 198, 0.3) 0%, transparent 50%),
                radial-gradient(circle at 80% 20%, rgba(139, 92, 246, 0.3) 0%, transparent 50%),
                radial-gradient(circle at 40% 40%, rgba(245, 158, 11, 0.1) 0%, transparent 50%);
            pointer-events: none;
            z-index: -1;
        }
        
        header {
            padding: 24px;
            background: rgba(30, 27, 75, 0.8);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid rgba(139, 92, 246, 0.3);
            text-align: center;
        }
        
        h1 {
            font-family: 'Cinzel', serif;
            font-size: 2.5rem;
            font-weight: 600;
            margin: 0;
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 50%, var(--accent) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-shadow: 0 0 30px rgba(139, 92, 246, 0.5);
        }
        
        .subtitle {
            font-style: italic;
            color: var(--text-light);
            opacity: 0.8;
            margin-top: 8px;
            font-size: 1.1rem;
        }
        
        main {
            padding: 24px;
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .character-intro {
            background: rgba(30, 27, 75, 0.6);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(139, 92, 246, 0.3);
            border-radius: 16px;
            padding: 20px;
            margin-bottom: 24px;
            text-align: center;
        }
        
        .character-intro h2 {
            font-family: 'Cinzel', serif;
            color: var(--accent);
            margin: 0 0 12px 0;
            font-size: 1.5rem;
        }
        
        .row {
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
            align-items: end;
            margin-bottom: 24px;
        }
        
        .panel {
            background: rgba(30, 27, 75, 0.4);
            backdrop-filter: blur(8px);
            border: 1px solid rgba(139, 92, 246, 0.3);
            border-radius: 12px;
            padding: 16px;
        }
        
        label {
            color: var(--text-light);
            font-weight: 500;
            display: block;
            margin-bottom: 8px;
        }
        
        select, input[type="text"], input[type="number"] {
            padding: 10px 12px;
            border: 1px solid rgba(139, 92, 246, 0.4);
            border-radius: 8px;
            background: rgba(15, 12, 41, 0.8);
            color: var(--text-light);
            font-size: 14px;
            transition: all 0.3s ease;
        }
        
        select:focus, input:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
        }
        
        button {
            padding: 12px 24px;
            border: 0;
            border-radius: 10px;
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            color: white;
            cursor: pointer;
            font-weight: 600;
            font-size: 16px;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3);
        }
        
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(99, 102, 241, 0.4);
        }
        
        button:disabled {
            opacity: .6;
            cursor: not-allowed;
            transform: none;
        }
        
        .cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(var(--card-w), 1fr));
            gap: var(--gap);
            margin-top: 20px;
        }
        
        .card3d {
            width: var(--card-w);
            height: var(--card-h);
            perspective: 1000px;
            margin: 0 auto;
        }
        
        .inner {
            position: relative;
            width: 100%;
            height: 100%;
            transition: transform .7s ease;
            transform-style: preserve-3d;
            border-radius: var(--radius);
        }
        
        .flipped .inner {
            transform: rotateY(180deg);
        }
        
        .face {
            position: absolute;
            inset: 0;
            backface-visibility: hidden;
            border-radius: var(--radius);
            overflow: hidden;
            box-shadow: 0 8px 25px rgba(139, 92, 246, 0.3);
            border: 1px solid rgba(245, 158, 11, 0.4);
        }
        
        .face img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            display: block;
        }
        
        .back {
            transform: rotateY(180deg);
        }
        
        .meta {
            margin-top: 12px;
            font-size: 14px;
            background: rgba(30, 27, 75, 0.6);
            backdrop-filter: blur(8px);
            padding: 12px;
            border-radius: 8px;
            border: 1px solid rgba(139, 92, 246, 0.2);
        }
        
        .badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 999px;
            font-size: 11px;
            font-weight: 600;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: white;
            margin-right: 8px;
            margin-bottom: 4px;
        }
        
        .grid {
            display: grid;
            grid-template-columns: 1fr;
            gap: 8px;
        }
        
        .sym {
            color: #555;
            font-size: 13px;
        }
        
        .pos {
            font-weight: 600;
        }
        
        details {
            background: #fff;
            border: 1px solid #eee;
            border-radius: 10px;
            padding: 8px 10px;
        }
        
        footer {
            color: #777;
            font-size: 12px;
            padding: 20px;
            text-align: center;
        }
    </style>
</head>
<body>
    <header>
        <h1>✨ SoulBridge AI ✨</h1>
        <div class="subtitle">Mystical Tarot Reading Experience</div>
    </header>
    <main>
        <div class="character-intro">
            <h2 style="display: flex; align-items: center; gap: 12px; justify-content: center;">
                <img src="/static/logos/Fortune Teller Sky.png" style="width: 50px; height: 50px; border-radius: 50%; border: 2px solid var(--accent); box-shadow: 0 0 20px rgba(245, 158, 11, 0.4);" alt="Fortune Teller Sky">
                Welcome, seeker of wisdom
            </h2>
            <p>I am your spiritual guide, here to illuminate the path ahead through the ancient art of tarot. The cards hold profound insights waiting to be revealed. Let me draw the sacred cards and interpret their mystical messages for you...</p>
            <p><em>Choose your spread, focus your intention, and let the universe speak through the cards.</em></p>
        </div>
        
        <div class="row">
            <div class="panel">
                <label>Spread 
                    <select id="spread"></select>
                </label>
            </div>
            <div class="panel">
                <label><input type="checkbox" id="reversals" checked /> Include reversals</label>
            </div>
            <div class="panel">
                <label>Add clarifier card 
                    <input type="checkbox" id="clarifiers" />
                </label>
            </div>
            <div class="panel">
                <label><input type="checkbox" id="interpretation" checked /> AI Interpretation</label>
            </div>
            <div class="panel">
                <button id="draw">Draw Cards</button>
            </div>
        </div>
        <div id="reading"></div>
    </main>
    <footer>PNG tarot card images in <code>/static/tarot</code>. Click cards to flip. Reversed cards render rotated.</footer>

    <script>
        const API = "/api/tarot";
        const IMG_EXT = "{{ ext }}";
        const IMG_BASE = "/static/tarot/";
        const BACK_IMG = IMG_BASE + "back" + IMG_EXT;

        function cardUrl(slug) {
            return IMG_BASE + slug + IMG_EXT;
        }

        async function loadSpreads() {
            const r = await fetch(API + "/spreads");
            const d = await r.json();
            const sel = document.getElementById("spread");
            Object.entries(d.spreads).forEach(([name,count]) => {
                const o = document.createElement("option");
                o.value = name;
                o.textContent = `${name} (${count})`;
                sel.appendChild(o);
            });
            sel.value = "3 Card";
        }

        function cardHtml(item) {
            const rev = item.orientation === "Reversed";
            const flipClass = "card3d" + (rev ? " flipped" : "");
            const front = cardUrl(item.slug);
            const back = BACK_IMG;
            
            return `<div class="panel" style="padding:12px">
                <div class="${flipClass}" onclick="this.classList.toggle('flipped')">
                    <div class="inner">
                        <div class="face front"><img src="${front}" onerror="this.src='${back}'" alt="${item.card}" /></div>
                        <div class="face back"><img src="${back}" alt="Back" /></div>
                    </div>
                </div>
                <div class="meta">
                    <span class="badge">${item.position}</span>
                    <span class="badge">${item.orientation}</span>
                    <div><strong>${item.card}</strong></div>
                    <div class="grid">
                        <div>${item.meaning}</div>
                        ${item.symbols ? `<div class="sym"><strong>Symbols:</strong> ${item.symbols}</div>` : ""}
                    </div>
                </div>
                ${Array.isArray(item.clarifiers) && item.clarifiers.length ? `<details><summary>Clarifiers (${item.clarifiers.length})</summary>
                    <div class="cards">
                        ${item.clarifiers.map(c => `<div>
                            <div class="${c.orientation === "Reversed" ? "card3d flipped" : "card3d"}">
                                <div class="inner">
                                    <div class="face front"><img src="${cardUrl(c.slug)}" onerror="this.src='${back}'" alt="${c.card}" /></div>
                                    <div class="face back"><img src="${back}" alt="Back" /></div>
                                </div>
                            </div>
                            <div class="meta" style="text-align:center">
                                <span class="badge">${c.orientation}</span>
                                <div><small>${c.card}</small></div>
                            </div>
                        </div>`).join("")}
                    </div>
                </details>` : ""}
            </div>`;
        }

        async function draw() {
            const spread = document.getElementById("spread").value;
            const reversals = document.getElementById("reversals").checked;
            const clarifiers = document.getElementById("clarifiers").checked ? 1 : 0;
            const interpretation = document.getElementById("interpretation").checked;
            
            const body = { spread, reversals, clarifiers, interpretation };
            const r = await fetch(API + "/reading", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(body)
            });
            const d = await r.json();
            const wrap = document.getElementById("reading");
            
            if (d.error) {
                wrap.innerHTML = "<p style='color:#c00'>"+d.error+"</p>";
                return;
            }
            
            let html = `<div class="panel">
                <div><strong>${d.spread}</strong> • ${d.reversals ? "Reversals On" : "Reversals Off"} • ${d.timestamp}</div>
                ${d.clarifiers_per_position ? `<div>Clarifiers/pos: ${d.clarifiers_per_position}</div>` : ""}
                ${d.saved_to_library ? `<div style="color: var(--accent); font-size: 12px; margin-top: 4px; display: flex; align-items: center; gap: 6px;"><img src="/static/logos/Fortune Teller Sky.png" style="width: 16px; height: 16px; border-radius: 50%;" alt=""> Saved to your library</div>` : ""}
            </div>
            <div class="cards">${d.cards.map(cardHtml).join("")}</div>`;
            
            // Add AI interpretation if available
            if (d.interpretation) {
                html += `<div class="panel" style="margin-top: 24px; background: rgba(245, 158, 11, 0.1); border: 2px solid rgba(245, 158, 11, 0.3); backdrop-filter: blur(12px);">
                    <h3 style="color: var(--accent); margin-top: 0; font-family: 'Cinzel', serif; display: flex; align-items: center; gap: 12px;">
                        <img src="/static/logos/Fortune Teller Sky.png" style="width: 40px; height: 40px; border-radius: 50%; border: 2px solid var(--accent); box-shadow: 0 0 15px rgba(245, 158, 11, 0.4);" alt="Fortune Teller"> 
                        <span>Your Personal Reading</span>
                    </h3>
                    <div style="line-height: 1.7; color: var(--text-light); font-size: 16px; font-style: italic;">${d.interpretation.replace(/\n/g, '<br>')}</div>
                </div>`;
            }
            
            wrap.innerHTML = html;
        }

        document.getElementById("draw").addEventListener("click", draw);
        loadSpreads();
    </script>
</body>
</html>
"""

@app.get("/tarot")
def tarot_page():
    return render_template_string(HTML, ext=IMG_EXT)

# Optional: serve /static/* (Flask already serves static_url_path="/static")

# -----------------------------
# Run
# -----------------------------
if __name__ == "__main__":
    os.makedirs(TAROT_IMG_DIR, exist_ok=True)
    app.run(host="0.0.0.0", port=PORT, debug=True)