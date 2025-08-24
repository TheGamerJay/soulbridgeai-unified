# =========================
# BACKEND (Flask / Python)
# file: routes_secretwriter.py
# =========================
from flask import Blueprint, request, jsonify, render_template, session, redirect
from datetime import datetime
import logging

secret = Blueprint("secret", __name__)
logger = logging.getLogger(__name__)

# LLM Call function (you'll need to import or define your actual LLM service)
def call_llm(prompt):
    """Call your LLM service with the given prompt"""
    # TODO: Replace with actual LLM service call
    # For now, return a placeholder
    return "SecretWriter response placeholder - integrate with your LLM service"

# Template prompts
FULL_SONG_TMPL = """You are SecretWriter, a professional AI songwriter specializing in {genre} music.

CREATE A COMPLETE ORIGINAL SONG with these specifications:
- Language: {language}
- Genre: {genre}
- Style: {style}  
- Mood: {mood}
- Tempo: {tempo_bpm} BPM ({tempo_feel})
- Perspective: {perspective}
- Key Themes: {themes}
- Rhyme Level: {rhyme_level}
- Structure: {structure}
- Content Guidelines: {boundaries}
- Bilingual Mode: {bilingual} {bilingual_note}

REQUIREMENTS:
- Professional radio-ready quality lyrics
- Complex internal rhymes and multisyllabic patterns
- Cinematic storytelling with vivid imagery
- Strong hooks and memorable choruses
- Smooth transitions between sections
- Emotional depth and authentic expression

Return ONLY the complete song lyrics with clearly marked sections."""

FIX_SONG_TMPL = """You are SecretWriter. POLISH AND IMPROVE this complete song:

Target: {genre} | Style: {style} | Mood: {mood} | Language: {language}

IMPROVEMENTS NEEDED:
- Enhance rhyme schemes and internal rhymes
- Strengthen weak lines and improve flow
- Boost emotional impact and imagery
- Fix any awkward phrasing or rhythm issues
- Maintain original structure and concept

[Full Song To Improve]
{full_song}

Return the COMPLETE IMPROVED VERSION with all sections."""

FIX_PART_TMPL = """You are SecretWriter. REWRITE this specific section to be much better:

Target: {genre} | Style: {style} | Mood: {mood} | Language: {language}

CONTEXT (Full Song):
{full_song}

[Selected Section To Rewrite]
{section}

Return ONLY the improved version of this section."""

SUGGESTIONS_TMPL = """You are SecretWriter. Analyze the FULL SONG and suggest concrete improvements:
- punchlines, multisyllabic chains, internal rhymes
- stronger metaphors, cleaner prosody, tighter imagery
- section transitions, hook lift ideas, motif callbacks
Give bullet lists + a few sample replacement lines (don't rewrite everything).
Target genre: {genre}; style vibe: {style}; mood: {mood}; language: {language}.        
Return suggestions only.

[Full Song]
{full_song}"""

# ---------- Builders ----------
def _field(data, key, default):
    v = data.get(key)
    return default if v in (None, "", []) else v

def build_full_song_prompt(data):
    # Smart defaults aligned with your usual vibe
    language     = _field(data, "language", "Spanish (Puerto Rican style)")
    genre        = _field(data, "genre", "Melodic Trap / Bachata Fusion")
    style        = _field(data, "style", "emotional, cinematic, modern")
    mood         = _field(data, "mood", "romantic, hopeful")
    tempo_bpm    = _field(data, "tempo_bpm", "88")
    tempo_feel   = _field(data, "tempo_feel", "slow dembow / halftime")
    perspective  = _field(data, "perspective", "first person")
    themes       = _field(data, "themes", "amor verdadero, sanación, destino")
    rhyme_level  = _field(data, "rhyme_level", "complex multisyllabic with internal rhymes")
    structure    = _field(data, "structure", "Intro, Verse, Pre, Chorus, Verse, Bridge, Chorus, Outro")
    boundaries   = _field(data, "boundaries", "no explicit content")
    bilingual    = bool(data.get("bilingual", False))
    bilingual_note = "(Blend English hooks with Spanish verses naturally.)" if bilingual else ""
    return FULL_SONG_TMPL.format(
        language=language, genre=genre, style=style, mood=mood,
        tempo_bpm=tempo_bpm, tempo_feel=tempo_feel, perspective=perspective,
        themes=themes, rhyme_level=rhyme_level, structure=structure,
        boundaries=boundaries, bilingual="ON" if bilingual else "OFF",
        bilingual_note=bilingual_note
    )

def build_fix_song_prompt(data):
    return FIX_SONG_TMPL.format(
        genre=_field(data, "genre", "User's original genre"),
        style=_field(data, "style", "polished, modern, cinematic"),
        mood=_field(data, "mood", "match original"),
        language=_field(data, "language", "match original"),
        full_song=_field(data, "full_song", "")
    )

def build_fix_part_prompt(data):
    return FIX_PART_TMPL.format(
        genre=_field(data, "genre", "match original"),
        style=_field(data, "style", "match original"),
        mood=_field(data, "mood", "match original"),
        language=_field(data, "language", "match original"),
        full_song=_field(data, "full_song", ""),
        section=_field(data, "section", "")
    )

def build_suggestions_prompt(data):
    return SUGGESTIONS_TMPL.format(
        genre=_field(data, "genre", "match original"),
        style=_field(data, "style", "match original"),
        mood=_field(data, "mood", "match original"),
        language=_field(data, "language", "match original"),
        full_song=_field(data, "full_song", "")
    )

# ---------- Page Route ----------
@secret.route("/secretwriter")
def secretwriter_page():
    """SecretWriter main interface"""
    return render_template("secretwriter.html")

# ---------- API Routes ----------
@secret.route("/api/secretwriter/full-song", methods=["POST"])
def secretwriter_full_song():
    data   = request.get_json(force=True) or {}
    prompt = build_full_song_prompt(data)
    out    = call_llm(prompt)
    return jsonify({"ok": True, "output": out})

@secret.route("/api/secretwriter/fix-song", methods=["POST"])
def secretwriter_fix_song():
    data   = request.get_json(force=True) or {}
    prompt = build_fix_song_prompt(data)
    out    = call_llm(prompt)
    return jsonify({"ok": True, "output": out})

@secret.route("/api/secretwriter/fix-part", methods=["POST"])
def secretwriter_fix_part():
    data   = request.get_json(force=True) or {}
    prompt = build_fix_part_prompt(data)
    out    = call_llm(prompt)
    return jsonify({"ok": True, "output": out})

@secret.route("/api/secretwriter/suggestions", methods=["POST"])
def secretwriter_suggestions():
    data   = request.get_json(force=True) or {}
    prompt = build_suggestions_prompt(data)
    out    = call_llm(prompt)
    return jsonify({"ok": True, "output": out})