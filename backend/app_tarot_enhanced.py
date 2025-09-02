#!/usr/bin/env python3
"""
SoulBridge AI - Enhanced Tarot System (PNG Version)
Standalone complete tarot API + UI with 3D cards, reversals, clarifiers
Converted from JPG to PNG to match our organized tarot card system
"""

# Before running: put your images in static/tarot/ (see naming rules in comments below), 
# put your JSON in data/tarot_meanings_full.json, then run python app_tarot_enhanced.py.
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
# python app_tarot_enhanced.py
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

# -----------------------------
# Config
# -----------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
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
    
    try:
        out = do_reading(spread, reversals, seed, clarifiers, allow_duplicates)
        return jsonify(out), 200
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
    <title>SoulBridge AI - Tarot Reader</title>
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <style>
        :root {
            --gap: 14px;
            --card-w: 180px;
            --card-h: 300px;
            --radius: 12px;
        }
        
        body {
            font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
            margin: 0;
            color: #111;
            background: #fafafa;
        }
        
        header {
            padding: 16px;
            background: #111;
            color: #fff;
        }
        
        main {
            padding: 16px;
            max-width: 1100px;
            margin: 0 auto;
        }
        
        .row {
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
            align-items: end;
        }
        
        .panel {
            background: #fff;
            border: 1px solid #e5e5e5;
            border-radius: 12px;
            padding: 12px;
        }
        
        select, input[type="text"], input[type="number"] {
            padding: 8px 10px;
            border: 1px solid #ccc;
            border-radius: 8px;
        }
        
        button {
            padding: 10px 14px;
            border: 0;
            border-radius: 10px;
            background: #111;
            color: #fff;
            cursor: pointer;
        }
        
        button:disabled {
            opacity: .6;
            cursor: not-allowed;
        }
        
        .cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(var(--card-w), 1fr));
            gap: var(--gap);
            margin-top: 14px;
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
            transition: transform .7s;
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
            box-shadow: 0 8px 20px rgba(0,0,0,.1);
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
            margin-top: 8px;
            font-size: 14px;
        }
        
        .badge {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 999px;
            font-size: 12px;
            background: #f1f1f1;
            margin-right: 6px;
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
    <header><h1>SoulBridge AI - Tarot Reader</h1></header>
    <main>
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
                <label>Clarifiers / position 
                    <input type="number" id="clarifiers" min="0" max="3" value="0" style="width:70px" />
                </label>
            </div>
            <div class="panel">
                <label>Seed (optional) 
                    <input type="text" id="seed" placeholder="repeatable shuffle" />
                </label>
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
            const seed = document.getElementById("seed").value.trim() || null;
            const clarifiers = parseInt(document.getElementById("clarifiers").value || "0", 10);
            
            const body = { spread, reversals, seed, clarifiers };
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
            
            wrap.innerHTML = `<div class="panel">
                <div><strong>${d.spread}</strong> • ${d.reversals ? "Reversals On" : "Reversals Off"} • ${d.timestamp}</div>
                ${d.seed ? `<div>Seed: <code>${d.seed}</code></div>` : ""}
                ${d.clarifiers_per_position ? `<div>Clarifiers/pos: ${d.clarifiers_per_position}</div>` : ""}
            </div>
            <div class="cards">${d.cards.map(cardHtml).join("")}</div>`;
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