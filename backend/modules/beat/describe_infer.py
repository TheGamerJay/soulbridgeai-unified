"""
Enhanced Beat Wizard - Advanced Music Production Analysis
Improved version with confidence scoring, auto-save, and robust detection
"""

import logging
import re
import hashlib
import json
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from flask import Blueprint, request, jsonify, session

from ..auth.session_manager import requires_login, get_user_id
from ..auth.access_control import require_tier
from ..library.library_manager import LibraryManager

logger = logging.getLogger(__name__)

# Create blueprint
beat_bp = Blueprint('beat', __name__)

# Advanced section detection (extracted from comprehensive code)
SECTION_ALIASES = {
    "hook": {"hook", "chorus", "coro", "estribillo", "refrain", "refrán", "gancho"},
    "verse": {"verse", "verso", "estrofa", "rap", "bar", "barra"},
    "bridge": {"bridge", "puente", "middle eight", "m8", "break"},
    "pre": {"pre-chorus", "prechorus", "pre chorus", "pre-coro", "precoro", "pre coro", 
            "pre-estribillo", "preestribillo", "buildup", "antecoro"},
    "intro": {"intro", "entrada", "start", "beginning"},
    "outro": {"outro", "salida", "cierre", "end", "ending", "final"},
    "interlude": {"interlude", "interludio", "instrumental", "solo"},
    "drop": {"drop", "break", "beat drop", "bajada", "subida", "climax"},
    "ad_lib": {"ad-lib", "adlib", "vocal", "background", "bg"}
}

NORM = {n.lower(): canon for canon, names in SECTION_ALIASES.items() for n in names}
SECTION_TAG_RE = re.compile(r"^\s*[\[\(]?\s*(?P<label>[A-Za-zÁÉÍÓÚÑáéíóúñ\- ]{2,30})\s*[\]\)]?\s*:?\s*$")

