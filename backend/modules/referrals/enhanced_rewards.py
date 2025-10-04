"""
SoulBridge AI - Enhanced Referral Rewards System
Properly distinguishes between companions (unique characters) and skins (variants)
"""
import logging
from database_utils import get_database
from ..companions.companion_data import COMPANIONS
from ..companions.skin_system import COMPANION_SKINS
from database_utils import format_query

logger = logging.getLogger(__name__)

# Enhanced referral rewards - now distinguishes between companions and skins
REFERRAL_REWARDS = {
    2: {
        "companions": ["blayzike"],  # New unique companion
        "skins": [],  # No skins at this level
        "message": "🎉 You've unlocked Blayzike - your first referral companion!"
    },
    5: {
        "companions": ["nyxara"],  # New unique companion
        "skins": ["claude_silver", "lumen_silver"],  # Silver skins for existing companions
        "message": "🌟 Amazing! Nyxara joins your team + Silver skins unlocked!"
    },
    8: {
        "companions": ["claude_referral"],  # Premium referral companion
        "skins": ["claude_gold", "crimson_gold", "violet_gold"],  # Gold skins
        "message": "👑 Incredible! Claude Referral unlocked + Gold skins available!"
    }
}

def classify_reward_type(companion_id: str) -> dict:
    """
    Classify if a companion_id is a unique companion or a skin variant
    Returns: {"type": "companion"|"skin", "base_character": str|None, "details": dict}
    """
    # Check if this is a skin variant
    for base_name, skin_data in COMPANION_SKINS.items():
        for skin in skin_data["skins"]:
            if skin["id"] == companion_id:
                return {
                    "type": "skin",
                    "base_character": base_name,
                    "skin_name": skin["name"],
                    "tier": skin["tier"],
                    "image": skin["image"],
                    "details": skin
                }
    
    # If not a skin, it's a unique companion
    companion = next((c for c in COMPANIONS if c["id"] == companion_id), None)
    if companion:
        return {
            "type": "companion",
            "base_character": None,
            "details": companion
        }
    
    return {"type": "unknown", "base_character": None, "details": None}

def get_enhanced_unlocks_for_referrals(referral_count: int) -> dict:
    """
    Get all companions and skins that should be unlocked for a given referral count
    Returns organized data with companions and skins separated
    """
    result = {
        "companions": {},  # Unique new characters
        "skins": {},       # Visual variants grouped by base character
        "total_unlocks": 0
    }
    
    for threshold, rewards in REFERRAL_REWARDS.items():
        if referral_count >= threshold:
            
            # Process new companions (unique characters)
            for companion_id in rewards.get("companions", []):
                classification = classify_reward_type(companion_id)
                if classification["type"] == "companion":
                    companion = classification["details"]
                    result["companions"][companion_id] = {
                        "id": companion_id,
                        "name": companion["name"],
                        "tier": companion["tier"],
                        "image_url": companion["image_url"],
                        "threshold": threshold,
                        "min_referrals": companion.get("min_referrals", 0),
                        "greeting": companion.get("greeting", ""),
                        "type": "companion"
                    }
                    result["total_unlocks"] += 1
            
            # Process new skins (character variants)
            for skin_id in rewards.get("skins", []):
                classification = classify_reward_type(skin_id)
                if classification["type"] == "skin":
                    base_char = classification["base_character"]
                    skin_details = classification["details"]
                    
                    if base_char not in result["skins"]:
                        result["skins"][base_char] = {
                            "base_name": COMPANION_SKINS[base_char]["name"],
                            "unlocked_skins": []
                        }
                    
                    result["skins"][base_char]["unlocked_skins"].append({
                        "id": skin_id,
                        "name": f"{skin_details['name']} Skin",  # Add "Skin" to the name
                        "tier": skin_details["tier"],
                        "image": skin_details["image"],
                        "threshold": threshold,
                        "type": "skin"
                    })
                    result["total_unlocks"] += 1
    
    return result

