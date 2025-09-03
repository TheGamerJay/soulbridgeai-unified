"""
SoulBridge AI - Enhanced Fortune/Tarot Service
Deterministic tarot readings using seed-based generation
Integrated from standalone app_tarot_full.py
"""
import os
import json
import random
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Load tarot meanings
DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "data", "tarot_meanings_full.json")

try:
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        DECK = json.load(f)
    logger.info(f"Loaded {len(DECK)} tarot cards from {DATA_FILE}")
except Exception as e:
    logger.warning(f"Could not load tarot meanings from {DATA_FILE}: {e}")
    # Fallback minimal deck
    DECK = {
        "The Fool": {
            "upright": "New beginnings, spontaneity, innocence",
            "reversed": "Recklessness, taken advantage of, inconsistency",
            "symbols": "Cliff, dog, rose, bag"
        },
        "The Magician": {
            "upright": "Manifestation, resourcefulness, power",
            "reversed": "Manipulation, poor planning, unused talents",
            "symbols": "Infinity symbol, wand, altar tools"
        },
        "The High Priestess": {
            "upright": "Intuition, sacred knowledge, divine feminine",
            "reversed": "Secrets, disconnected from intuition, withdrawal",
            "symbols": "Moon crown, pillars, scroll"
        }
    }

# Spread configurations
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
    "21 Card Grand Spread": [
        "Core Self", "Life Purpose", "Hidden Influences", "Recent Past", "Possible Future",
        "Distant Past", "Your Approach", "External Influences", "Inner Feelings", "Hopes & Fears",
        "Final Outcome", "Love & Relationships", "Work & Career", "Family & Home", "Health & Vitality", 
        "Spirituality", "Travel & Change", "Hidden Enemies", "Friends & Allies", "Money & Resources", "Ultimate Destiny"
    ]
}

def to_slug(card_name: str) -> str:
    """Convert card name to image filename slug"""
    replacers = {
        "The ": "the_",
        " of ": "_of_",
        " & ": "_and_",
        "-": "_",
        " ": "_"
    }
    slug = card_name.lower()
    for old, new in replacers.items():
        slug = slug.replace(old.lower(), new)
    return slug

def generate_deterministic_seed(user_id: int, question: str, spread_type: str, date_str: str = None) -> str:
    """Generate deterministic seed for consistent readings"""
    if date_str is None:
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    # Create seed from user, question, spread, and date
    seed_string = f"{user_id}:{question or 'general'}:{spread_type}:{date_str}"
    return hashlib.sha256(seed_string.encode()).hexdigest()[:16]

def do_reading(
    spread_name: str = "3 Card",
    reversals: bool = True,
    seed: Optional[str] = None,
    clarifiers: int = 0,
    allow_duplicates: bool = False,
) -> Dict[str, Any]:
    """Generate a deterministic tarot reading"""
    
    # Set deterministic seed
    if seed is not None and str(seed).strip():
        random.seed(str(seed))
    
    positions = SPREADS.get(spread_name, SPREADS["3 Card"])
    cards = list(DECK.keys())
    n = len(positions)
    
    if allow_duplicates:
        drawn = [random.choice(cards) for _ in range(n)]
    else:
        drawn = random.sample(cards, min(n, len(cards)))
    
    results = []
    already = set(drawn)
    
    for pos, card in zip(positions, drawn):
        orientation = "Upright"
        if reversals:
            orientation = random.choice(["Upright", "Reversed"])
        
        entry = DECK[card]
        meaning = entry["upright"] if orientation == "Upright" else entry["reversed"]
        
        card_data = {
            "position": pos,
            "card": card,
            "slug": to_slug(card),
            "orientation": orientation,
            "meaning": meaning,
            "symbols": entry.get("symbols", ""),
            "image_url": f"/static/tarot/{to_slug(card)}.png"
        }
        
        # Add clarifiers if requested
        if clarifiers and clarifiers > 0:
            card_data["clarifiers"] = []
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
                
                card_data["clarifiers"].append({
                    "card": clar,
                    "slug": to_slug(clar),
                    "orientation": cor,
                    "meaning": cmeaning,
                    "symbols": centry.get("symbols", ""),
                    "image_url": f"/static/tarot/{to_slug(clar)}.png"
                })
        
        results.append(card_data)
    
    return {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "spread": spread_name,
        "reversals": bool(reversals),
        "seed": seed,
        "clarifiers_per_position": int(clarifiers),
        "cards": results,
        "success": True
    }

