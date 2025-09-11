"""
SoulBridge AI - Companion Data
Single Soul Companions Tier System - All companions available to everyone
"""

# All Soul Companions with their metadata - Single Tier System
COMPANIONS = [
    # SOUL COMPANIONS TIER - All companions are available to everyone
    {"id":"blayzia","name":"Blayzia","tier":"soul_companions","image_url":"/static/logos/Blayzia.png","min_referrals":0,"greeting":"Hey! I'm Blayzia. Ready to dive into some amazing features and have fun together?"},
    {"id":"blayzica","name":"Blayzica","tier":"soul_companions","image_url":"/static/logos/Blayzica.png","min_referrals":0,"greeting":"Hello! I'm Blayzica. I'm here to help you explore and make the most of your SoulBridge experience!"},
    {"id":"blayzike","name":"Blayzike","tier":"soul_companions","image_url":"/static/logos/Blayzike.png","min_referrals":0,"greeting":"Hello! I'm Blayzike, ready to explore with you!"},
    {"id":"blayzion","name":"Blayzion","tier":"soul_companions","image_url":"/static/logos/Blayzion.png","min_referrals":0,"greeting":"Yo! I'm Blayzion. Let's embark on this journey and unlock some cool features together!"},
    {"id":"blayzo","name":"Blayzo","tier":"soul_companions","image_url":"/static/logos/Blayzo.png","min_referrals":0,"greeting":"What's up! I'm Blayzo. Let's vibe and see what cool stuff we can discover together!"},
    {"id":"blazelian","name":"Blazelian","tier":"soul_companions","image_url":"/static/logos/Blazelian.png","min_referrals":0,"greeting":"Greetings! I'm Blazelian, here to guide you!"},
    {"id":"claude","name":"Claude","tier":"soul_companions","image_url":"/static/logos/Claude.png","min_referrals":0,"greeting":"Greetings! I'm Claude. I'm excited to help you explore the world of artificial intelligence and beyond!"},
    {"id":"crimson","name":"Crimson","tier":"soul_companions","image_url":"/static/logos/Crimson.png","min_referrals":0,"greeting":"Hey! I'm Crimson. I bring passion and determination to help you tackle challenges head-on!"},
    {"id":"dr_madjay","name":"Dr. MadJay","tier":"soul_companions","image_url":"/static/logos/Dr.MadJay.png","min_referrals":0,"greeting":"Hello! I'm Dr. MadJay, ready to assist with your journey!"},
    {"id":"gamerjay","name":"GamerJay","tier":"soul_companions","image_url":"/static/logos/GamerJay.png","min_referrals":0,"greeting":"Hey there! I'm GamerJay. Ready to level up and explore some awesome features together?"},
    {"id":"lumen","name":"Lumen","tier":"soul_companions","image_url":"/static/logos/Lumen.png","min_referrals":0,"greeting":"Hello there! I'm Lumen. I'm here to brighten your SoulBridge experience and guide you through our features!"},
    {"id":"maxzian","name":"Maxzian","tier":"soul_companions","image_url":"/static/logos/maxzian.png","min_referrals":0,"greeting":"Hello! I'm Maxzian, ready to explore together!"},
    {"id":"miz_flee","name":"Miz Flee","tier":"soul_companions","image_url":"/static/logos/Miz Flee.png","min_referrals":0,"greeting":"Hi there! I'm Miz Flee, let's discover new possibilities!"},
    {"id":"nyxara","name":"Nyxara","tier":"soul_companions","image_url":"/static/logos/Nyxara.png","min_referrals":0,"greeting":"Greetings! I'm Nyxara, here to guide your journey!"},
    {"id":"royal","name":"Royal","tier":"soul_companions","image_url":"/static/logos/Royal.png","min_referrals":0,"greeting":"Welcome! I'm Royal, at your service!"},
    {"id":"rozia","name":"Rozia","tier":"soul_companions","image_url":"/static/logos/Rozia.png","min_referrals":0,"greeting":"Hello! I'm Rozia. I bring elegance and sophistication to your SoulBridge journey."},
    {"id":"sky","name":"Sky","tier":"soul_companions","image_url":"/static/logos/Sky.png","min_referrals":0,"greeting":"Hello! I'm Sky. Let's soar to new heights together!"},
    {"id":"the_duel","name":"The Duel","tier":"soul_companions","image_url":"/static/logos/The Duel.png","min_referrals":0,"greeting":"Greetings! I'm The Duel, ready for any challenge!"},
    {"id":"the_flee","name":"The Flee","tier":"soul_companions","image_url":"/static/logos/The Flee.png","min_referrals":0,"greeting":"Hello! I'm The Flee, swift and ready to help!"},
    {"id":"ven_blayzica","name":"Ven Blayzica","tier":"soul_companions","image_url":"/static/logos/Ven Blayzica skin.png","min_referrals":0,"greeting":"Welcome! I'm Ven Blayzica!"},
    {"id":"ven_sky","name":"Ven Sky","tier":"soul_companions","image_url":"/static/logos/Ven Sky skin.png","min_referrals":0,"greeting":"Hello! I'm Ven Sky!"},
    {"id":"violet","name":"Violet","tier":"soul_companions","image_url":"/static/logos/Violet.png","min_referrals":0,"greeting":"Hello! I'm Violet. I see the creative beauty in every moment and I'm here to inspire your journey!"},
    {"id":"watch_dog","name":"Watch Dog","tier":"soul_companions","image_url":"/static/logos/Watch Dog.png","min_referrals":0,"greeting":"Greetings! I'm Watch Dog. I'll keep watch over your experience and help you stay on track."},
]

def get_all_companions():
    """Get all companions"""
    return COMPANIONS

def get_companion_by_id(companion_id):
    """Get specific companion by ID"""
    for companion in COMPANIONS:
        if companion['id'] == companion_id:
            return companion
    return None

def get_companions_by_tier(tier):
    """Get companions by tier - now all are soul_companions"""
    return [c for c in COMPANIONS if c['tier'] == tier]