"""
SoulBridge AI - Creative Features Configuration
Extracted from app.py monolith using strategic bulk extraction
Decoder, Fortune, Horoscope, Creative Writing system
"""

# Feature limits by tier
CREATIVE_LIMITS = {
    "decoder": {
        "bronze": 5,    # 5 daily uses (increased for better UX)
        "silver": 15,   # 15 daily uses  
        "gold": 999     # Unlimited (999 = unlimited display)
    },
    "fortune": {
        "bronze": 5,    # 5 daily uses (increased for better UX)
        "silver": 10,   # 10 daily uses
        "gold": 999     # Unlimited
    },
    "horoscope": {
        "bronze": 5,    # 5 daily uses (increased for better UX)
        "silver": 10,   # 10 daily uses
        "gold": 999     # Unlimited
    },
    "creative_writing": {
        "bronze": 5,    # 5 daily uses (increased for better UX)
        "silver": 20,   # 20 daily uses
        "gold": 999     # Unlimited
    }
}

# Feature descriptions
FEATURE_DESCRIPTIONS = {
    "decoder": "AI Dream Decoder - Decode the hidden meanings in your dreams",
    "fortune": "Fortune Teller - Get insights into your future with AI-powered tarot",
    "horoscope": "Daily Horoscope - Personalized astrological readings",
    "creative_writing": "Creative Writer - AI-powered creative content generation"
}

# Zodiac signs for horoscope
ZODIAC_SIGNS = [
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"
]

# Complete 78-card Tarot deck for fortune telling
MAJOR_ARCANA = [
    {"name": "The Fool", "suit": "major", "meaning": "New beginnings, innocence, spontaneity"},
    {"name": "The Magician", "suit": "major", "meaning": "Manifestation, resourcefulness, power"},
    {"name": "The High Priestess", "suit": "major", "meaning": "Intuition, sacred knowledge, divine feminine"},
    {"name": "The Empress", "suit": "major", "meaning": "Femininity, beauty, nature, abundance"},
    {"name": "The Emperor", "suit": "major", "meaning": "Authority, establishment, structure, father figure"},
    {"name": "The Hierophant", "suit": "major", "meaning": "Religion, group identification, conformity"},
    {"name": "The Lovers", "suit": "major", "meaning": "Love, harmony, relationships, values alignment"},
    {"name": "The Chariot", "suit": "major", "meaning": "Control, willpower, success, determination"},
    {"name": "Strength", "suit": "major", "meaning": "Strength, courage, patience, control"},
    {"name": "The Hermit", "suit": "major", "meaning": "Soul searching, introspection, inner guidance"},
    {"name": "Wheel of Fortune", "suit": "major", "meaning": "Good luck, karma, life cycles, destiny"},
    {"name": "Justice", "suit": "major", "meaning": "Justice, fairness, truth, cause and effect"},
    {"name": "The Hanged Man", "suit": "major", "meaning": "Suspension, restriction, letting go"},
    {"name": "Death", "suit": "major", "meaning": "Endings, beginnings, change, transformation"},
    {"name": "Temperance", "suit": "major", "meaning": "Balance, moderation, patience, purpose"},
    {"name": "The Devil", "suit": "major", "meaning": "Bondage, addiction, sexuality, materialism"},
    {"name": "The Tower", "suit": "major", "meaning": "Sudden change, upheaval, chaos, revelation"},
    {"name": "The Star", "suit": "major", "meaning": "Hope, faith, purpose, renewal, spirituality"},
    {"name": "The Moon", "suit": "major", "meaning": "Illusion, fear, anxiety, subconscious, intuition"},
    {"name": "The Sun", "suit": "major", "meaning": "Happiness, success, optimism, vitality"},
    {"name": "Judgement", "suit": "major", "meaning": "Judgement, rebirth, inner calling, absolution"},
    {"name": "The World", "suit": "major", "meaning": "Completion, integration, accomplishment, travel"}
]