def generate_tarot_interpretation(reading_data: Dict[str, Any]) -> str:
    """Generate interpretation of tarot reading using deterministic approach"""
    
    cards = reading_data.get('cards', [])
    if not cards:
        return "Unable to interpret reading - no cards found."
    
    # Build interpretation based on spread and card meanings
    spread = reading_data.get('spread', '3 Card')
    interpretations = []
    
    interpretations.append(f"**{spread} Reading Interpretation**\n")
    
    for card_data in cards:
        position = card_data.get('position', 'Unknown')
        card_name = card_data.get('card', 'Unknown')
        orientation = card_data.get('orientation', 'Upright')
        meaning = card_data.get('meaning', 'No meaning available')
        
        interpretation = f"**{position}**: {card_name} ({orientation})\n"
        interpretation += f"*Meaning*: {meaning}\n"
        
        # Add symbols if available
        symbols = card_data.get('symbols')
        if symbols:
            interpretation += f"*Key Symbols*: {symbols}\n"
        
        interpretations.append(interpretation)
    
    # Add comprehensive summary
    interpretations.append("---")
    interpretations.append("**Overall Reading Summary:**\n")
    
    # Generate cohesive interpretation based on spread type
    if spread == "5 Card":
        summary = generate_five_card_summary(cards)
    elif spread == "3 Card":
        summary = generate_three_card_summary(cards)
    elif spread == "Celtic Cross":
        summary = generate_celtic_cross_summary(cards)
    elif spread == "21 Card Grand Spread":
        summary = generate_grand_spread_summary(cards)
    else:
        summary = generate_general_summary(cards)
    
    interpretations.append(summary)
    
    return "\n".join(interpretations)

def generate_five_card_summary(cards: List[Dict[str, Any]]) -> str:
    """Generate comprehensive summary for 5-card spread"""
    if len(cards) < 5:
        return "Incomplete reading - unable to provide summary."
    
    situation = cards[0]['card']
    challenge = cards[1]['card']
    advice = cards[2]['card']
    hidden = cards[3]['card']
    outcome = cards[4]['card']
    
    # Create narrative based on card themes
    situation_theme = get_card_theme(cards[0])
    challenge_theme = get_card_theme(cards[1])
    advice_theme = get_card_theme(cards[2])
    outcome_theme = get_card_theme(cards[4])
    
    summary = f"Your current situation shows {situation_theme}, with the main challenge being {challenge_theme}. "
    summary += f"The cards advise you to focus on {advice_theme}. "
    summary += f"There are hidden influences of {get_card_theme(cards[3])} at work. "
    summary += f"If you follow this guidance, the likely outcome points toward {outcome_theme}."
    
    return summary

def generate_three_card_summary(cards: List[Dict[str, Any]]) -> str:
    """Generate comprehensive summary for 3-card spread"""
    if len(cards) < 3:
        return "Incomplete reading - unable to provide summary."
    
    past_theme = get_card_theme(cards[0])
    present_theme = get_card_theme(cards[1])
    future_theme = get_card_theme(cards[2])
    
    summary = f"Your journey shows a progression from {past_theme} in the past, "
    summary += f"through your current experience of {present_theme}, "
    summary += f"leading toward a future of {future_theme}. "
    summary += f"This reading suggests embracing the lessons of your past while navigating present challenges toward positive transformation."
    
    return summary

def generate_celtic_cross_summary(cards: List[Dict[str, Any]]) -> str:
    """Generate comprehensive summary for Celtic Cross spread"""
    if len(cards) < 10:
        return "Incomplete reading - unable to provide summary."
    
    present_theme = get_card_theme(cards[0])
    challenge_theme = get_card_theme(cards[1])
    outcome_theme = get_card_theme(cards[9])
    
    summary = f"This Celtic Cross reveals a complex situation centered around {present_theme}. "
    summary += f"The primary challenge you're facing involves {challenge_theme}. "
    summary += f"Your path forward leads toward {outcome_theme}, "
    summary += f"guided by the interplay of conscious goals, subconscious drives, and external influences shown in this comprehensive spread."
    
    return summary

def generate_grand_spread_summary(cards: List[Dict[str, Any]]) -> str:
    """Generate comprehensive summary for 21-card Grand spread"""
    if len(cards) < 21:
        return "Incomplete reading - unable to provide summary."
    
    core_theme = get_card_theme(cards[0])  # Core Self
    purpose_theme = get_card_theme(cards[1])  # Life Purpose
    destiny_theme = get_card_theme(cards[20])  # Ultimate Destiny
    
    summary = f"This Grand Tarot spread reveals your core essence as {core_theme}, "
    summary += f"with a life purpose centered on {purpose_theme}. "
    summary += f"The comprehensive view of your life's areas - relationships, career, health, spirituality - "
    summary += f"all point toward an ultimate destiny of {destiny_theme}. "
    summary += f"This reading provides a complete life map for your spiritual and personal journey."
    
    return summary