def record_enhanced_unlock(user_id: int, reward_id: str, reward_type: str, threshold: int):
    """
    Record companion or skin unlock with proper type classification
    """
    db = get_database()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        # Create enhanced table if it doesn't exist
        cursor.execute(format_query("""
            CREATE TABLE IF NOT EXISTS user_referral_rewards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                reward_id TEXT NOT NULL,
                reward_type TEXT NOT NULL CHECK (reward_type IN ('companion', 'skin')),
                base_character TEXT,
                unlock_threshold INTEGER,
                unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, reward_id),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # Classify the reward
        classification = classify_reward_type(reward_id)
        base_character = classification.get("base_character")
        
        # Insert the unlock record
        cursor.execute("""
            INSERT OR IGNORE INTO user_referral_rewards 
            (user_id, reward_id, reward_type, base_character, unlock_threshold, unlocked_at)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
        """), (user_id, reward_id, reward_type, base_character, threshold))
        
        conn.commit()
        logger.info(f"✅ Recorded {reward_type} unlock: {reward_id} for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error recording enhanced unlock: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

def check_and_grant_enhanced_rewards(user_id: int, new_referral_count: int, old_referral_count: int = 0) -> dict:
    """
    Check and grant both companions and skins when thresholds are reached
    Returns organized data about newly unlocked rewards
    """
    newly_unlocked = {
        "companions": [],
        "skins": [],
        "messages": [],
        "total_new": 0
    }
    
    # Check each threshold
    for threshold, rewards in REFERRAL_REWARDS.items():
        if old_referral_count < threshold <= new_referral_count:
            
            # Grant new companions
            for companion_id in rewards.get("companions", []):
                try:
                    record_enhanced_unlock(user_id, companion_id, "companion", threshold)
                    
                    companion = next((c for c in COMPANIONS if c["id"] == companion_id), None)
                    if companion:
                        newly_unlocked["companions"].append({
                            "id": companion_id,
                            "name": companion["name"],
                            "tier": companion["tier"],
                            "image_url": companion["image_url"],
                            "threshold": threshold,
                            "type": "companion"
                        })
                        newly_unlocked["total_new"] += 1
                        
                except Exception as e:
                    logger.error(f"❌ Failed to grant companion {companion_id}: {e}")
            
            # Grant new skins
            for skin_id in rewards.get("skins", []):
                try:
                    record_enhanced_unlock(user_id, skin_id, "skin", threshold)
                    
                    classification = classify_reward_type(skin_id)
                    if classification["type"] == "skin":
                        newly_unlocked["skins"].append({
                            "id": skin_id,
                            "name": f"{classification['skin_name']} Skin",  # Add "Skin" to the name
                            "tier": classification["tier"],
                            "image": classification["image"],
                            "base_character": classification["base_character"],
                            "threshold": threshold,
                            "type": "skin"
                        })
                        newly_unlocked["total_new"] += 1
                        
                except Exception as e:
                    logger.error(f"❌ Failed to grant skin {skin_id}: {e}")
            
            # Add threshold message
            newly_unlocked["messages"].append(rewards["message"])
    
    return newly_unlocked

def get_user_referral_rewards(user_id: int) -> dict:
    """
    Get all companions and skins unlocked by user via referrals
    Returns organized data with proper categorization
    """
    db = get_database()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(format_query("""
            SELECT reward_id, reward_type, base_character, unlock_threshold, unlocked_at
            FROM user_referral_rewards 
            WHERE user_id = ?
            ORDER BY unlocked_at
        """), (user_id,))
        
        results = cursor.fetchall()
        
        organized_rewards = {
            "companions": [],
            "skins": {},
            "total_rewards": 0
        }
        
        for row in results:
            reward_id, reward_type, base_character, threshold, unlocked_at = row
            
            if reward_type == "companion":
                companion = next((c for c in COMPANIONS if c["id"] == reward_id), None)
                if companion:
                    organized_rewards["companions"].append({
                        "id": reward_id,
                        "name": companion["name"],
                        "tier": companion["tier"],
                        "image_url": companion["image_url"],
                        "threshold": threshold,
                        "unlocked_at": unlocked_at,
                        "type": "companion"
                    })
                    organized_rewards["total_rewards"] += 1
            
            elif reward_type == "skin" and base_character:
                if base_character not in organized_rewards["skins"]:
                    organized_rewards["skins"][base_character] = {
                        "base_name": COMPANION_SKINS.get(base_character, {}).get("name", base_character),
                        "unlocked_skins": []
                    }
                
                classification = classify_reward_type(reward_id)
                if classification["type"] == "skin":
                    organized_rewards["skins"][base_character]["unlocked_skins"].append({
                        "id": reward_id,
                        "name": f"{classification['skin_name']} Skin",  # Add "Skin" to the name
                        "tier": classification["tier"],
                        "image": classification["image"],
                        "threshold": threshold,
                        "unlocked_at": unlocked_at,
                        "type": "skin"
                    })
                    organized_rewards["total_rewards"] += 1
        
        return organized_rewards
        
    except Exception as e:
        logger.error(f"Error getting user referral rewards: {e}")
        return {"companions": [], "skins": {}, "total_rewards": 0}
    finally:
        cursor.close()
        conn.close()