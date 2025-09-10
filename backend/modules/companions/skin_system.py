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
            {"id": "blayzo_bronze", "name": "Classic Blayzo", "image": "/static/logos/Blayzo.png", "tier": "bronze"},
            {"id": "blayzo2_bronze", "name": "Blayzo.2", "image": "/static/logos/blayzo_free_tier.png", "tier": "bronze"},
            {"id": "blayzo_silver", "name": "Premium Blayzo", "image": "/static/logos/Blayzo_premium_companion.png", "tier": "silver"}
        ]
    },
    "claude": {
        "name": "Claude",
        "base_id": "claude_bronze",
        "skins": [
            {"id": "claude_bronze", "name": "Classic Claude", "image": "/static/logos/Claude_Free.png", "tier": "bronze"},
            {"id": "claude_silver", "name": "Claude.3", "image": "/static/logos/Claude_Growth.png", "tier": "silver"},
            {"id": "claude_gold", "name": "Claude.2", "image": "/static/logos/Claude_Max.png", "tier": "gold"}
        ]
    },
    "crimson": {
        "name": "Crimson", 
        "base_id": "crimson_bronze",
        "skins": [
            {"id": "crimson_bronze", "name": "Classic Crimson", "image": "/static/logos/Crimson_Free.png", "tier": "bronze"},
            {"id": "crimson_gold", "name": "Crimson.2", "image": "/static/logos/Crimson_a_Max_companion.png", "tier": "gold"}
        ]
    },
    "violet": {
        "name": "Violet",
        "base_id": "violet_bronze", 
        "skins": [
            {"id": "violet_bronze", "name": "Classic Violet", "image": "/static/logos/Violet_Free.png", "tier": "bronze"},
            {"id": "violet_gold", "name": "Violet.2", "image": "/static/logos/Violet_a_Max_companion.png", "tier": "gold"}
        ]
    },
    "lumen": {
        "name": "Lumen",
        "base_id": "lumen_bronze",
        "skins": [
            {"id": "lumen_bronze", "name": "Classic Lumen", "image": "/static/logos/Lumen_Bronze.png", "tier": "bronze"},
            {"id": "lumen_silver", "name": "Lumen.2", "image": "/static/logos/Lumen_Silver.png", "tier": "silver"}
        ]
    },
    "gamerjay": {
        "name": "GamerJay",
        "base_id": "gamerjay_bronze",
        "skins": [
            {"id": "gamerjay_bronze", "name": "Classic GamerJay", "image": "/static/logos/GamerJay_Free_companion.png", "tier": "bronze"},
            {"id": "gamerjay_silver", "name": "GamerJay.2", "image": "/static/logos/GamerJay_premium_companion.png", "tier": "silver"}
        ]
    },
    "blayzica": {
        "name": "Blayzica", 
        "base_id": "blayzica_bronze",
        "skins": [
            {"id": "blayzica_bronze", "name": "Classic Blayzica", "image": "/static/logos/Blayzica.png", "tier": "bronze"},
            {"id": "blayzica_silver", "name": "Blayzica.2", "image": "/static/logos/Blayzica_Pro.png", "tier": "silver"}
        ]
    },
    "watchdog": {
        "name": "WatchDog",
        "base_id": "watchdog_silver",
        "skins": [
            {"id": "watchdog_silver", "name": "WatchDog", "image": "/static/logos/WatchDog_a_Premium_companion.png", "tier": "silver"},
            {"id": "watchdog_gold", "name": "WatchDog.2", "image": "/static/logos/WatchDog_a_Max_Companion.png", "tier": "gold"}
        ]
    }
}

# Single-skin companions (no variants)
SINGLE_COMPANIONS = [
    {"id": "blayzia_bronze", "name": "Blayzia", "image": "/static/logos/Blayzia.png", "tier": "bronze"},
    {"id": "blayzion_bronze", "name": "Blayzion", "image": "/static/logos/Blayzion.png", "tier": "bronze"},
    {"id": "sky_silver", "name": "Sky", "image": "/static/logos/Sky_a_premium_companion.png", "tier": "silver"},
    {"id": "rozia_silver", "name": "Rozia", "image": "/static/logos/Rozia_Silver.png", "tier": "silver"},
    {"id": "royal_gold", "name": "Royal", "image": "/static/logos/Royal_a_Max_companion.png", "tier": "gold"},
    {"id": "ven_blayzica_gold", "name": "Ven Blayzica", "image": "/static/logos/Ven_Blayzica_a_Max_companion.png", "tier": "gold"},
    {"id": "ven_sky_gold", "name": "Ven Sky", "image": "/static/logos/Ven_Sky_a_Max_companion.png", "tier": "gold"},
    {"id": "dr_madjay_gold", "name": "Dr. MadJay", "image": "/static/logos/Dr. MadJay.png", "tier": "gold"}
]

# Referral companions (keep separate as requested)
REFERRAL_COMPANIONS = [
    {"id": "blayzike", "name": "Blayzike", "image": "/static/logos/blayzike.png", "min_referrals": 2},
    {"id": "blazelian", "name": "Blazelian", "image": "/static/logos/blazelian.png", "min_referrals": 4},
    {"id": "nyxara", "name": "Nyxara", "image": "/static/logos/Nyxara.png", "min_referrals": 6},
    {"id": "claude_referral", "name": "Claude Referral", "image": "/static/logos/claude_referral.png", "min_referrals": 8},
    {"id": "blayzo_referral", "name": "Blayzo Referral", "image": "/static/logos/Blayzo_Referral.png", "min_referrals": 10}
]

def get_consolidated_companions():
    """Get companions consolidated by name with skin variants"""
    companions = []
    
    # Add multi-skin companions
    for base_name, companion_data in COMPANION_SKINS.items():
        companions.append({
            "id": companion_data["base_id"],
            "name": companion_data["name"],
            "image": companion_data["skins"][0]["image"],  # Default to first skin
            "has_skins": True,
            "skins": companion_data["skins"]
        })
    
    # Add single companions
    for companion in SINGLE_COMPANIONS:
        companions.append({
            "id": companion["id"],
            "name": companion["name"], 
            "image": companion["image"],
            "has_skins": False,
            "skins": []
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