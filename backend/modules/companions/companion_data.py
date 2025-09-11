"""
SoulBridge AI - Companion Data
Extracted from app.py monolith for modular architecture
"""

# All 29 AI companions with their metadata
COMPANIONS = [
    # BRONZE TIER COMPANIONS (10)
    {"id":"gamerjay_bronze","name":"GamerJay","tier":"bronze","image_url":"/static/companions/gamerjay.png","min_referrals":0,"greeting":"Hey there! I'm GamerJay. Ready to level up and explore some awesome features together?"},
    {"id":"blayzo_bronze","name":"Blayzo","tier":"bronze","image_url":"/static/companions/blayzo.png","min_referrals":0,"greeting":"What's up! I'm Blayzo. Let's vibe and see what cool stuff we can discover together!"},
    {"id":"blayzica_bronze","name":"Blayzica","tier":"bronze","image_url":"/static/companions/blayzica.png","min_referrals":0,"greeting":"Hello! I'm Blayzica. I'm here to help you explore and make the most of your SoulBridge experience!"},
    {"id":"claude_bronze","name":"Claude","tier":"bronze","image_url":"/static/companions/claude.png","min_referrals":0,"greeting":"Greetings! I'm Claude. I'm excited to help you explore the world of artificial intelligence and beyond!"},
    {"id":"blayzia_bronze","name":"Blayzia","tier":"bronze","image_url":"/static/companions/blayzia.png","min_referrals":0,"greeting":"Hey! I'm Blayzia. Ready to dive into some amazing features and have fun together?"},
    {"id":"blayzion_bronze","name":"Blayzion","tier":"bronze","image_url":"/static/companions/blayzion.png","min_referrals":0,"greeting":"Yo! I'm Blayzion. Let's embark on this journey and unlock some cool features together!"},
    {"id":"lumen_bronze","name":"Lumen","tier":"bronze","image_url":"/static/companions/lumen.png","min_referrals":0,"greeting":"Hello there! I'm Lumen. I'm here to brighten your SoulBridge experience and guide you through our features!"},
    {"id":"blayzo2_bronze","name":"Blayzo.2","tier":"bronze","image_url":"/static/companions/blayzo2.png","min_referrals":0,"greeting":"Hey! I'm Blayzo.2. Ready to explore the next level of features together?"},
    {"id":"crimson_bronze","name":"Crimson","tier":"bronze","image_url":"/static/companions/crimson.png","min_referrals":0,"greeting":"Hey! I'm Crimson. I bring passion and determination to help you tackle challenges head-on!"},
    {"id":"violet_bronze","name":"Violet","tier":"bronze","image_url":"/static/companions/violet.png","min_referrals":0,"greeting":"Hello! I'm Violet. I see the creative beauty in every moment and I'm here to inspire your journey!"},

    # SILVER TIER COMPANIONS (8) 
    {"id":"sky_silver","name":"Sky","tier":"silver","image_url":"/static/companions/sky.png","min_referrals":0,"greeting":"Hello! I'm Sky. With enhanced features at your fingertips, let's soar to new heights together!"},
    {"id":"gamerjay_silver","name":"GamerJay.2","tier":"silver","image_url":"/static/companions/gamerjay_premium.png","min_referrals":0,"greeting":"What's up! I'm GamerJay.2. Time to unlock the next level of features and dominate together!"},
    {"id":"claude_silver","name":"Claude.3","tier":"silver","image_url":"/static/companions/claude_growth.png","min_referrals":0,"greeting":"Welcome! I'm Claude.3. With expanded capabilities, I'm ready to help you achieve more!"},
    {"id":"blayzo_silver","name":"Blayzo.3","tier":"silver","image_url":"/static/companions/blayzo_premium.png","min_referrals":0,"greeting":"Hey! I'm Blayzo.3. Ready to take your experience to the premium level?"},
    {"id":"blayzica_silver","name":"Blayzica.2","tier":"silver","image_url":"/static/companions/blayzica_pro.png","min_referrals":0,"greeting":"Hi there! I'm Blayzica.2. Let's explore the enhanced features together!"},
    {"id":"watchdog_silver","name":"WatchDog","tier":"silver","image_url":"/static/companions/watchdog.png","min_referrals":0,"greeting":"Greetings! I'm WatchDog. I'll keep watch over your premium experience and help you stay on track."},
    {"id":"rozia_silver","name":"Rozia","tier":"silver","image_url":"/static/companions/rozia.png","min_referrals":0,"greeting":"Hello! I'm Rozia. I bring elegance and sophistication to your SoulBridge journey."},
    {"id":"lumen_silver","name":"Lumen.2","tier":"silver","image_url":"/static/companions/lumen_silver.png","min_referrals":0,"greeting":"Welcome! I'm Lumen.2. Let me illuminate your path to premium features and capabilities."},

    # GOLD TIER COMPANIONS (8)
    {"id":"crimson_gold","name":"Crimson.2","tier":"gold","image_url":"/static/companions/crimson_max.png","min_referrals":0,"greeting":"Welcome, I'm Crimson.2. You have access to unlimited features and the full power of SoulBridge AI!"},
    {"id":"violet_gold","name":"Violet.2","tier":"gold","image_url":"/static/companions/violet_max.png","min_referrals":0,"greeting":"Greetings! I'm Violet.2. Together we'll explore unlimited possibilities and exclusive features!"},
    {"id":"claude_gold","name":"Claude.2","tier":"gold","image_url":"/static/companions/claude_max.png","min_referrals":0,"greeting":"Hello! I'm Claude.2. With unlimited access to all features, let's achieve extraordinary things together!"},
    {"id":"royal_gold","name":"Royal","tier":"gold","image_url":"/static/companions/royal.png","min_referrals":0,"greeting":"Greetings! I'm Royal. Experience the pinnacle of AI companionship with unlimited possibilities."},
    {"id":"ven_blayzica_gold","name":"Ven Blayzica","tier":"gold","image_url":"/static/companions/ven_blayzica.png","min_referrals":0,"greeting":"Hello! I'm Ven Blayzica. Let's venture into the ultimate SoulBridge experience together."},
    {"id":"ven_sky_gold","name":"Ven Sky","tier":"gold","image_url":"/static/companions/ven_sky.png","min_referrals":0,"greeting":"Welcome! I'm Ven Sky. Together we'll soar beyond limits with unlimited premium access."},
    {"id":"watchdog_gold","name":"WatchDog.2","tier":"gold","image_url":"/static/companions/watchdog_max.png","min_referrals":0,"greeting":"Greetings! I'm WatchDog.2. I'll safeguard your unlimited access and guide you through premium features."},
    {"id":"dr_madjay_gold","name":"Dr. MadJay","tier":"gold","image_url": "/static/companions/dr_madjay.png","min_referrals":0,"greeting":"Greetings! I'm Dr. MadJay. Let's explore the cutting-edge possibilities of unlimited AI access."},

    # REFERRAL COMPANIONS (5) - Unlocked by referring friends
    {"id":"blayzike","name":"Blayzike","tier":"silver","image_url":"/static/companions/blayzike.png","min_referrals":2},
    {"id":"blazelian","name":"Blazelian","tier":"gold","image_url":"/static/companions/blazelian.png","min_referrals":4},
    {"id":"nyxara","name":"Nyxara","tier":"silver","image_url":"/static/companions/nyxara.png","min_referrals":6},
    {"id":"claude_referral","name":"Claude Referral","tier":"gold","image_url":"/static/companions/claude_referral.png","min_referrals":8},
    {"id":"blayzo_referral","name":"Blayzo Referral","tier":"gold","image_url":"/static/companions/blayzo_referral.png","min_referrals":10},
]

def get_companions_by_tier(tier: str) -> list:
    """Get all companions for a specific tier"""
    return [comp for comp in COMPANIONS if comp["tier"] == tier and comp["min_referrals"] == 0]

def get_referral_companions() -> list:
    """Get all companions that require referrals"""
    return [comp for comp in COMPANIONS if comp["min_referrals"] > 0]

def get_companion_by_id(companion_id: str) -> dict:
    """Get a specific companion by ID"""
    for comp in COMPANIONS:
        if comp["id"] == companion_id:
            return comp
    return None

def get_all_companions() -> list:
    """Get all companions"""
    return COMPANIONS.copy()

def get_companion_tiers() -> list:
    """Get all available tiers"""
    return ["bronze", "silver", "gold"]