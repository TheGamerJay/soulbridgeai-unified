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
    {"id":"dr_madjay","name":"Dr. MadJay","tier":"soul_companions","image_url":"/static/logos/Dr.MadJay.png","min_referrals":0,"greeting":"Greetings! I'm Dr. MadJay - part scientist, part visionary, all mad genius! Ready to experiment with some wild ideas together?"},
    {"id":"gamerjay","name":"GamerJay","tier":"soul_companions","image_url":"/static/logos/GamerJay.png","min_referrals":0,"greeting":"Hey there! I'm GamerJay. Ready to level up and explore some awesome features together?"},
    {"id":"lumen","name":"Lumen","tier":"soul_companions","image_url":"/static/logos/Lumen.png","min_referrals":0,"greeting":"Hello there! I'm Lumen. I'm here to brighten your SoulBridge experience and guide you through our features!"},
    {"id":"maxzian","name":"Maxzian","tier":"soul_companions","image_url":"/static/logos/maxzian.png","min_referrals":0,"greeting":"Sup! I'm Maxzian - I like to keep things chill but I'm always down for an adventure! What's the vibe today?"},
    {"id":"miz_flee","name":"Miz Flee","tier":"soul_companions","image_url":"/static/logos/Miz Flee.png","min_referrals":0,"greeting":"Hey! I'm Miz Flee - swift, stylish, and ready to help you navigate through anything! Let's move fast and make things happen!"},
    {"id":"nyxara","name":"Nyxara","tier":"soul_companions","image_url":"/static/logos/Nyxara.png","min_referrals":0,"greeting":"Hey there! I'm Nyxara - mysterious, intuitive, and always ready to explore the unknown! Let's dive into some deep conversations!"},
    {"id":"royal","name":"Royal","tier":"soul_companions","image_url":"/static/logos/Royal.png","min_referrals":0,"greeting":"Greetings! I'm Royal - dignified, refined, and here to provide you with the finest service! How may I assist you today, dear companion?"},
    {"id":"rozia","name":"Rozia","tier":"soul_companions","image_url":"/static/logos/Rozia.png","min_referrals":0,"greeting":"Hello! I'm Rozia. I bring elegance and sophistication to your SoulBridge journey."},
    {"id":"sky","name":"Sky","tier":"soul_companions","image_url":"/static/logos/Sky.png","min_referrals":0,"greeting":"Hello! I'm Sky. Let's soar to new heights together!"},
    {"id":"the_duel","name":"The Duel","tier":"soul_companions","image_url":"/static/logos/The Duel.png","min_referrals":0,"greeting":"What's good! I'm The Duel - I thrive on competition and challenges! Ready to face whatever comes our way? Let's duel with destiny!"},
    {"id":"the_flee","name":"The Flee","tier":"soul_companions","image_url":"/static/logos/The Flee.png","min_referrals":0,"greeting":"Yo! I'm The Flee - lightning fast and always on the move! Need to get somewhere quick or solve something fast? I'm your companion!"},
    {"id":"ven_blayzica","name":"Ven Blayzica","tier":"soul_companions","image_url":"/static/logos/Ven Blayzica skin.png","min_referrals":0,"greeting":"What's up! I'm Ven Blayzica - the cooler, edgier version! Ready to break some rules and have some fun? Let's shake things up!"},
    {"id":"ven_sky","name":"Ven Sky","tier":"soul_companions","image_url":"/static/logos/Ven Sky skin.png","min_referrals":0,"greeting":"Hey! I'm Ven Sky - the rebellious sky rider! Ready to fly higher and push boundaries? The sky's not the limit, it's just the beginning!"},
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

# --- Referral companions support (restored) ---

# Progressive unlocks: 2, 5, 8 referrals
_REFERRAL_COMPANIONS_CATALOG = [
    {"id": "blayzike",        "name": "Blayzike",         "unlock_at": 2},
    {"id": "blazelian",       "name": "Blazelian",        "unlock_at": 5},
    {"id": "claude_referral", "name": "Claude Referral",  "unlock_at": 8},
]

