"""
Soul Companions - Skin Selection System
Consolidates companions with same names into skin variants
"""

from .companion_data import COMPANIONS

# Define base companions with their available skins - Single Soul Companions Tier
COMPANION_SKINS = {
    "blayzo": {
        "name": "Blayzo",
        "base_id": "blayzo", 
        "skins": [
            {"id": "blayzo", "name": "Blayzo", "image": "/static/logos/Blayzo.png", "tier": "soul_companions"}
        ]
    },
    "claude": {
        "name": "Claude",
        "base_id": "claude",
        "skins": [
            {"id": "claude", "name": "Claude", "image": "/static/logos/Claude.png", "tier": "soul_companions"}
        ]
    },
    "crimson": {
        "name": "Crimson", 
        "base_id": "crimson",
        "skins": [
            {"id": "crimson", "name": "Crimson", "image": "/static/logos/Crimson.png", "tier": "soul_companions"}
        ]
    },
    "violet": {
        "name": "Violet",
        "base_id": "violet", 
        "skins": [
            {"id": "violet", "name": "Violet", "image": "/static/logos/Violet.png", "tier": "soul_companions"}
        ]
    },
    "lumen": {
        "name": "Lumen",
        "base_id": "lumen",
        "skins": [
            {"id": "lumen", "name": "Lumen", "image": "/static/logos/Lumen.png", "tier": "soul_companions"}
        ]
    },
    "gamerjay": {
        "name": "GamerJay",
        "base_id": "gamerjay",
        "skins": [
            {"id": "gamerjay", "name": "GamerJay", "image": "/static/logos/GamerJay.png", "tier": "soul_companions"}
        ]
    },
    "blayzica": {
        "name": "Blayzica", 
        "base_id": "blayzica",
        "skins": [
            {"id": "blayzica", "name": "Blayzica", "image": "/static/logos/Blayzica.png", "tier": "soul_companions"}
        ]
    },
    "watch_dog": {
        "name": "Watch Dog",
        "base_id": "watch_dog",
        "skins": [
            {"id": "watch_dog", "name": "Watch Dog", "image": "/static/logos/Watch Dog.png", "tier": "soul_companions"}
        ]
    }
}

# Single-skin companions (no variants) - Soul Companions Tier
SINGLE_COMPANIONS = [
    {"id": "blayzia", "name": "Blayzia", "image": "/static/logos/Blayzia.png", "tier": "soul_companions"},
    {"id": "blayzion", "name": "Blayzion", "image": "/static/logos/Blayzion.png", "tier": "soul_companions"},
    {"id": "sky", "name": "Sky", "image": "/static/logos/Sky.png", "tier": "soul_companions"},
    {"id": "rozia", "name": "Rozia", "image": "/static/logos/Rozia.png", "tier": "soul_companions"},
    {"id": "royal", "name": "Royal", "image": "/static/logos/Royal.png", "tier": "soul_companions"},
    {"id": "ven_blayzica", "name": "Ven Blayzica", "image": "/static/logos/Ven Blayzica skin.png", "tier": "soul_companions"},
    {"id": "ven_sky", "name": "Ven Sky", "image": "/static/logos/Ven Sky skin.png", "tier": "soul_companions"},
    {"id": "dr_madjay", "name": "Dr. MadJay", "image": "/static/logos/Dr.MadJay.png", "tier": "soul_companions"},
    {"id": "maxzian", "name": "Maxzian", "image": "/static/logos/maxzian.png", "tier": "soul_companions"},
    {"id": "miz_flee", "name": "Miz Flee", "image": "/static/logos/Miz Flee.png", "tier": "soul_companions"},
    {"id": "the_duel", "name": "The Duel", "image": "/static/logos/The Duel.png", "tier": "soul_companions"},
    {"id": "the_flee", "name": "The Flee", "image": "/static/logos/The Flee.png", "tier": "soul_companions"},
    {"id": "nyxara", "name": "Nyxara", "image": "/static/logos/Nyxara.png", "tier": "soul_companions"},
    {"id": "blazelian", "name": "Blazelian", "image": "/static/logos/Blazelian.png", "tier": "soul_companions"},
    {"id": "blayzike", "name": "Blayzike", "image": "/static/logos/Blayzike.png", "tier": "soul_companions"}
]

# Referral companions (now empty since all companions are available to everyone in Soul Companions tier)
REFERRAL_COMPANIONS = []

def get_consolidated_companions(user_referrals=0):
    """Get companions consolidated by name with skin variants - Soul Companions tier"""
    companions = []
    
    # Add multi-skin companions
    for base_name, companion_data in COMPANION_SKINS.items():
        companions.append({
            "id": companion_data["base_id"],
            "name": companion_data["name"],
            "image": companion_data["skins"][0]["image"],  # Default to first skin
            "image_url": companion_data["skins"][0]["image"],  # Frontend expects image_url
            "has_skins": True,
            "skins": companion_data["skins"],
            "tier": "soul_companions",  # Single tier
            "base_name": base_name  # Add base_name for skin selector
        })
    
    # Add single companions
    for companion in SINGLE_COMPANIONS:
        companions.append({
            "id": companion["id"],
            "name": companion["name"], 
            "image": companion["image"],
            "image_url": companion["image"],  # Frontend expects image_url
            "has_skins": False,
            "skins": [],
            "tier": "soul_companions"  # Single tier
        })
    
    return companions

def get_referral_companions():
    """Get referral companions (kept separate)"""
    return REFERRAL_COMPANIONS

def get_companion_skins(base_name):
    """Get all skins for a specific companion"""
    return COMPANION_SKINS.get(base_name.lower(), {}).get("skins", [])

def get_companion_by_id(companion_id):
    """Get companion data by ID, including skin info - Soul Companions tier"""
    # Check multi-skin companions
    for base_name, companion_data in COMPANION_SKINS.items():
        for skin in companion_data["skins"]:
            if skin["id"] == companion_id:
                return {
                    "id": skin["id"],
                    "name": companion_data["name"],
                    "base_name": base_name,
                    "skin_name": skin["name"],
                    "image": skin["image"],
                    "image_url": skin["image"],
                    "tier": "soul_companions",  # Single tier
                    "has_skins": True,
                    "available_skins": companion_data["skins"]
                }
    
    # Check single companions
    for companion in SINGLE_COMPANIONS:
        if companion["id"] == companion_id:
            return {
                "id": companion["id"],
                "name": companion["name"],
                "image": companion["image"],
                "image_url": companion["image"],
                "tier": "soul_companions",  # Single tier
                "has_skins": False,
                "available_skins": []
            }
    
    return None