# Minor Arcana - Wands (Fire/Passion/Career)
WANDS = [
    {"name": "Ace of Wands", "suit": "wands", "meaning": "New creative projects, inspiration, potential"},
    {"name": "Two of Wands", "suit": "wands", "meaning": "Planning, making decisions, leaving comfort zone"},
    {"name": "Three of Wands", "suit": "wands", "meaning": "Expansion, foresight, overseas opportunities"},
    {"name": "Four of Wands", "suit": "wands", "meaning": "Celebration, harmony, home, community"},
    {"name": "Five of Wands", "suit": "wands", "meaning": "Competition, conflict, struggle"},
    {"name": "Six of Wands", "suit": "wands", "meaning": "Success, recognition, victory"},
    {"name": "Seven of Wands", "suit": "wands", "meaning": "Perseverance, defensive stance, maintaining position"},
    {"name": "Eight of Wands", "suit": "wands", "meaning": "Swift action, movement, progress"},
    {"name": "Nine of Wands", "suit": "wands", "meaning": "Resilience, persistence, last stretch"},
    {"name": "Ten of Wands", "suit": "wands", "meaning": "Burden, responsibility, hard work"},
    {"name": "Page of Wands", "suit": "wands", "meaning": "Exploration, excitement, freedom"},
    {"name": "Knight of Wands", "suit": "wands", "meaning": "Adventure, impulsiveness, pursuing goals"},
    {"name": "Queen of Wands", "suit": "wands", "meaning": "Confidence, determination, social butterfly"},
    {"name": "King of Wands", "suit": "wands", "meaning": "Leadership, vision, honor"}
]

# Minor Arcana - Cups (Water/Emotions/Relationships)
CUPS = [
    {"name": "Ace of Cups", "suit": "cups", "meaning": "New love, emotional fulfillment, spirituality"},
    {"name": "Two of Cups", "suit": "cups", "meaning": "Partnership, unity, mutual attraction"},
    {"name": "Three of Cups", "suit": "cups", "meaning": "Friendship, community, celebration"},
    {"name": "Four of Cups", "suit": "cups", "meaning": "Contemplation, apathy, reevaluation"},
    {"name": "Five of Cups", "suit": "cups", "meaning": "Loss, grief, disappointment"},
    {"name": "Six of Cups", "suit": "cups", "meaning": "Nostalgia, childhood memories, innocence"},
    {"name": "Seven of Cups", "suit": "cups", "meaning": "Options, illusion, wishful thinking"},
    {"name": "Eight of Cups", "suit": "cups", "meaning": "Walking away, seeking deeper meaning"},
    {"name": "Nine of Cups", "suit": "cups", "meaning": "Contentment, satisfaction, luxury"},
    {"name": "Ten of Cups", "suit": "cups", "meaning": "Happiness, harmony, family"},
    {"name": "Page of Cups", "suit": "cups", "meaning": "Creative opportunities, intuitive messages"},
    {"name": "Knight of Cups", "suit": "cups", "meaning": "Romance, charm, being led by emotions"},
    {"name": "Queen of Cups", "suit": "cups", "meaning": "Compassion, calm, comfort"},
    {"name": "King of Cups", "suit": "cups", "meaning": "Emotional balance, generosity, control"}
]

# Minor Arcana - Swords (Air/Thoughts/Communication)
SWORDS = [
    {"name": "Ace of Swords", "suit": "swords", "meaning": "New ideas, mental clarity, breakthrough"},
    {"name": "Two of Swords", "suit": "swords", "meaning": "Difficult decisions, weighing options"},
    {"name": "Three of Swords", "suit": "swords", "meaning": "Heartbreak, sorrow, grief"},
    {"name": "Four of Swords", "suit": "swords", "meaning": "Rest, contemplation, recovery"},
    {"name": "Five of Swords", "suit": "swords", "meaning": "Conflict, defeat, winning at all costs"},
    {"name": "Six of Swords", "suit": "swords", "meaning": "Transition, moving forward, travel"},
    {"name": "Seven of Swords", "suit": "swords", "meaning": "Deception, theft, getting away with something"},
    {"name": "Eight of Swords", "suit": "swords", "meaning": "Restriction, imprisonment, victim mentality"},
    {"name": "Nine of Swords", "suit": "swords", "meaning": "Anxiety, worry, nightmares"},
    {"name": "Ten of Swords", "suit": "swords", "meaning": "Rock bottom, betrayal, defeat"},
    {"name": "Page of Swords", "suit": "swords", "meaning": "Curiosity, restlessness, mental energy"},
    {"name": "Knight of Swords", "suit": "swords", "meaning": "Action, impulsiveness, defending beliefs"},
    {"name": "Queen of Swords", "suit": "swords", "meaning": "Independence, unbiased judgment, direct communication"},
    {"name": "King of Swords", "suit": "swords", "meaning": "Mental clarity, intellectual power, authority"}
]

