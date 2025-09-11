"""
Soul Companions - Skin Selection System
Consolidates companions with same names into skin variants
"""

from .companion_data import COMPANIONS

# Define base companions with their available skins
COMPANION_SKINS = {
    "blayzo": {
        "name": "Blayzo",
        "base_id": "blayzo_bronze", 
        "skins": [
            {"id": "blayzo_bronze", "name": "Classic Blayzo", "image": "/static/images/companions/blayzo.png", "tier": "bronze"},
            {"id": "blayzo2_bronze", "name": "Blayzo.2", "image": "/static/images/companions/blayzo2.png", "tier": "bronze"},
            {"id": "blayzo_silver", "name": "Premium Blayzo", "image": "/static/images/companions/blayzo_premium.png", "tier": "silver"}
        ]
    },
    "claude": {
        "name": "Claude",
        "base_id": "claude_bronze",
        "skins": [
            {"id": "claude_bronze", "name": "Classic Claude", "image": "/static/images/companions/claude.png", "tier": "bronze"},
            {"id": "claude_silver", "name": "Claude.3", "image": "/static/images/companions/claude_growth.png", "tier": "silver"},
            {"id": "claude_gold", "name": "Claude.2", "image": "/static/images/companions/claude_max.png", "tier": "gold"}
        ]
    },
    "crimson": {
        "name": "Crimson", 
        "base_id": "crimson_bronze",
        "skins": [
            {"id": "crimson_bronze", "name": "Classic Crimson", "image": "/static/images/companions/crimson.png", "tier": "bronze"},
            {"id": "crimson_gold", "name": "Crimson.2", "image": "/static/images/companions/crimson_max.png", "tier": "gold"}
        ]
    },
    "violet": {
        "name": "Violet",
        "base_id": "violet_bronze", 
        "skins": [
            {"id": "violet_bronze", "name": "Classic Violet", "image": "/static/images/companions/violet.png", "tier": "bronze"},
            {"id": "violet_gold", "name": "Violet.2", "image": "/static/images/companions/violet_max.png", "tier": "gold"}
        ]
    },
    "lumen": {
        "name": "Lumen",
        "base_id": "lumen_bronze",
        "skins": [
            {"id": "lumen_bronze", "name": "Classic Lumen", "image": "/static/images/companions/lumen.png", "tier": "bronze"},
            {"id": "lumen_silver", "name": "Lumen.2", "image": "/static/images/companions/lumen_silver.png", "tier": "silver"}
        ]
    },
    "gamerjay": {
        "name": "GamerJay",
        "base_id": "gamerjay_bronze",
        "skins": [
            {"id": "gamerjay_bronze", "name": "Classic GamerJay", "image": "/static/images/companions/gamerjay.png", "tier": "bronze"},
            {"id": "gamerjay_silver", "name": "GamerJay.2", "image": "/static/images/companions/gamerjay_premium.png", "tier": "silver"}
        ]
    },
    "blayzica": {
        "name": "Blayzica", 
        "base_id": "blayzica_bronze",
        "skins": [
            {"id": "blayzica_bronze", "name": "Classic Blayzica", "image": "/static/images/companions/blayzica.png", "tier": "bronze"},
            {"id": "blayzica_silver", "name": "Blayzica.2", "image": "/static/images/companions/blayzica_pro.png", "tier": "silver"}
        ]
    },
    "watchdog": {
        "name": "WatchDog",
        "base_id": "watchdog_silver",
        "skins": [
            {"id": "watchdog_silver", "name": "WatchDog", "image": "/static/images/companions/watchdog.png", "tier": "silver"},
            {"id": "watchdog_gold", "name": "WatchDog.2", "image": "/static/images/companions/watchdog_max.png", "tier": "gold"}
        ]
    }
}

# Single-skin companions (no variants)
SINGLE_COMPANIONS = [
    {"id": "blayzia_bronze", "name": "Blayzia", "image": "/static/images/companions/blayzia.png", "tier": "bronze"},
    {"id": "blayzion_bronze", "name": "Blayzion", "image": "/static/images/companions/blayzion.png", "tier": "bronze"},
    {"id": "sky_silver", "name": "Sky", "image": "/static/images/companions/sky.png", "tier": "silver"},
    {"id": "rozia_silver", "name": "Rozia", "image": "/static/images/companions/rozia.png", "tier": "silver"},
    {"id": "royal_gold", "name": "Royal", "image": "/static/images/companions/royal.png", "tier": "gold"},
    {"id": "ven_blayzica_gold", "name": "Ven Blayzica", "image": "/static/images/companions/ven_blayzica.png", "tier": "gold"},
    {"id": "ven_sky_gold", "name": "Ven Sky", "image": "/static/images/companions/ven_sky.png", "tier": "gold"},
    {"id": "dr_madjay_gold", "name": "Dr. MadJay", "image": "/static/images/companions/dr_madjay.png", "tier": "gold"}
]

# Referral companions (unlocked by referrals, then integrated by tier)
REFERRAL_COMPANIONS = [
    {"id": "blayzike", "name": "Blayzike", "image": "/static/images/companions/blayzike.png", "min_referrals": 2, "tier": "bronze"},
    {"id": "blazelian", "name": "Blazelian", "image": "/static/images/companions/blazelian.png", "min_referrals": 4, "tier": "silver"},
    {"id": "nyxara", "name": "Nyxara", "image": "/static/images/companions/nyxara.png", "min_referrals": 6, "tier": "silver"},
    {"id": "claude_referral", "name": "Claude Referral", "image": "/static/images/companions/claude_referral.png", "min_referrals": 8, "tier": "gold"},
    {"id": "blayzo_referral", "name": "Blayzo Referral", "image": "/static/images/companions/blayzo_referral.png", "min_referrals": 10, "tier": "gold"}
]

def get_consolidated_companions(user_referrals=0):
    """Get companions consolidated by name with skin variants, including unlocked referral companions"""
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
            "tier": companion_data["skins"][0]["tier"],  # Use first skin's tier
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
            "tier": companion["tier"]
        })
    
    # Add unlocked referral companions to main grid
    for companion in REFERRAL_COMPANIONS:
        if user_referrals >= companion["min_referrals"]:
            companions.append({
                "id": companion["id"],
                "name": companion["name"],
                "image": companion["image"],
                "image_url": companion["image"],  # Frontend expects image_url
                "has_skins": False,
                "skins": [],
                "tier": companion["tier"],
                "is_referral": True  # Mark as referral companion
            })
        
    return companions

def get_referral_companions():
    """Get referral companions (kept separate)"""
    return REFERRAL_COMPANIONS

def get_companion_skins(base_name):
    """Get all skins for a specific companion"""
    return COMPANION_SKINS.get(base_name.lower(), {}).get("skins", [])

def get_companion_by_id(companion_id):
    """Get companion data by ID, including skin info"""
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
                    "tier": skin["tier"],
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
                "tier": companion["tier"],
                "has_skins": False,
                "available_skins": []
            }
    
    # Check referral companions
    for companion in REFERRAL_COMPANIONS:
        if companion["id"] == companion_id:
            return {
                "id": companion["id"],
                "name": companion["name"],
                "image": companion["image"],
                "min_referrals": companion["min_referrals"],
                "is_referral": True
            }
    
    return None