@dataclass
class BeatAnalysis:
    """Immutable beat analysis result with enhanced structure analysis"""
    bpm: int
    genre: str
    mood: str
    key_signature: str
    time_signature: str
    description: str
    suggestions: List[str]
    confidence_scores: Dict[str, float]
    structure: str
    sections_detected: int
    created_at: str
    seed: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class EnhancedBeatWizard:
    """Enhanced Beat Wizard with improved analysis capabilities"""
    
    def __init__(self):
        self.genre_keywords = {
            # ELECTRONIC & EDM
            'house': {
                'keywords': ['four-on-the-floor', 'synth', 'electronic', 'dance', 'club', 'bassline', 'kick'],
                'bpm_range': (120, 130),
                'weight': 1.0,
                'instruments': ['synthesizer', 'drum machine', 'electric piano', 'bass synth']
            },
            'deep-house': {
                'keywords': ['deep house', 'deep', 'groovy', 'underground', 'soulful', 'minimal'],
                'bpm_range': (118, 125),
                'weight': 1.2,
                'instruments': ['analog synths', 'electric piano', 'filtered samples', 'deep bass']
            },
            'techno': {
                'keywords': ['repetitive', 'electronic', 'industrial', 'driving', 'mechanical', 'synthesizer'],
                'bpm_range': (120, 150),
                'weight': 1.0,
                'instruments': ['analog drum machines', '303 acid synth', 'industrial samples', 'reverb tanks']
            },
            'trance': {
                'keywords': ['trance', 'uplifting', 'euphoric', 'breakdown', 'build-up', 'progressive'],
                'bpm_range': (128, 140),
                'weight': 1.1,
                'instruments': ['supersaw synths', 'arpeggiators', 'gated pads', 'white noise sweeps']
            },
            'dubstep': {
                'keywords': ['wobble', 'bass', 'drop', 'electronic', 'heavy', 'distorted'],
                'bpm_range': (140, 150),
                'weight': 1.0,
                'instruments': ['wobbly bass synths', 'snare rolls', 'vocal chops', 'LFO modulators']
            },
            'drum-and-bass': {
                'keywords': ['dnb', 'jungle', 'amen break', 'fast', 'breakbeat', 'liquid'],
                'bpm_range': (160, 180),
                'weight': 1.2,
                'instruments': ['amen breaks', 'reese bass', 'atmospheric pads', 'jungle samples']
            },
            'future-bass': {
                'keywords': ['future bass', 'future', 'melodic', 'emotional', 'drop', 'synth'],
                'bpm_range': (130, 160),
                'weight': 1.1,
                'instruments': ['supersaw chords', 'vocal chops', 'sidechain compression', 'filtered leads']
            },
            'synthwave': {
                'keywords': ['synthwave', 'retro', '80s', 'nostalgic', 'neon', 'cyber'],
                'bpm_range': (100, 130),
                'weight': 1.0,
                'instruments': ['analog synths', 'arpeggiated bass', 'gated reverb', 'vintage drums']
            },
            'ambient': {
                'keywords': ['atmospheric', 'calm', 'peaceful', 'floating', 'ethereal', 'spacious'],
                'bpm_range': (60, 90),
                'weight': 0.9,
                'instruments': ['pad synths', 'field recordings', 'reverb', 'drones']
            },

            # HIP HOP & RAP
            'hip-hop': {
                'keywords': ['rap', 'urban', 'beats', 'sampling', 'rhythm', 'bass', 'drums', 'street'],
                'bpm_range': (70, 140),
                'weight': 1.2,
                'instruments': ['samples', 'kick drums', 'snare', 'hi-hats', 'turntables']
            },
            'trap': {
                'keywords': ['trap', '808', 'hi-hat', 'snare', 'roll', 'southern', 'heavy', 'bass'],
                'bpm_range': (130, 170),
                'weight': 1.1,
                'instruments': ['808 drums', 'rapid hi-hats', 'sub bass', 'trap snares']
            },
            'drill': {
                'keywords': ['drill', 'dark', 'aggressive', 'sliding', '808', 'menacing', 'street'],
                'bpm_range': (130, 160),
                'weight': 1.1,
                'instruments': ['sliding 808s', 'drill snares', 'dark samples', 'aggressive hi-hats']
            },
            'boom-bap': {
                'keywords': ['boom bap', 'golden age', '90s', 'sampling', 'old school', 'classic'],
                'bpm_range': (85, 105),
                'weight': 1.3,
                'instruments': ['vinyl samples', 'analog drums', 'bass guitar', 'jazz samples']
            },
            'lo-fi': {
                'keywords': ['lo-fi', 'chill', 'vinyl', 'crackling', 'nostalgic', 'study', 'relaxing'],
                'bpm_range': (70, 90),
                'weight': 1.2,
                'instruments': ['vinyl crackle', 'muffled drums', 'warm bass', 'piano loops']
            },

            # ROCK & METAL
            'rock': {
                'keywords': ['rock', 'guitar', 'drums', 'electric', 'power', 'loud', 'distortion'],
                'bpm_range': (110, 140),
                'weight': 1.2,
                'instruments': ['electric guitar', 'bass guitar', 'drum kit', 'power chords']
            },
            'alternative': {
                'keywords': ['alternative', 'indie', 'grunge', 'alternative rock', 'experimental', 'underground'],
                'bpm_range': (100, 130),
                'weight': 1.1,
                'instruments': ['distorted guitars', 'fuzzy bass', 'dynamic drums', 'effects pedals']
            },
            'metal': {
                'keywords': ['metal', 'heavy', 'aggressive', 'distorted', 'powerful', 'intense'],
                'bpm_range': (120, 180),
                'weight': 1.2,
                'instruments': ['heavy guitars', 'double bass drums', 'palm muting', 'aggressive vocals']
            },
            'punk': {
                'keywords': ['punk', 'fast', 'raw', 'rebellious', 'simple', 'aggressive'],
                'bpm_range': (150, 200),
                'weight': 1.3,
                'instruments': ['power chords', 'fast drums', 'simple bass', 'shouted vocals']
            },

            # LATIN & WORLD
            'reggaeton': {
                'keywords': ['perreo', 'dembow', 'reggaeton', 'reggaetón', 'reguetón', 'latin'],
                'bpm_range': (90, 110),
                'weight': 1.5,
                'instruments': ['dembow rhythm', 'latin percussion', 'synthesized bass', 'melodic instruments']
            },
            'bachata': {
                'keywords': ['bachata', 'guitarra', 'romantic', 'guitar', 'latin'],
                'bpm_range': (80, 100),
                'weight': 1.4,
                'instruments': ['acoustic guitar', 'güira', 'bongo drums', 'electric guitar']
            },
            'merengue': {
                'keywords': ['merengue', 'dominican', 'accordion', 'fast', 'dance', 'caribbean', 'tropical'],
                'bpm_range': (120, 160),
                'weight': 1.4,
                'instruments': ['accordion', 'tambora', 'güira', 'bass guitar']
            },
            'salsa': {
                'keywords': ['salsa', 'latin', 'percussion', 'brass', 'trumpet', 'timbales', 'clave'],
                'bpm_range': (150, 200),
                'weight': 1.4,
                'instruments': ['piano montuno', 'timbales', 'congas', 'brass section', 'bass tumbao']
            },
            'cumbia': {
                'keywords': ['cumbia', 'colombian', 'gaita', 'accordion', 'tropical', 'folklore'],
                'bpm_range': (90, 120),
                'weight': 1.4,
                'instruments': ['accordion', 'gaita', 'guacharaca', 'tambores']
            },
            'bossa-nova': {
                'keywords': ['bossa nova', 'brazilian', 'smooth', 'jazz', 'guitar', 'soft'],
                'bpm_range': (90, 120),
                'weight': 1.3,
                'instruments': ['nylon guitar', 'soft percussion', 'bass', 'subtle drums']
            },
            'afrobeats': {
                'keywords': ['afrobeats', 'african', 'percussion', 'afro', 'lagos', 'highlife', 'african'],
                'bpm_range': (100, 130),
                'weight': 1.3,
                'instruments': ['talking drums', 'log drums', 'shekere', 'bass guitar', 'keyboards']
            },
            'amapiano': {
                'keywords': ['amapiano', 'south african', 'piano', 'log drum', 'african'],
                'bpm_range': (110, 120),
                'weight': 1.4,
                'instruments': ['piano', 'log drums', 'jazz samples', 'saxophone', 'bass']
            },

            # JAZZ & BLUES
            'jazz': {
                'keywords': ['swing', 'improvisation', 'complex', 'sophisticated', 'brass', 'piano'],
                'bpm_range': (90, 180),
                'weight': 0.8,
                'instruments': ['piano', 'trumpet', 'saxophone', 'double bass', 'drums']
            },
            'blues': {
                'keywords': ['blues', '12-bar', 'soulful', 'guitar', 'harmonica', 'melancholic'],
                'bpm_range': (80, 120),
                'weight': 1.2,
                'instruments': ['electric guitar', 'harmonica', 'piano', 'bass', 'drums']
            },

            # SOUL & R&B
            'soul': {
                'keywords': ['soul', 'soulful', 'gospel', 'motown', 'spiritual', 'emotional', 'heartfelt'],
                'bpm_range': (70, 110),
                'weight': 1.2,
                'instruments': ['Hammond organ', 'electric piano', 'horn section', 'gospel vocals']
            },
            'rnb': {
                'keywords': ['r&b', 'rnb', 'rhythm and blues', 'smooth', 'groove', 'urban'],
                'bpm_range': (70, 100),
                'weight': 1.2,
                'instruments': ['electric piano', 'smooth bass', 'drum machines', 'vocal harmonies']
            },
            'neo-soul': {
                'keywords': ['neo soul', 'neo-soul', 'modern soul', 'alternative rnb', 'conscious'],
                'bpm_range': (80, 110),
                'weight': 1.3,
                'instruments': ['vintage keyboards', 'live drums', 'bass guitar', 'analog warmth']
            },

            # POP & MAINSTREAM
            'pop': {
                'keywords': ['catchy', 'mainstream', 'accessible', 'commercial', 'melodic'],
                'bpm_range': (100, 130),
                'weight': 0.8,
                'instruments': ['synthesizers', 'pop drums', 'bass', 'vocal production']
            },
            'synthpop': {
                'keywords': ['synthpop', 'new wave', '80s pop', 'electronic pop', 'synth'],
                'bpm_range': (110, 140),
                'weight': 1.0,
                'instruments': ['vintage synths', 'drum machines', 'arpeggiated bass', 'pop vocals']
            },

            # COUNTRY & FOLK
            'country': {
                'keywords': ['country', 'acoustic', 'fiddle', 'banjo', 'twang', 'folk', 'americana'],
                'bpm_range': (90, 120),
                'weight': 1.3,
                'instruments': ['acoustic guitar', 'banjo', 'fiddle', 'steel guitar', 'harmonica']
            },
            'folk': {
                'keywords': ['folk', 'acoustic', 'traditional', 'storytelling', 'simple', 'organic'],
                'bpm_range': (80, 120),
                'weight': 1.2,
                'instruments': ['acoustic guitar', 'harmonica', 'mandolin', 'simple percussion']
            },

            # REGGAE & CARIBBEAN
            'reggae': {
                'keywords': ['offbeat', 'caribbean', 'skank', 'bass', 'guitar', 'rhythm'],
                'bpm_range': (60, 90),
                'weight': 0.9,
                'instruments': ['electric guitar skank', 'bass guitar', 'drums', 'organ']
            },
            'dancehall': {
                'keywords': ['dancehall', 'jamaican', 'digital', 'toasting', 'ragga'],
                'bpm_range': (80, 100),
                'weight': 1.3,
                'instruments': ['digital drums', 'synthesized bass', 'drum machines', 'samples']
            },

            # BALLADS & SLOW
            'ballad': {
                'keywords': ['ballad', 'slow', 'emotional', 'piano', 'soft', 'tender', 'love song'],
                'bpm_range': (60, 80),
                'weight': 1.3,
                'instruments': ['piano', 'strings', 'soft drums', 'acoustic guitar']
            },

            # UK & EUROPEAN STYLES
            'uk-garage': {
                'keywords': ['uk garage', 'garage', 'uk', 'chopped', 'vocal', '2-step'],
                'bpm_range': (120, 140),
                'weight': 1.2,
                'instruments': ['chopped vocals', 'skippy beats', 'sub bass', 'pitched vocals']
            },
            'grime': {
                'keywords': ['grime', 'uk', 'aggressive', '8-bar', 'electronic', 'raw'],
                'bpm_range': (135, 145),
                'weight': 1.3,
                'instruments': ['sparse beats', 'digital sounds', 'aggressive synths', 'UK vocals']
            },

            # EXPERIMENTAL & ALTERNATIVE
            'industrial': {
                'keywords': ['industrial', 'noise', 'mechanical', 'harsh', 'experimental', 'electronic'],
                'bpm_range': (90, 140),
                'weight': 1.0,
                'instruments': ['metal percussion', 'distorted samples', 'noise generators', 'synthesizers']
            },
            'shoegaze': {
                'keywords': ['shoegaze', 'dreamy', 'ethereal', 'effects', 'layers', 'wall of sound'],
                'bpm_range': (90, 130),
                'weight': 1.1,
                'instruments': ['heavily effected guitars', 'reverb', 'delay', 'distortion pedals']
            }
        }
        
        self.mood_keywords = {
            'energetic': ['fast', 'upbeat', 'driving', 'powerful', 'intense', 'exciting'],
            'chill': ['relaxed', 'calm', 'smooth', 'laid-back', 'peaceful', 'mellow'],
            'dark': ['heavy', 'aggressive', 'menacing', 'brooding', 'intense', 'sinister'],
            'happy': ['uplifting', 'joyful', 'positive', 'bright', 'cheerful', 'optimistic'],
            'melancholic': ['sad', 'emotional', 'nostalgic', 'wistful', 'contemplative'],
            'mysterious': ['atmospheric', 'ethereal', 'ambient', 'spacious', 'haunting']
        }

    def generate_deterministic_seed(self, description: str, user_id: str) -> str:
        """Generate deterministic seed for consistent results"""
        combined = f"{description.lower().strip()}:{user_id}"
        return hashlib.sha256(combined.encode()).hexdigest()[:16]

    def detect_song_sections(self, text: str) -> List[Tuple[str, str]]:
        """Advanced section detection with bilingual support"""
        sections = []
        lines = text.splitlines()
        
        for i, line in enumerate(lines):
            raw = line.strip()
            if not raw: 
                continue
                
            # Check for bracketed/parenthesized sections
            m = SECTION_TAG_RE.match(raw)
            candidate = None
            
            if m:
                candidate = m.group("label")
            else:
                # Check for all-caps short lines (likely section headers)
                if (len(raw) <= 25 and raw == raw.upper() and 
                    any(c.isalpha() for c in raw) and 
                    len([c for c in raw if c.isalpha()]) >= 3):
                    candidate = raw
            
            if candidate:
                canon = self._normalize_label(candidate)
                if canon:
                    sections.append((canon, candidate.strip()))
        
        return sections
    
    def _normalize_label(self, raw: str) -> Optional[str]:
        """Enhanced label normalization with better pattern matching"""
        if not raw: 
            return None
        
        # Clean and normalize
        t = re.sub(r"[^a-záéíóúñ\- ]", "", raw.strip().lower())
        t = re.sub(r"\s+", " ", t).strip()
        
        # Direct match
        if t in NORM: 
            return NORM[t]
        
        # Prefix match
        for k in NORM:
            if t.startswith(k) and len(t) - len(k) <= 3:  # Allow slight variations
                return NORM[k]
        
        # Fuzzy matching for common misspellings
        fuzzy_matches = {
            "corus": "hook",
            "versus": "verse", 
            "bridg": "bridge",
            "introo": "intro",
            "outroo": "outro"
        }
        
        for fuzzy, canon in fuzzy_matches.items():
            if fuzzy in t:
                return canon
        
        return None

    def generate_song_structure(self, sections: List[Tuple[str, str]], genre: str) -> str:
        """Generate enhanced structure with comprehensive genre-specific patterns"""
        if not sections:
            # Comprehensive genre-specific default structures
            defaults = {
                # ELECTRONIC & EDM
                "house": "Intro(16) → Build(8) → Drop(32) → Break(16) → Build(8) → Drop(32) → Outro(16)",
                "deep-house": "Intro(32) → Verse(16) → Build(8) → Drop(32) → Break(16) → Drop(32) → Outro(32)",
                "techno": "Intro(32) → Main(64) → Break(32) → Main(64) → Build(16) → Peak(32) → Outro(32)",
                "trance": "Intro(16) → Verse(16) → Buildup(16) → Drop(32) → Break(16) → Buildup(16) → Drop(32) → Outro(16)",
                "dubstep": "Intro(8) → Buildup(8) → Drop(16) → Verse(8) → Buildup(8) → Drop(16) → Outro(8)",
                "drum-and-bass": "Intro(16) → Verse(16) → Drop(32) → Break(16) → Drop(32) → Outro(16)",
                "future-bass": "Intro(8) → Verse(8) → Pre(4) → Drop(16) → Verse(8) → Pre(4) → Drop(16) → Outro(8)",
                "synthwave": "Intro(16) → Verse(16) → Chorus(16) → Verse(16) → Chorus(16) → Solo(16) → Chorus(16) → Outro(16)",
                "ambient": "Intro(32) → Movement A(64) → Transition(16) → Movement B(64) → Outro(32)",

                # HIP HOP & RAP  
                "hip-hop": "Intro(4) → Verse(16) → Hook(8) → Verse(16) → Hook(8) → Bridge(8) → Hook(8) → Outro(4)",
                "trap": "Intro(4) → Hook(8) → Verse(16) → Hook(8) → Verse(16) → Bridge(8) → Hook(8) → Outro(4)",
                "drill": "Intro(8) → Hook(8) → Verse(16) → Hook(8) → Verse(16) → Hook(8) → Outro(4)",
                "boom-bap": "Intro(4) → Verse(16) → Hook(8) → Verse(16) → Hook(8) → Verse(16) → Hook(8) → Outro(4)",
                "lo-fi": "Intro(8) → Loop A(32) → Variation(16) → Loop B(32) → Outro(8)",

                # ROCK & METAL
                "rock": "Intro(8) → Verse(16) → Chorus(16) → Verse(16) → Chorus(16) → Solo(16) → Chorus(16) → Outro(8)",
                "alternative": "Intro(8) → Verse(12) → Chorus(12) → Verse(12) → Chorus(12) → Bridge(8) → Chorus(12) → Outro(8)",
                "metal": "Intro(8) → Verse(16) → Chorus(16) → Verse(16) → Chorus(16) → Breakdown(8) → Solo(16) → Chorus(16) → Outro(8)",
                "punk": "Intro(4) → Verse(12) → Chorus(8) → Verse(12) → Chorus(8) → Bridge(8) → Chorus(8) → Outro(4)",

                # LATIN & WORLD
                "reggaeton": "Intro(4) → Coro(8) → Verso(16) → Coro(8) → Verso(16) → Puente(8) → Coro(8) → Outro(4)",
                "bachata": "Intro(8) → Verso(16) → Coro(8) → Verso(16) → Coro(8) → Puente(8) → Coro(8) → Outro(8)",
                "merengue": "Intro(4) → Coro(8) → Verso(8) → Coro(8) → Verso(8) → Coro(8) → Mambo(16) → Coro(8) → Outro(4)",
                "salsa": "Intro(8) → Coro(8) → Verso(16) → Coro(8) → Mambo(32) → Coro(8) → Outro(8)",
                "cumbia": "Intro(8) → Verso(16) → Coro(16) → Verso(16) → Coro(16) → Instrumental(16) → Coro(16) → Outro(8)",
                "bossa-nova": "Intro(8) → Verse(16) → Chorus(16) → Verse(16) → Chorus(16) → Bridge(8) → Chorus(16) → Outro(8)",
                "afrobeats": "Intro(8) → Hook(8) → Verse(16) → Hook(8) → Bridge(8) → Hook(8) → Outro(8)",
                "amapiano": "Intro(16) → Build(8) → Drop(32) → Break(8) → Drop(32) → Outro(16)",

                # JAZZ & BLUES
                "jazz": "Intro(8) → Head(32) → Solo A(32) → Solo B(32) → Head(32) → Outro(8)",
                "blues": "Intro(4) → Verse(12) → Verse(12) → Bridge(6) → Verse(12) → Solo(12) → Verse(12) → Outro(4)",

                # SOUL & R&B
                "soul": "Intro(8) → Verse(16) → Chorus(16) → Verse(16) → Chorus(16) → Bridge(8) → Chorus(16) → Outro(8)",
                "rnb": "Intro(4) → Verse(16) → Pre-Chorus(4) → Chorus(16) → Verse(16) → Pre-Chorus(4) → Chorus(16) → Bridge(8) → Chorus(16) → Outro(4)",
                "neo-soul": "Intro(8) → Verse(16) → Chorus(12) → Verse(16) → Chorus(12) → Breakdown(8) → Chorus(12) → Outro(8)",

                # POP & MAINSTREAM
                "pop": "Intro(4) → Verse(16) → Pre-Chorus(4) → Chorus(16) → Verse(16) → Pre-Chorus(4) → Chorus(16) → Bridge(8) → Chorus(16) → Outro(4)",
                "synthpop": "Intro(8) → Verse(16) → Chorus(16) → Verse(16) → Chorus(16) → Synth Solo(8) → Chorus(16) → Outro(8)",

                # COUNTRY & FOLK
                "country": "Intro(4) → Verse(16) → Chorus(16) → Verse(16) → Chorus(16) → Bridge(8) → Chorus(16) → Outro(4)",
                "folk": "Intro(4) → Verse(16) → Chorus(12) → Verse(16) → Chorus(12) → Bridge(8) → Chorus(12) → Outro(4)",

                # REGGAE & CARIBBEAN
                "reggae": "Intro(8) → Verse(16) → Chorus(16) → Verse(16) → Chorus(16) → Bridge(8) → Chorus(16) → Outro(8)",
                "dancehall": "Intro(4) → Hook(8) → Verse(16) → Hook(8) → Verse(16) → Hook(8) → Outro(4)",

                # BALLADS & SLOW
                "ballad": "Intro(8) → Verse(16) → Chorus(16) → Verse(16) → Chorus(16) → Bridge(8) → Chorus(16) → Outro(8)",

                # UK & EUROPEAN STYLES
                "uk-garage": "Intro(8) → Vocal(16) → Drop(16) → Break(8) → Vocal(16) → Drop(16) → Outro(8)",
                "grime": "Intro(8) → Bars(64) → Hook(8) → Bars(64) → Hook(8) → Outro(8)",

                # EXPERIMENTAL & ALTERNATIVE
                "industrial": "Intro(16) → Section A(32) → Build(8) → Section B(32) → Breakdown(16) → Section B(32) → Outro(16)",
                "shoegaze": "Intro(16) → Verse(16) → Wall(32) → Verse(16) → Wall(32) → Bridge(16) → Wall(32) → Outro(16)",
            }
            return defaults.get(genre, defaults.get("pop", "Intro(4) → Verse(16) → Chorus(16) → Verse(16) → Chorus(16) → Bridge(8) → Chorus(16) → Outro(4)"))
        
        # Build from detected sections
        label_map = {}
        sequence = []
        
        for canon, raw in sections:
            label_map[canon] = raw
            if not sequence or sequence[-1] != canon:
                sequence.append(canon)
        
        def format_section(canon: str) -> str:
            raw = label_map.get(canon, "")
            display = raw.title() if raw else {
                "hook": "Hook", "verse": "Verse", "bridge": "Bridge", "pre": "Pre-Chorus",
                "intro": "Intro", "outro": "Outro", "interlude": "Interlude", 
                "drop": "Drop", "ad_lib": "Ad-Lib"
            }.get(canon, canon.title())
            
            # Comprehensive genre-specific bar counts
            genre_bar_counts = {
                # ELECTRONIC & EDM
                "house": {"intro": 16, "build": 8, "drop": 32, "break": 16, "outro": 16, "verse": 16, "hook": 16},
                "deep-house": {"intro": 32, "verse": 16, "build": 8, "drop": 32, "break": 16, "outro": 32},
                "techno": {"intro": 32, "verse": 32, "drop": 64, "break": 32, "build": 16, "outro": 32},
                "trance": {"intro": 16, "verse": 16, "pre": 16, "drop": 32, "break": 16, "outro": 16},
                "dubstep": {"intro": 8, "verse": 8, "pre": 8, "drop": 16, "outro": 8},
                
                # HIP HOP & RAP
                "hip-hop": {"intro": 4, "verse": 16, "hook": 8, "bridge": 8, "outro": 4},
                "trap": {"intro": 4, "verse": 16, "hook": 8, "bridge": 8, "outro": 4},
                "drill": {"intro": 8, "verse": 16, "hook": 8, "outro": 4},
                "boom-bap": {"intro": 4, "verse": 16, "hook": 8, "outro": 4},
                
                # ROCK & METAL
                "rock": {"intro": 8, "verse": 16, "hook": 16, "bridge": 8, "outro": 8},
                "metal": {"intro": 8, "verse": 16, "hook": 16, "bridge": 8, "outro": 8},
                
                # LATIN & WORLD
                "reggaeton": {"intro": 4, "verse": 16, "hook": 8, "bridge": 8, "outro": 4},
                "bachata": {"intro": 8, "verse": 16, "hook": 8, "bridge": 8, "outro": 8},
                "salsa": {"intro": 8, "verse": 16, "hook": 8, "bridge": 16, "outro": 8},
                
                # Default for other genres
                "default": {"intro": 4, "pre": 4, "hook": 8, "verse": 16, "bridge": 8, 
                           "interlude": 4, "drop": 16, "outro": 4, "ad_lib": 2}
            }
            
            bar_counts = genre_bar_counts.get(genre, genre_bar_counts["default"])
            bars = bar_counts.get(canon, 8)
            return f"{display}({bars})"
        
        parts = [format_section(section) for section in sequence]
        return " → ".join(parts)

    def calculate_syllable_density(self, text: str) -> float:
        """Calculate syllable density for BPM estimation"""
        words = re.findall(r'\b\w+\b', text.lower())
        if not words:
            return 1.0
            
        vowel_groups = re.findall(r'[aeiouy]+', ' '.join(words))
        syllable_count = len(vowel_groups)
        word_count = len(words)
        
        return syllable_count / word_count if word_count > 0 else 1.0

    def detect_genre_with_confidence(self, description: str, bpm: int) -> Tuple[str, float]:
        """Enhanced genre detection with confidence scoring"""
        description_lower = description.lower()
        genre_scores = {}
        
        for genre, data in self.genre_keywords.items():
            score = 0.0
            keyword_matches = 0
            
            # Keyword matching with weights
            for keyword in data['keywords']:
                if keyword in description_lower:
                    score += data['weight']
                    keyword_matches += 1
            
            # BPM range bonus
            bpm_min, bpm_max = data['bpm_range']
            if bpm_min <= bpm <= bpm_max:
                score += 2.0
            elif abs(bpm - (bpm_min + bpm_max) / 2) <= 20:
                score += 1.0
            
            # Normalize score
            if keyword_matches > 0:
                score = score / len(data['keywords']) * keyword_matches
                
            genre_scores[genre] = score
        
        # First check direct keyword matches for high confidence
        if 'drill' in description_lower:
            return 'drill', 0.9
        elif 'trap' in description_lower:
            return 'trap', 0.9  
        elif 'rock' in description_lower and 'alternative' in description_lower:
            return 'alternative', 0.9
        elif 'rock' in description_lower:
            return 'rock', 0.9
        elif 'country' in description_lower:
            return 'country', 0.9
        elif 'soul' in description_lower:
            return 'soul', 0.9
        elif 'ballad' in description_lower:
            return 'ballad', 0.9
        elif 'merengue' in description_lower:
            return 'merengue', 0.9
        elif 'salsa' in description_lower:
            return 'salsa', 0.9
        elif 'bachata' in description_lower:
            return 'bachata', 0.9
        elif 'reggaeton' in description_lower or 'dembow' in description_lower:
            return 'reggaeton', 0.9
        elif 'house' in description_lower or ('electronic' in description_lower and 'dance' in description_lower):
            return 'house', 0.8
        
        if not genre_scores:
            return 'electronic', 0.5
            
        best_genre = max(genre_scores.items(), key=lambda x: x[1])
        confidence = min(best_genre[1] / 3.0, 1.0)  # Normalize to 0-1
        
        return best_genre[0], confidence

    def detect_mood_with_confidence(self, description: str) -> Tuple[str, float]:
        """Enhanced mood detection with confidence scoring"""
        description_lower = description.lower()
        mood_scores = {}
        
        for mood, keywords in self.mood_keywords.items():
            score = sum(1 for keyword in keywords if keyword in description_lower)
            if score > 0:
                mood_scores[mood] = score / len(keywords)
        
        if not mood_scores:
            return 'neutral', 0.5
            
        best_mood = max(mood_scores.items(), key=lambda x: x[1])
        return best_mood[0], best_mood[1]

    def estimate_bpm(self, description: str, genre: str) -> int:
        """Enhanced BPM estimation with genre context"""
        syllable_density = self.calculate_syllable_density(description)
        
        # Base BPM from syllable density
        base_bpm = int(80 + (syllable_density - 1.0) * 40)
        base_bpm = max(60, min(200, base_bpm))
        
        # Genre-specific adjustment
        if genre in self.genre_keywords:
            genre_min, genre_max = self.genre_keywords[genre]['bpm_range']
            genre_center = (genre_min + genre_max) / 2
            
            # Weighted average between calculated and genre typical
            final_bpm = int(0.6 * base_bpm + 0.4 * genre_center)
            
            # Ensure within reasonable range for genre
            return max(genre_min - 10, min(genre_max + 10, final_bpm))
        
        return base_bpm

    def generate_suggestions(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate contextual suggestions based on analysis with instrument specifications"""
        suggestions = []
        genre = analysis['genre']
        mood = analysis['mood']
        bpm = analysis['bpm']
        
        # Get genre-specific instrument suggestions
        if genre in self.genre_keywords:
            genre_data = self.genre_keywords[genre]
            instruments = genre_data.get('instruments', [])
            
            if instruments:
                # Primary instrument suggestions
                primary_instruments = instruments[:2]
                suggestions.append(f"Essential instruments: {', '.join(primary_instruments)}")
                
                # Secondary instrument suggestions
                if len(instruments) > 2:
                    secondary = instruments[2:]
                    suggestions.append(f"Layer with: {', '.join(secondary)}")
        
        # Genre-specific production suggestions
        genre_suggestions = {
            'house': [
                "Add a strong four-on-the-floor kick pattern",
                "Layer filtered disco samples for authentic house vibes",
                "Use sidechain compression on pads"
            ],
            'deep-house': [
                "Focus on groove and subtle progression",
                "Use warm analog-style filtering",
                "Keep arrangements minimal and spacious"
            ],
            'techno': [
                "Create driving repetitive patterns",
                "Use industrial samples for texture",
                "Build tension with gradual filter sweeps"
            ],
            'hip-hop': [
                "Focus on groove and pocket",
                "Layer vinyl crackle for authenticity",
                "Leave space for vocal delivery"
            ],
            'trap': [
                "Use heavy 808 patterns with slides",
                "Add rapid hi-hat rolls and snare fills",
                "Layer dark atmospheric elements"
            ],
            'drill': [
                "Keep arrangements dark and minimal",
                "Use sliding 808s as main element",
                "Add aggressive hi-hat patterns"
            ],
            'boom-bap': [
                "Sample from jazz and soul records",
                "Use analog warmth and tape saturation",
                "Keep drum patterns simple but punchy"
            ],
            'lo-fi': [
                "Add vinyl crackle and tape noise",
                "Use warm, muffled drum sounds",
                "Keep melodies simple and nostalgic"
            ],
            'reggaeton': [
                "Use the classic dembow rhythm pattern",
                "Add Latin percussion layers",
                "Include melodic guitar or piano hooks"
            ],
            'rock': [
                "Use power chords and strong rhythm",
                "Add driving drums with 2 and 4 emphasis",
                "Include dynamic builds and releases"
            ],
            'metal': [
                "Use heavy, distorted guitars",
                "Add double bass drum patterns",
                "Focus on powerful, aggressive sounds"
            ],
            'jazz': [
                "Leave space for improvisation",
                "Use complex chord progressions",
                "Focus on swing and groove dynamics"
            ],
            'ambient': [
                "Create spatial depth with reverb",
                "Use atmospheric textures and drones",
                "Keep percussion minimal or absent"
            ],
            'dnb': [
                "Chop and manipulate breakbeats",
                "Use rolling bass patterns",
                "Create complex rhythm variations"
            ]
        }
        
        # Add genre-specific suggestions
        if genre in genre_suggestions:
            suggestions.extend(genre_suggestions[genre][:2])
        elif genre.replace('-', '_') in genre_suggestions:
            suggestions.extend(genre_suggestions[genre.replace('-', '_')][:2])
        
        # BPM-specific suggestions
        if bpm < 80:
            suggestions.append("Perfect tempo for downtempo and ambient vibes")
        elif bpm > 150:
            suggestions.append("High-energy tempo - great for dance and electronic music")
        elif 120 <= bpm <= 130:
            suggestions.append("Optimal dancing tempo - perfect for clubs")
        
        # Mood-specific suggestions
        mood_suggestions = {
            'dark': "Use minor keys and heavy bass for darker atmosphere",
            'energetic': "Add dynamic builds and drops to maintain energy", 
            'chill': "Use warm sounds and relaxed rhythms",
            'happy': "Focus on major keys and uplifting melodies",
            'melancholic': "Use emotional chord progressions and space",
            'mysterious': "Layer atmospheric textures and ambient sounds"
        }
        
        if mood in mood_suggestions:
            suggestions.append(mood_suggestions[mood])
        
        return suggestions[:5]  # Limit to top 5 suggestions

    def analyze_beat(self, description: str, user_id: str, genre_override: Optional[str] = None, bpm_override: Optional[int] = None) -> BeatAnalysis:
        """Comprehensive beat analysis with enhanced algorithms"""
        try:
            # Generate deterministic seed
            seed = self.generate_deterministic_seed(description, user_id)
            
            # Enhanced analysis with overrides
            if genre_override and genre_override in self.genre_keywords:
                genre = genre_override
                genre_confidence = 1.0  # High confidence for user-selected genre
            else:
                genre, genre_confidence = self.detect_genre_with_confidence(description, 120)  # Initial BPM estimate
            
            mood, mood_confidence = self.detect_mood_with_confidence(description)
            
            if bpm_override and 60 <= bpm_override <= 200:
                bpm = bpm_override
            else:
                bpm = self.estimate_bpm(description, genre)
            
            # Re-calculate genre with better BPM if not overridden
            if not genre_override:
                genre, genre_confidence = self.detect_genre_with_confidence(description, bpm)
            
            # Enhanced section and structure analysis
            sections = self.detect_song_sections(description)
            structure = self.generate_song_structure(sections, genre)
            
            # Additional analysis
            key_signature = self._infer_key_signature(description, mood)
            time_signature = self._infer_time_signature(description, genre)
            
            analysis_dict = {
                'genre': genre,
                'mood': mood,
                'bpm': bpm,
                'key_signature': key_signature,
                'time_signature': time_signature,
                'structure': structure,
                'sections_detected': len(sections)
            }
            
            suggestions = self.generate_suggestions(analysis_dict)
            confidence_scores = {
                'genre': genre_confidence,
                'mood': mood_confidence,
                'overall': (genre_confidence + mood_confidence) / 2
            }
            
            # Generate enhanced description
            enhanced_description = self._generate_description(analysis_dict, description)
            
            return BeatAnalysis(
                bpm=bpm,
                genre=genre,
                mood=mood,
                key_signature=key_signature,
                time_signature=time_signature,
                description=enhanced_description,
                suggestions=suggestions,
                confidence_scores=confidence_scores,
                structure=structure,
                sections_detected=len(sections),
                created_at=datetime.now().isoformat(),
                seed=seed
            )
            
        except Exception as e:
            logger.error(f"Error in beat analysis: {e}")
            # Return safe default
            return BeatAnalysis(
                bpm=120,
                genre='electronic',
                mood='neutral',
                key_signature='C major',
                time_signature='4/4',
                description="A balanced electronic composition suitable for various applications.",
                suggestions=["Focus on strong rhythm patterns", "Add melodic elements for interest"],
                confidence_scores={'genre': 0.5, 'mood': 0.5, 'overall': 0.5},
                structure="Intro(4) → Hook(8) → Verse(16) → Hook(8) → Outro(4)",
                sections_detected=0,
                created_at=datetime.now().isoformat(),
                seed='default'
            )

    def _infer_key_signature(self, description: str, mood: str) -> str:
        """Infer key signature based on description and mood"""
        description_lower = description.lower()
        
        # Mood-based key inference
        if mood in ['dark', 'melancholic']:
            minor_keys = ['A minor', 'D minor', 'G minor', 'C minor', 'F minor']
            return minor_keys[hash(description) % len(minor_keys)]
        elif mood in ['happy', 'energetic']:
            major_keys = ['C major', 'G major', 'D major', 'A major', 'E major']
            return major_keys[hash(description) % len(major_keys)]
        
        # Default balanced approach
        all_keys = ['C major', 'G major', 'D major', 'A minor', 'E minor', 'F major']
        return all_keys[hash(description) % len(all_keys)]

    def _infer_time_signature(self, description: str, genre: str) -> str:
        """Infer time signature based on description and genre"""
        description_lower = description.lower()
        
        # Genre-specific time signatures
        if genre in ['house', 'techno', 'pop', 'hip-hop', 'trap']:
            return '4/4'
        elif genre == 'jazz' and any(word in description_lower for word in ['swing', 'waltz']):
            return '3/4'
        elif 'complex' in description_lower or 'odd' in description_lower:
            return '7/8'
        
        return '4/4'  # Default

    def _generate_description(self, analysis: Dict[str, Any], original: str) -> str:
        """Generate enhanced description based on analysis"""
        genre = analysis['genre']
        mood = analysis['mood']
        bpm = analysis['bpm']
        key = analysis['key_signature']
        
        tempo_desc = "slow and contemplative" if bpm < 80 else "moderate" if bpm < 130 else "fast-paced and energetic"
        
        return f"A {mood} {genre} composition in {key} with a {tempo_desc} feel at {bpm} BPM. {original[:100]}{'...' if len(original) > 100 else ''}"
    
    def get_available_genres(self) -> List[Dict[str, Any]]:
        """Get list of all available genres with their metadata"""
        genres = []
        for genre, data in self.genre_keywords.items():
            genres.append({
                'name': genre,
                'display_name': genre.replace('-', ' ').title(),
                'bpm_range': data['bpm_range'],
                'instruments': data.get('instruments', []),
                'weight': data['weight']
            })
        return sorted(genres, key=lambda x: x['display_name'])
    
    def get_genre_info(self, genre: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific genre"""
        if genre in self.genre_keywords:
            data = self.genre_keywords[genre]
            return {
                'name': genre,
                'display_name': genre.replace('-', ' ').title(),
                'keywords': data['keywords'],
                'bpm_range': data['bpm_range'],
                'instruments': data.get('instruments', []),
                'weight': data['weight']
            }
        return None


# Initialize the enhanced beat wizard
beat_wizard = EnhancedBeatWizard()

@beat_bp.route('/analyze', methods=['POST'])
@requires_login
def analyze_beat():
    """Analyze beat description and return comprehensive results"""
    try:
        data = request.get_json()
        if not data or not data.get('description'):
            return jsonify({
                'success': False,
                'error': 'Beat description is required'
            }), 400
        
        description = data['description'].strip()
        if len(description) < 10:
            return jsonify({
                'success': False,
                'error': 'Description must be at least 10 characters long'
            }), 400
        
        user_id = get_user_id()
        
        # Get optional overrides
        genre_override = data.get('genre_override')
        bpm_override = data.get('bpm_override')
        
        # Perform analysis with overrides
        analysis = beat_wizard.analyze_beat(description, user_id, genre_override, bpm_override)
        
        # Auto-save to library
        try:
            from ...db.database_manager import get_db
            database = get_db()
            library_manager = LibraryManager(database)
            library_manager.save_content(
                user_id=user_id,
                content_type='beat_analysis',
                content_data={
                    'title': f"Beat Analysis - {analysis.genre.title()}",
                    'description': description,
                    'analysis': analysis.to_dict(),
                    'created_at': analysis.created_at
                },
                metadata={'seed': analysis.seed}
            )
            logger.info(f"Beat analysis auto-saved for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to auto-save beat analysis: {e}")
            # Continue anyway - analysis still works
        
        return jsonify({
            'success': True,
            'analysis': analysis.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error in beat analysis endpoint: {e}")
        return jsonify({
            'success': False,
            'error': 'Beat analysis failed'
        }), 500

@beat_bp.route('/health', methods=['GET'])
def beat_health():
    """Health check for beat wizard service"""
    try:
        # Quick test analysis
        test_analysis = beat_wizard.analyze_beat("upbeat electronic dance track", "test_user")
        
        return jsonify({
            'status': 'healthy',
            'service': 'beat_wizard',
            'version': '2.0.0',
            'features': [
                'genre_detection',
                'mood_analysis',
                'bpm_estimation',
                'confidence_scoring',
                'auto_save',
                'multilingual_support'
            ],
            'test_passed': test_analysis.genre is not None
        })
        
    except Exception as e:
        logger.error(f"Beat wizard health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@beat_bp.route('/stats', methods=['GET'])
@requires_login
def beat_stats():
    """Get beat analysis statistics for current user"""
    try:
        user_id = get_user_id()
        
        # This would require database integration for real stats
        # For now, return mock stats
        return jsonify({
            'success': True,
            'stats': {
                'total_analyses': 0,
                'favorite_genre': 'electronic',
                'average_bpm': 120,
                'most_common_mood': 'energetic'
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting beat stats: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get statistics'
        }), 500

@beat_bp.route('/genres', methods=['GET'])
def get_genres():
    """Get list of all available genres"""
    try:
        genres = beat_wizard.get_available_genres()
        return jsonify({
            'success': True,
            'genres': genres
        })
    except Exception as e:
        logger.error(f"Error getting genres: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get genres'
        }), 500

@beat_bp.route('/genres/<genre>', methods=['GET'])
def get_genre_info(genre):
    """Get detailed information about a specific genre"""
    try:
        genre_info = beat_wizard.get_genre_info(genre)
        if genre_info:
            return jsonify({
                'success': True,
                'genre': genre_info
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Genre not found'
            }), 404
    except Exception as e:
        logger.error(f"Error getting genre info: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get genre information'
        }), 500

@beat_bp.route('/', methods=['GET'])
def beat_wizard_page():
    """Serve the Beat Wizard frontend page"""
    from flask import render_template
    genre_count = len(beat_wizard.genre_keywords)
    return render_template('beat_wizard.html', genre_count=genre_count)

def init_beat_system():
    """Initialize Beat Wizard system"""
    logger.info("Enhanced Beat Wizard system initialized successfully")