# Minor Arcana - Pentacles (Earth/Material/Money)
PENTACLES = [
    {"name": "Ace of Pentacles", "suit": "pentacles", "meaning": "New financial opportunity, manifestation"},
    {"name": "Two of Pentacles", "suit": "pentacles", "meaning": "Balance, adaptability, time management"},
    {"name": "Three of Pentacles", "suit": "pentacles", "meaning": "Collaboration, teamwork, skill"},
    {"name": "Four of Pentacles", "suit": "pentacles", "meaning": "Saving money, security, conservatism"},
    {"name": "Five of Pentacles", "suit": "pentacles", "meaning": "Financial loss, poverty, isolation"},
    {"name": "Six of Pentacles", "suit": "pentacles", "meaning": "Generosity, charity, sharing"},
    {"name": "Seven of Pentacles", "suit": "pentacles", "meaning": "Assessment, hard work, perseverance"},
    {"name": "Eight of Pentacles", "suit": "pentacles", "meaning": "Skill development, quality work, mastery"},
    {"name": "Nine of Pentacles", "suit": "pentacles", "meaning": "Luxury, self-reliance, financial independence"},
    {"name": "Ten of Pentacles", "suit": "pentacles", "meaning": "Wealth, family, long-term success"},
    {"name": "Page of Pentacles", "suit": "pentacles", "meaning": "Learning, planning, new ventures"},
    {"name": "Knight of Pentacles", "suit": "pentacles", "meaning": "Hard work, productivity, routine"},
    {"name": "Queen of Pentacles", "suit": "pentacles", "meaning": "Nurturing, practical, resource management"},
    {"name": "King of Pentacles", "suit": "pentacles", "meaning": "Financial success, leadership, security"}
]

# Complete 78-card tarot deck
TAROT_CARDS = MAJOR_ARCANA + WANDS + CUPS + SWORDS + PENTACLES

def get_feature_limit(feature: str, user_plan: str, trial_active: bool) -> int:
    """Get daily usage limit for a creative feature"""
    if feature not in CREATIVE_LIMITS:
        return 0
    
    # Trial users get Gold limits for feature access
    if trial_active and user_plan == 'bronze':
        effective_plan = 'gold'
    else:
        effective_plan = user_plan
    
    return CREATIVE_LIMITS[feature].get(effective_plan, 0)

def is_feature_unlimited(feature: str, user_plan: str, trial_active: bool) -> bool:
    """Check if user has unlimited access to a feature"""
    limit = get_feature_limit(feature, user_plan, trial_active)
    return limit >= 999

def get_all_creative_features() -> list:
    """Get list of all creative features"""
    return list(CREATIVE_LIMITS.keys())

def get_feature_description(feature: str) -> str:
    """Get description for a creative feature"""
    return FEATURE_DESCRIPTIONS.get(feature, f"{feature.title()} feature")

def validate_zodiac_sign(sign: str) -> bool:
    """Validate zodiac sign"""
    return sign.lower() in ZODIAC_SIGNS

def get_random_tarot_cards(count: int = 3) -> list:
    """Get random tarot cards for reading"""
    import random
    return random.sample(TAROT_CARDS, min(count, len(TAROT_CARDS)))

def get_creative_limits_summary(user_plan: str, trial_active: bool) -> dict:
    """Get summary of all creative feature limits for user"""
    summary = {}
    
    for feature in get_all_creative_features():
        limit = get_feature_limit(feature, user_plan, trial_active)
        summary[feature] = {
            "limit": limit,
            "unlimited": is_feature_unlimited(feature, user_plan, trial_active),
            "description": get_feature_description(feature)
        }
    
    return summary