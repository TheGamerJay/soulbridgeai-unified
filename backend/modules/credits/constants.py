"""
SoulBridge AI - Credits Constants
All credit costs and allowances consolidated in one place
"""

# Credit costs for different features (artistic time required)
ARTISTIC_TIME_COSTS = {
    # Core Companion Features
    "decoder": 3,                      # Quick analysis and insights
    "fortune_teller": 5,               # Tarot readings and fortune telling
    "horoscope": 3,                    # Daily horoscope insights
    "creative_writer": 8,              # Long-form creative content
    "soul_riddle": 4,                  # Mind-bending puzzles & brain games
    "chat_message": 1,                 # Per chat message cost
    
    # AI Generation Features
    "ai_images": 15,                   # DALL-E image generation (premium)
    "voice_journaling": 10,            # Voice transcription + AI analysis
    "relationship_profiles": 15,       # Complex relationship analysis
    "meditations": 5,                  # Personalized meditation generation
    "mini_studio": 20,                 # Music production features (basic)
    "mini_studio_advanced": 35,        # Advanced music production
    
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
    "soul_companions": 100,    # Free tier gets 100 signup credits (one-time)
    "soul_companions_pro": 300, # Pro subscription gets 300 monthly credits
}

# Trial system credits
TRIAL_ARTISTIC_TIME = 60  # Trial users get 60 one-time credits for 5 hours

# Legacy constant for backwards compatibility (maps to ai_images cost)
AI_IMAGE_COST = ARTISTIC_TIME_COSTS["ai_images"]

# Feature categories for organization
CORE_FEATURES = ["decoder", "fortune_teller", "horoscope", "creative_writer", "soul_riddle", "chat_message"]
GENERATION_FEATURES = ["ai_images", "voice_journaling", "relationship_profiles", "meditations"]
STUDIO_FEATURES = ["mini_studio", "mini_studio_advanced", "lyrics_generation", "beat_composition", "vocal_synthesis_base"]
ALL_FEATURES = CORE_FEATURES + GENERATION_FEATURES + STUDIO_FEATURES

# New unified tier access - all users get all features, gated by credits only
SOUL_COMPANIONS_FEATURES = ALL_FEATURES  # All features available to all users