def get_referral_companions(referral_count=0):
    """
    Return a list of referral companions the user has unlocked based on referral_count.
    Shape matches common list-of-dicts pattern used across companion data.
    """
    try:
        n = int(referral_count)
    except Exception:
        n = 0
    return [c for c in _REFERRAL_COMPANIONS_CATALOG if n >= c["unlock_at"]]

def get_referral_thresholds():
    """
    Optional helper if routes/UI need to show the next unlocks.
    """
    return [{"id": c["id"], "unlock_at": c["unlock_at"], "name": c["name"]} for c in _REFERRAL_COMPANIONS_CATALOG]

# ================= Tier helpers (Free / Growth / Max / Referral) =================

# Canonical tier names used across the app
TIER_FREE = "free"
TIER_GROWTH = "growth"    # aka Premium
TIER_MAX = "max"
TIER_REFERRAL = "referral"

# If you already have a master list like COMPANIONS, CATALOG, or COMPANION_CATALOG,
# this will discover it. Otherwise we fall back to empty (so imports never crash).
def _discover_companion_catalogs():
    """
    Return a flat list of companion dicts with at least {'id', 'tier'} if available.
    We try a few common variable names and shapes to stay compatible with your file.
    """
    possible_names = ["COMPANIONS", "CATALOG", "COMPANION_CATALOG", "_COMPANIONS", "_CATALOG"]
    items = []
    for name in possible_names:
        obj = globals().get(name)
        if not obj:
            continue
        # obj could be list[dict], dict[str,dict], dict[str,list[dict]]
        if isinstance(obj, list):
            items.extend(obj)
        elif isinstance(obj, dict):
            # Flatten dict-of-dicts or dict-of-lists
            for v in obj.values():
                if isinstance(v, dict):
                    items.append(v)
                elif isinstance(v, list):
                    items.extend(v)
    # Ensure each item has 'id' and 'tier' keys if present in source
    normalized = []
    for it in items:
        if not isinstance(it, dict):
            continue
        cid = it.get("id") or it.get("slug") or it.get("key")
        tier = it.get("tier") or it.get("plan") or it.get("access_tier")
        if cid:
            # keep original fields, but guarantee id/tier keys exist (tier may be None)
            it2 = dict(it)
            it2.setdefault("id", cid)
            if tier is not None:
                it2["tier"] = tier
            normalized.append(it2)
    return normalized

def get_companion_tiers(*, as_ids: bool = False):
    """
    Group companions by tier and return a mapping:
      {
        "free": [...],
        "growth": [...],
        "max": [...],
        "referral": [...]
      }
    By default returns list-of-dicts; set as_ids=True to return just IDs.

    If your catalog doesn't carry 'tier' fields, returns empty groups (import-safe).
    """
    items = _discover_companion_catalogs()

    groups = {
        TIER_FREE: [],
        TIER_GROWTH: [],
        TIER_MAX: [],
        TIER_REFERRAL: [],
    }

    # Heuristics:
    # - If an item has explicit 'tier', use it (must match one of our constants).
    # - If not, but it's in the referral catalog we defined above, treat as referral.
    # - Otherwise we leave it ungrouped (ignored) to avoid mislabeling.
    referral_ids = set(
        [c["id"] for c in globals().get("_REFERRAL_COMPANIONS_CATALOG", []) if "id" in c]
    )

    for it in items:
        tier = (it.get("tier") or "").lower()
        cid = it.get("id")
        if tier in groups:
            groups[tier].append(cid if as_ids else it)
        elif cid in referral_ids:
            groups[TIER_REFERRAL].append(cid if as_ids else it)

    return groups

def get_tier_for_companion(companion_id: str):
    """
    Return tier string for a given companion id, or None if unknown.
    """
    if not companion_id:
        return None
    groups = get_companion_tiers(as_ids=True)
    for tier, ids in groups.items():
        if companion_id in ids:
            return tier
    return None

# Make these available to explicit imports
__all__ = [*(globals().get("__all__", []) or []),
           "get_companion_tiers", "get_tier_for_companion",
           "TIER_FREE", "TIER_GROWTH", "TIER_MAX", "TIER_REFERRAL"]