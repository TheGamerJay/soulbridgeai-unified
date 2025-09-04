# ================================
# BACKEND (Flask) — STRICT BEAT BRIEF (NO LYRIC ECHO)
# ================================
# File: backend/modules/beat/beat_brief_strict.py
import re
from flask import Blueprint, request, Response

brief_strict_bp = Blueprint("beat_brief_strict", __name__, url_prefix="/api/beat")

# ------------------ Core Maps ------------------
GENRE_INSTRUMENTS = {
    "trap": "808 kick & sub with glide, crisp snare/clap, closed-hat rolls (1/16–1/32), moody pads, sparse piano or pluck",
    "r&b": "soft punch kick, warm snare, brushed hats, round sub, electric piano, airy pads, clean guitar licks",
    "pop": "clean kick+clap, steady hats, bright bass, piano/synth chords, catchy pluck lead",
    "hip-hop": "fat kick, snappy snare, textured hats, sampled loops, warm bassline",
    "boom bap": "sampled drum breaks, acoustic snare, deep kick, upright bass, chopped soul/jazz loops",
    "drill": "sliding 808s, fast hi-hats with triplets, sharp snare, dark pads, minimal lead",
    "reggaeton": "dembow groove (syncopated kick/snare), bright claps/hats, short sub, keys/pads bed, clean pluck",
    "perreo": "heavy dembow drums, layered claps, distorted sub, metallic synth stabs",
    "dembow": "fast dembow pattern, loud claps/snares, plucky synths, club-ready sub",
    "latin trap": "trap 808s + hats, reggaetón-inspired percussion, Spanish guitar/piano accents",
    "bachata": "nylon/steel-string guitar arpeggios + requinto lead, güira driving high end, bongos/congas, warm bass, soft piano, romantic strings",
    "trapchata": "trap 808 kit layered with bachata guitars, airy pads, shaker/güira",
    "salsa": "timbales, congas, bongos, piano montuno, acoustic bass, punchy brass section",
    "afrobeats": "Afro drums, shakers, log-drum style bass, melodic plucks, rhythmic chord stabs",
    "amapiano": "deep kick, log-drum bass, shakers, soulful piano chords, airy pads",
    "house": "four-on-the-floor kick, bright hats, clap on 2&4, plucky bassline, wide pads",
    "tech house": "rolling kick, metallic hats, minimal claps, repetitive bass groove, FX risers",
    "future bass": "sidechained chords, bright synth leads, trap-style drums, pitched vocal chops",
    "dubstep": "half-time drums at 140, wobble/growl bass, sharp snares, heavy sub",
    "dnb": "fast breakbeats, tight snares, reese/sub bass, atmospheric pads",
    "synthwave": "retro drum machines, analog bass arps, lush pads, chorus-soaked leads",
    "hyperpop": "distorted drums, glitch FX, bright synths, pitched vox, heavy bass",
    "lo-fi hip-hop": "dusty drum loop, vinyl crackle, mellow keys, sub bass, chopped samples",
    "ambient": "long pads, evolving textures, drones, minimal/no drums",
    "cinematic": "strings, brass, big percussion, choirs, atmospheric layers, dramatic hits"
}

GENRE_BPM = {
    "trap": (82,98), "r&b": (72,88), "pop": (92,108), "hip-hop": (85,100), "boom bap": (85,95),
    "drill": (136,144), "reggaeton": (94,104), "perreo": (94,104), "dembow": (100,110),
    "latin trap": (82,98), "bachata": (86,94), "trapchata": (86,94), "salsa": (88,104),
    "afrobeats": (95,110), "amapiano": (110,115), "house": (118,125), "tech house": (120,125),
    "future bass": (140,160), "dubstep": (140,140), "dnb": (165,175), "synthwave": (80,115),
    "hyperpop": (160,200), "lo-fi hip-hop": (60,80), "ambient": (60,60), "cinematic": (100,100)
}