def generate_general_summary(cards: List[Dict[str, Any]]) -> str:
    """Generate general summary for any spread"""
    if not cards:
        return "No cards available for interpretation."
    
    themes = [get_card_theme(card) for card in cards[:3]]  # Use first 3 cards
    
    summary = f"The cards reveal themes of {', '.join(themes[:-1])} and {themes[-1]}. "
    summary += f"This reading suggests a time of personal growth and spiritual awareness, "
    summary += f"encouraging you to trust your intuition while remaining grounded in practical wisdom."
    
    return summary

def get_card_theme(card_data: Dict[str, Any]) -> str:
    """Extract thematic essence from card data"""
    card_name = card_data.get('card', '').lower()
    orientation = card_data.get('orientation', 'Upright').lower()
    
    # Major Arcana themes
    major_themes = {
        'fool': 'new beginnings and fresh starts',
        'magician': 'manifestation and personal power',
        'high priestess': 'intuition and inner wisdom',
        'empress': 'abundance and creativity',
        'emperor': 'structure and leadership',
        'hierophant': 'tradition and spiritual guidance',
        'lovers': 'relationships and choices',
        'chariot': 'determination and victory',
        'strength': 'inner courage and resilience',
        'hermit': 'soul searching and introspection',
        'wheel': 'cycles of change and destiny',
        'justice': 'balance and fair judgment',
        'hanged': 'surrender and new perspective',
        'death': 'transformation and renewal',
        'temperance': 'harmony and moderation',
        'devil': 'temptation and material bondage',
        'tower': 'sudden change and revelation',
        'star': 'hope and spiritual guidance',
        'moon': 'illusion and subconscious fears',
        'sun': 'joy and positive energy',
        'judgement': 'rebirth and awakening',
        'world': 'completion and fulfillment'
    }
    
    # Check for major arcana
    for key, theme in major_themes.items():
        if key in card_name:
            if orientation == 'reversed':
                return f"blocked or delayed {theme}"
            return theme
    
    # Minor Arcana suit themes
    if 'cups' in card_name:
        base_theme = 'emotional fulfillment and relationships'
    elif 'wands' in card_name:
        base_theme = 'creative energy and ambition'
    elif 'swords' in card_name:
        base_theme = 'mental challenges and communication'
    elif 'pentacles' in card_name:
        base_theme = 'material success and practical matters'
    else:
        base_theme = 'spiritual growth and personal development'
    
    if orientation == 'reversed':
        return f"obstacles in {base_theme}"
    return base_theme

class FortuneService:
    """Enhanced Fortune/Tarot Service with deterministic readings"""
    
    def __init__(self):
        self.spreads_config = {
            "one": {"cards": 1, "name": "1 Card", "description": "Single card guidance"},
            "three": {"cards": 3, "name": "3 Card", "description": "Past, Present, Future"},  
            "five": {"cards": 5, "name": "5 Card", "description": "Comprehensive life reading"},
            "celtic": {"cards": 10, "name": "Celtic Cross", "description": "Full Celtic Cross spread"},
            "grand": {"cards": 21, "name": "21 Card Grand Spread", "description": "Complete life analysis"}
        }
    
    def generate_fortune(self, question: str = None, user_id: int = None, spread_type: str = "three") -> dict:
        """Generate deterministic fortune reading"""
        try:
            # Get spread configuration
            config = self.spreads_config.get(spread_type, self.spreads_config["three"])
            spread_name = config["name"]
            
            # Generate deterministic seed
            seed = generate_deterministic_seed(
                user_id or 1,
                question or "general guidance", 
                spread_type
            )
            
            # Generate reading
            result = do_reading(
                spread_name=spread_name,
                reversals=True,
                seed=seed,
                clarifiers=0,
                allow_duplicates=False
            )
            
            # Add interpretation
            result["interpretation"] = generate_tarot_interpretation(result)
            
            logger.info(f"Generated deterministic {spread_name} reading for user {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error generating fortune reading: {e}")
            return {
                "success": False,
                "error": str(e),
                "cards": []
            }
    
    def get_available_spreads(self) -> Dict[str, Any]:
        """Get available tarot spreads"""
        return {
            spread_key: {
                "name": config["name"],
                "cards": config["cards"],
                "description": config["description"]
            }
            for spread_key, config in self.spreads_config.items()
        }
    
    def generate_interpretation(self, reading_data: Dict[str, Any]) -> str:
        """Generate interpretation for an existing reading"""
        return generate_tarot_interpretation(reading_data)