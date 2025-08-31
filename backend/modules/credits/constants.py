"""
SoulBridge AI - Credits Constants
All credit costs and allowances consolidated in one place
"""

# Credit costs for different features (artistic time required)
ARTISTIC_TIME_COSTS = {
    # AI Generation Features
    "ai_images": 5,                    # DALL-E image generation
    "voice_journaling": 10,            # Voice transcription + AI analysis
    "relationship_profiles": 15,       # Complex relationship analysis
    "meditations": 8,                  # Personalized meditation generation
    "mini_studio": 20,                 # Music production features
    
    # Mini Studio Specific Costs (handled by studio service)
    "lyrics_generation": 5,            # OpenAI structured lyrics
    "beat_composition": 10,            # MusicGen + MIDI stems
    "vocal_synthesis_base": 10,        # DiffSinger base cost
    "vocal_synthesis_no_lyrics": 15,   # +5 for missing lyrics
    "vocal_synthesis_no_beat": 20,     # +10 for missing beat
    "vocal_synthesis_full": 25,        # Maximum cost (no assets provided)
}

# Monthly artistic time allowances per subscription tier
TIER_ARTISTIC_TIME = {
    "bronze": 0,       # Bronze gets no monthly artistic time (ads + trial only)
    "silver": 200,     # Silver gets 200 monthly artistic time
    "gold": 500,       # Gold gets 500 monthly artistic time
}

# Trial system credits
TRIAL_ARTISTIC_TIME = 60  # Trial users get 60 one-time credits for 5 hours

# Legacy constant for backwards compatibility (maps to ai_images cost)
AI_IMAGE_COST = ARTISTIC_TIME_COSTS["ai_images"]

# Feature categories for organization
GENERATION_FEATURES = ["ai_images", "voice_journaling", "relationship_profiles", "meditations"]
STUDIO_FEATURES = ["mini_studio", "lyrics_generation", "beat_composition", "vocal_synthesis_base"]
PREMIUM_FEATURES = GENERATION_FEATURES + STUDIO_FEATURES

# Tier access mapping
BRONZE_FEATURES = []  # Bronze only gets trial credits, no monthly features
SILVER_FEATURES = GENERATION_FEATURES  # Silver gets AI generation features
GOLD_FEATURES = PREMIUM_FEATURES  # Gold gets everything including Mini Studio