GENRE_STRUCTURE = {
    "trap":       ["Intro(4)","Hook(8)","Verse(16)","Hook(8)","Bridge(8)","Hook(8)","Outro(4)"],
    "r&b":        ["Intro(4)","Verse(16)","Pre(4)","Chorus(8)","Verse(16)","Bridge(8)","Chorus(8)","Outro(4)"],
    "pop":        ["Intro(4)","Verse(16)","Pre(4)","Chorus(8)","Verse(16)","Pre(4)","Chorus(8)","Bridge(8)","Chorus(8)"],
    "hip-hop":    ["Intro(4)","Verse(16)","Hook(8)","Verse(16)","Hook(8)","Outro(4)"],
    "boom bap":   ["Intro(4)","Verse(16)","Hook(8)","Verse(16)","Hook(8)","Verse(16)","Outro(4)"],
    "drill":      ["Intro(4)","Verse(16)","Hook(8)","Verse(16)","Hook(8)","Outro(4)"],
    "reggaeton":  ["Intro(4)","Pre(4)","Chorus(8)","Verse/Rap(16)","Pre(4)","Chorus(8)","Puente(8)","Chorus(8)"],
    "perreo":     ["Intro(4)","Chorus(8)","Verse/Rap(16)","Chorus(8)","Drop(4)","Chorus(8)"],
    "dembow":     ["Intro(4)","Chorus(8)","Verse(16)","Chorus(8)","Break(8)","Chorus(8)"],
    "latin trap": ["Intro(4)","Hook(8)","Verse(16)","Hook(8)","Bridge(8)","Hook(8)"],
    "bachata":    ["Intro(8)","Verso(16)","Coro(8)","Verso(16)","Coro(8)","Puente(8)","Coro(8)","Outro(8)"],
    "trapchata":  ["Intro(4)","Coro(8)","Verso(16)","Coro(8)","Puente(8)","Coro(8)"],
    "salsa":      ["Intro(4)","Verso(16)","Pre(4)","Coro(8)","Montuno(16)","Mambo(8)","Coro(8)","Cierre(4)"],
    "afrobeats":  ["Intro(4)","Chorus(8)","Verse(16)","Chorus(8)","Bridge(8)","Chorus(8)"],
    "amapiano":   ["Intro(8)","Groove(16)","Vocal(16)","Drop(8)","Groove(16)"],
    "house":      ["Intro(16)","Verse(16)","Build(8)","Drop(16)","Verse(16)","Build(8)","Drop(16)","Outro(16)"],
    "tech house": ["Intro(16)","Groove(16)","Break(8)","Drop(16)","Groove(16)","Outro(16)"],
    "future bass":["Intro(8)","Verse(16)","Build(8)","Drop(16)","Verse(16)","Build(8)","Drop(16)"],
    "dubstep":    ["Intro(8)","Build(8)","Drop(16)","Break(8)","Drop(16)","Outro(8)"],
    "dnb":        ["Intro(16)","DropA(32)","Break(16)","DropB(32)","Outro(16)"],
    "synthwave":  ["Intro(8)","Verse(16)","Chorus(8)","Verse(16)","Chorus(8)","Outro(8)"],
    "hyperpop":   ["Intro(4)","Verse(12)","Chorus(8)","Verse(12)","Chorus(8)","Bridge(8)","Chorus(8)"],
    "lo-fi hip-hop":["Intro(8)","LoopA(16)","LoopB(16)","LoopA(16)","Outro(8)"],
    "ambient":    ["TextureA(32)","TextureB(32)","TextureA(32)"],
    "cinematic":  ["Intro(8)","BuildI(16)","Climax(16)","BuildII(16)","Finale(16)"]
}

MOOD_MAP = {
    # user text -> safe descriptors we control (no echo of user words)
    "romantic": "romantic, sensual, heartfelt",
    "serious": "serious, intimate, reflective",
    "dark": "dark, moody, tense",
    "happy": "uplifting, bright, hopeful",
    "energetic": "energetic, driving, confident",
    "sad": "melancholic, emotional, tender"
}

# ------------------ Utilities ------------------
def _clean_text(s: str) -> str:
    s = s or ""
    s = re.sub(r"https?://\S+|@\w+","", s)
    return " ".join(s.split())

def _guess_genre(lyrics: str, style_hint: str) -> str:
    if style_hint:
        s = style_hint.strip().lower()
        # normalize a few common variants
        aliases = {"r&b":"r&b","reggaetón":"reggaeton","bachata":"bachata","latin trap":"latin trap",
                   "trapchata":"trapchata","hip hop":"hip-hop","lofi":"lo-fi hip-hop","lo-fi":"lo-fi hip-hop"}
        for k,v in aliases.items():
            if k in s: return v
        return s
    # default if no hint: trap
    t = lyrics.lower()
    if any(w in t for w in ["dembow","perreo","discoteca","reggaeton","reggaetón"]): return "reggaeton"
    if any(w in t for w in ["güira","guira","bachata","requinto"]): return "bachata"
    if any(w in t for w in ["drill","trrr","skrr"]): return "drill"
    if any(w in t for w in ["house","four on the floor","club"]): return "house"
    return "trap"

