"""
SoulBridge AI - Deterministic Content Generation
Based on excellent SDK patterns for consistent user experiences
Ensures users get the same reading per day but different readings daily
"""
import hashlib
import random
from datetime import datetime, date
from typing import List, Dict, Any, Optional, Literal
from dataclasses import dataclass

# Zodiac configuration from the original SDK pattern
ZODIAC_DATA = {
    "aries": {"element": "Fire", "quality": "Cardinal", "ruler": "Mars"},
    "taurus": {"element": "Earth", "quality": "Fixed", "ruler": "Venus"},
    "gemini": {"element": "Air", "quality": "Mutable", "ruler": "Mercury"},
    "cancer": {"element": "Water", "quality": "Cardinal", "ruler": "Moon"},
    "leo": {"element": "Fire", "quality": "Fixed", "ruler": "Sun"},
    "virgo": {"element": "Earth", "quality": "Mutable", "ruler": "Mercury"},
    "libra": {"element": "Air", "quality": "Cardinal", "ruler": "Venus"},
    "scorpio": {"element": "Water", "quality": "Fixed", "ruler": "Pluto"},
    "sagittarius": {"element": "Fire", "quality": "Mutable", "ruler": "Jupiter"},
    "capricorn": {"element": "Earth", "quality": "Cardinal", "ruler": "Saturn"},
    "aquarius": {"element": "Air", "quality": "Fixed", "ruler": "Uranus"},
    "pisces": {"element": "Water", "Quality": "Mutable", "ruler": "Neptune"}
}

Period = Literal["daily", "weekly", "monthly"]
Sign = Literal["aries", "taurus", "gemini", "cancer", "leo", "virgo", 
               "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"]

@dataclass(frozen=True)
class DeterministicHoroscope:
    """Immutable horoscope reading with deterministic generation"""
    sign: Sign
    period: Period
    date: date
    summary: str
    lucky_color: str
    lucky_time: str
    lucky_numbers: List[int]
    energy_focus: str
    element_guidance: str

def _create_deterministic_seed(
    user_id: int, 
    sign: str, 
    period: str, 
    target_date: date, 
    extra: Optional[str] = None
) -> None:
    """Create deterministic seed ensuring consistent readings per user per day"""
    seed_components = [str(user_id), sign, period, target_date.isoformat()]
    if extra:
        seed_components.append(extra)
    
    # Create SHA256 hash and use first 16 chars as numeric seed
    seed_string = "|".join(seed_components)
    hash_hex = hashlib.sha256(seed_string.encode()).hexdigest()
    numeric_seed = int(hash_hex[:16], 16)
    random.seed(numeric_seed)

def generate_deterministic_horoscope(
    user_id: int,
    sign: Sign, 
    period: Period = "daily", 
    target_date: Optional[date] = None,
    seed_extra: Optional[str] = None
) -> DeterministicHoroscope:
    """Generate consistent horoscope using deterministic seed pattern from SDK"""
    
    if target_date is None:
        target_date = date.today()
    
    # Set deterministic seed
    _create_deterministic_seed(user_id, sign, period, target_date, seed_extra)
    
    # Get zodiac data
    sign_data = ZODIAC_DATA.get(sign, ZODIAC_DATA["aries"])
    element = sign_data["element"].lower()
    
    # Generate consistent content based on seed
    energy_focuses = ["focus", "connection", "reset", "momentum", "clarity", "growth"]
    energy_focus = random.choice(energy_focuses)
    
    # Element-specific guidance
    element_guidance_templates = {
        "fire": [
            f"Channel your {element} energy into bold action today.",
            f"Your {element} nature calls for passionate pursuit of goals.",
            f"Let your {element} spirit illuminate new opportunities."
        ],
        "earth": [
            f"Ground yourself in {element} wisdom and practical steps.",
            f"Your {element} nature supports steady, methodical progress.",
            f"Trust your {element} instincts for building lasting foundations."
        ],
        "air": [
            f"Let your {element} nature guide clear communication today.",
            f"Your {element} element favors intellectual exploration.",
            f"Embrace {element} energy for social connections and ideas."
        ],
        "water": [
            f"Flow with your {element} intuition and emotional wisdom.",
            f"Your {element} nature enhances empathy and understanding.",
            f"Trust the {element} currents of your inner guidance."
        ]
    }
    
    element_guidance = random.choice(element_guidance_templates.get(element, element_guidance_templates["fire"]))
    
    # Generate summary
    summary_templates = [
        f"Energy leans into {energy_focus} today. {element_guidance}",
        f"Today brings opportunities for {energy_focus}. {element_guidance}",
        f"The stars align for {energy_focus} and growth. {element_guidance}"
    ]
    summary = random.choice(summary_templates)
    
    # Consistent random choices
    lucky_colors = ["teal", "indigo", "gold", "silver", "crimson", "emerald", "sapphire", "amethyst"]
    lucky_times = ["11:11", "14:44", "20:20", "07:07", "12:34", "16:16"]
    
    return DeterministicHoroscope(
        sign=sign,
        period=period,
        date=target_date,
        summary=summary,
        lucky_color=random.choice(lucky_colors),
        lucky_time=random.choice(lucky_times),
        lucky_numbers=random.sample(range(1, 78), 3),
        energy_focus=energy_focus,
        element_guidance=element_guidance
    )

def generate_decoder_symbols(
    user_id: int,
    text: str, 
    mode: str = "dream",
    target_date: Optional[date] = None
) -> Dict[str, Any]:
    """Generate consistent symbol analysis using deterministic approach"""
    
    if target_date is None:
        target_date = date.today()
    
    # Create seed from user, text hash, and date for consistency
    text_hash = hashlib.sha256(text.encode()).hexdigest()[:8]
    _create_deterministic_seed(user_id, mode, "analysis", target_date, text_hash)
    
    # Symbol libraries based on mode
    symbol_libraries = {
        "dream": {
            "water": "emotions/subconscious flow",
            "fire": "passion/transformation",
            "animals": "instincts/inner nature", 
            "flying": "freedom/transcendence",
            "falling": "loss of control/anxiety",
            "houses": "self/psyche structure"
        },
        "lyrics": {
            "moon": "mystery/cycles",
            "fire": "passion/intensity", 
            "road": "journey/life path",
            "glass": "fragility/clarity",
            "storm": "conflict/change",
            "light": "hope/revelation"
        }
    }
    
    symbols = symbol_libraries.get(mode, symbol_libraries["dream"])
    text_lower = text.lower()
    
    # Find symbols in text
    found_symbols = [symbol for symbol in symbols if symbol in text_lower]
    
    # Generate consistent suggestions
    suggestion_pool = [
        "Look for recurring patterns in imagery",
        "Consider the emotional undertones", 
        "Examine contrasting elements",
        "Focus on transformative moments",
        "Identify your strongest metaphors"
    ]
    
    suggestions = random.sample(suggestion_pool, min(3, len(suggestion_pool)))
    
    return {
        "symbols_found": found_symbols or ["(no specific symbols detected)"],
        "meanings": [f"{symbol}: {symbols[symbol]}" for symbol in found_symbols],
        "suggestions": suggestions,
        "analysis_mode": mode
    }