def _suggest_bpm(genre: str, bpm_override) -> int:
    if str(bpm_override).isdigit():
        return int(bpm_override)
    lo, hi = GENRE_BPM.get(genre, (90, 96))
    return max(60, min(200, (lo+hi)//2))

def _default_structure(genre: str) -> str:
    parts = GENRE_STRUCTURE.get(genre) or GENRE_STRUCTURE["trap"]
    return " \u2192 ".join(parts)  # → arrow

def _safe_mood(mood_hint: str) -> str:
    if not mood_hint: return "emotional, cinematic"
    key = mood_hint.strip().lower()
    return MOOD_MAP.get(key, "emotional, cinematic")

def _safe_key(user_key: str, genre: str) -> str:
    # Use provided key if it looks valid, else genre-based suggestion
    if user_key and re.match(r"^[A-G][#b]?\s*(major|minor)$", user_key.strip(), re.I):
        return user_key.strip().title()
    # defaults
    return "F minor" if genre in ("trap","drill","r&b","hyperpop","synthwave","dubstep","dnb","cinematic","lo-fi hip-hop") else "C major"

def _safe_time_sig(ts: str) -> str:
    if ts and re.match(r"^\d+/\d+$", ts.strip()):
        return ts.strip()
    return "4/4"

def _strict_non_echo(brief: str, user_text: str) -> str:
    """
    Remove any 3+ word sequences from the user text that accidentally appear in the brief.
    Ensures we never echo lyrics/prompt. Keeps brief readable.
    """
    t = " " + re.sub(r"\s+"," ", (user_text or "").lower()) + " "
    if not t.strip(): return brief
    brief_out = brief
    # collect simple 3-5 word n-grams from user text
    words = re.findall(r"[a-záéíóúñ]+", t.lower())
    grams = set()
    for n in (5,4,3):
        for i in range(len(words)-n+1):
            grams.add(" ".join(words[i:i+n]))
    for g in sorted(grams, key=len, reverse=True):
        if len(g) < 10:  # ignore tiny grams
            continue
        # replace if found in brief (case-insensitive)
        brief_out = re.sub(g, "", brief_out, flags=re.I)
    # collapse spaces
    brief_out = re.sub(r"\s{2,}", " ", brief_out).strip()
    return brief_out

def _trim_1k(s: str) -> str:
    s = re.sub(r"\s+"," ", s or "").strip()
    return s[:1000]

# ------------------ Main builder ------------------
def make_strict_brief(lyrics: str, mood: str, style: str, bpm, key_hint: str, time_sig: str, duration_sec) -> str:
    user_text = _clean_text(lyrics or "")
    genre = _guess_genre(user_text, style)
    bpm_val = _suggest_bpm(genre, bpm)
    key_val = _safe_key(key_hint, genre)
    ts_val = _safe_time_sig(time_sig)
    mood_val = _safe_mood(mood)
    instruments = GENRE_INSTRUMENTS.get(genre, GENRE_INSTRUMENTS["trap"])
    structure_line = _default_structure(genre)
    duration = int(duration_sec) if str(duration_sec).isdigit() else (150 if genre not in ("house","tech house","dnb") else 180)

    brief = (
        f"{genre.title()} beat, {bpm_val} BPM, {key_val}, {ts_val}. "
        f"Instruments: {instruments}. "
        f"Mood/Estado: {mood_val}. "
        f"Structure: {structure_line}. "
        f"Duration: ~{duration}s. "
        f"Mix: vocal space up front, sidechained sub to kick, wide pads/strings, mono bass <100Hz, warm master around -10 to -12 LUFS. "
        f"No artist names; does not use user lyrics."
    )

    # Strictly remove any accidental lyric/prompt overlap
    brief = _strict_non_echo(brief, user_text)
    # Final safety: length cap
    return _trim_1k(brief)

# ------------------ Endpoint ------------------
@brief_strict_bp.route("/brief_strict", methods=["POST"])
def brief_strict():
    """
    JSON in: { lyrics, mood?, style?, bpm?, key?, time_sig?, duration_sec? }
    Returns: text/plain (a strict, copy-ready beat description ≤ 1000 chars, no echo of user text)
    """
    data = request.get_json(silent=True) or {}
    brief = make_strict_brief(
        lyrics=data.get("lyrics","") or data.get("prompt",""),
        mood=data.get("mood",""),
        style=data.get("style",""),
        bpm=data.get("bpm"),
        key_hint=data.get("key",""),
        time_sig=data.get("time_sig",""),
        duration_sec=data.get("duration_sec")
    )
    return Response(brief, mimetype="text/plain; charset=utf-8")

# ---- Register once (e.g., in backend/app.py) ----
# from backend.modules.beat.beat_brief_strict import brief_strict_bp
# app.register_blueprint(brief_strict_bp)